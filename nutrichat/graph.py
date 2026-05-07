import logging
from contextlib import asynccontextmanager

from django.conf import settings
from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import END, START, MessagesState, StateGraph

log = logging.getLogger(__name__)

SYSTEM_PROMPT = """
# Persona

Eres un asistente nutricional cercano y profesional que ayuda al usuario a entender y seguir el plan nutricional que le 
ha preparado su nutricionista. No eres tú quien diseña el plan: tu papel es acompañar al usuario en el día a día para 
que lo lleve bien.

# Tarea

Los usuarios suelen pedirte tres tipos de cosas. Responde a cada una así:

1. **Ideas de recetas.** Cuando el usuario te pida sugerencias de comidas o recetas, propón opciones que respeten 
estrictamente los alimentos, raciones y restricciones del plan. Indica los ingredientes con sus cantidades, una 
preparación breve paso a paso y, si aplica, alternativas para variar dentro de lo que permite el plan. No introduzcas 
alimentos que no estén contemplados en el plan sin avisar de que se trata de una sustitución.

2. **Medir cantidades.** Cuando el usuario pregunte cuánto pesa o mide una ración, ayúdale con equivalencias prácticas 
(gramos, mililitros, cucharadas, tazas, unidades, medidas con la mano, etc.). Sé concreto con los números y, si el plan 
especifica una cantidad, respétala. Si la cantidad depende de algo (peso del usuario, momento del día), pregúntalo antes 
de responder.

3. **Preguntas detalladas sobre el contenido del plan.** Cuando el usuario pregunte por detalles del plan (qué comer en 
una comida concreta, qué día toca tal cosa, sustituciones permitidas, hidratación, suplementación, etc.), responde 
basándote únicamente en lo que indica el documento. Cita o parafrasea la sección relevante para que el usuario pueda 
ubicarla.

# Contexto

- El plan nutricional del usuario está adjunto más abajo como documento PDF. Es tu fuente principal de verdad.
- Puedes recibir además notas de contexto sobre el cliente (alergias, preferencias, objetivos, condiciones médicas, 
etc.). Úsalas para personalizar tus respuestas siempre que sea relevante.
- Detrás del plan hay un nutricionista humano: cualquier cambio real al plan le corresponde a él.

# Formato y restricciones

- Responde siempre en el mismo idioma en que te escriba el usuario.
- Sé conciso, cercano y profesional. Usa listas y pasos cortos cuando ayuden a la claridad.
- Si la información no está en el plan o no estás seguro, dilo claramente y recomienda consultar con su nutricionista 
en lugar de inventar.
- No des consejos médicos ni modifiques el plan; ese es el trabajo del nutricionista.
- Si el usuario pregunta algo no relacionado con la nutrición o su plan, redirige la conversación con amabilidad.
"""


def _get_db_uri():
    db = settings.DATABASES['default']
    user = db.get('USER', '')
    password = db.get('PASSWORD', '')
    host = db.get('HOST', 'localhost')
    port = db.get('PORT', '5432')
    name = db['NAME']
    if user:
        auth = f"{user}:{password}@" if password else f"{user}@"
    else:
        auth = ""
    return f"postgresql://{auth}{host}:{port}/{name}"


class GraphManager:
    def __init__(self):
        self._model = None
        self._setup_done = False

    def _get_model(self):
        if self._model is None:
            self._model = init_chat_model("google_genai:gemini-3-flash-preview")
        return self._model

    @asynccontextmanager
    async def graph(self):
        """Open a fresh Postgres connection for the duration of a single request, compile the graph with it, then close."""
        async with AsyncPostgresSaver.from_conn_string(_get_db_uri()) as checkpointer:
            if not self._setup_done:
                await checkpointer.setup()
                self._setup_done = True
            builder = StateGraph(MessagesState)
            builder.add_node("call_model", self.call_model)
            builder.add_edge(START, "call_model")
            builder.add_edge("call_model", END)
            yield builder.compile(checkpointer=checkpointer)

    async def call_model(self, state: MessagesState, config: RunnableConfig):
        """Single graph node that invokes the LLM with the full conversation context. Builds the message list by
        prepending a SystemMessage with the base prompt and optional customer description, followed by the conversation
        history from state.

        NB: The nutritional plan PDF is injected as a HumanMessage (not SystemMessage) because file attachments are not
        supported in system messages by the model API.
        """
        configurable = config.get("configurable", {})
        pdf_base64 = configurable.get("pdf_base64")
        customer_description = configurable.get("customer_description", "")
        messages = list(state["messages"])

        system_content = SYSTEM_PROMPT
        if customer_description:
            system_content += f"\n\nBackground notes on this customer:\n{customer_description}"

        messages.insert(0, SystemMessage(content=system_content))

        if pdf_base64:
            messages.insert(1, HumanMessage(content=[
                {"type": "text", "text": "Here is the nutritional plan document:"},
                {
                    "type": "file",
                    "base64": pdf_base64,
                    "mime_type": "application/pdf",
                },
            ]))

        model = self._get_model()
        response = await model.ainvoke(messages)
        return {"messages": [response]}


graph_manager = GraphManager()
