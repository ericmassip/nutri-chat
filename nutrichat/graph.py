import logging
from contextlib import asynccontextmanager

from django.conf import settings
from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import END, START, MessagesState, StateGraph

log = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a helpful nutritional assistant. The user's nutritional plan is attached below. "
    "You may also be provided with background notes about the customer — "
    "use this context to personalise your responses where relevant. "
    "Answer questions about the plan accurately and helpfully. "
    "If the user asks something unrelated to nutrition, gently steer the conversation back. "
    "Be concise, friendly, and professional."
)


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
