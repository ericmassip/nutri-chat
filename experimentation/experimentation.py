import base64
import json
from pathlib import Path

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage

# Load environment variables
load_dotenv()

# Paths
DATA_DIR = Path(__file__).parent / "data"
PDF_PATH = DATA_DIR / "atletismo_hombre.pdf"
TEST_JSON_PATH = DATA_DIR / "test_atletismo_hombre.json"
GROUND_TRUTH_PATH = DATA_DIR / "atletismo_hombre.json"


def load_pdf_as_base64(filepath: Path) -> str:
    """Load PDF and encode as base64."""
    with open(filepath, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def load_json(filepath: Path) -> dict:
    """Load JSON file."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_answers(model) -> str:
    """
    Step 1: Send PDF + test JSON to model, get filled JSON back.
    """
    print(f"\n{'=' * 60}")
    print("Step 1: Generating answers")
    print(f"{'=' * 60}\n")

    # Load data
    pdf_base64 = load_pdf_as_base64(PDF_PATH)
    test_data = load_json(TEST_JSON_PATH)
    test_json_str = json.dumps(test_data, indent=2, ensure_ascii=False)

    # Create message with PDF attachment using standardized content blocks
    message = HumanMessage(
        content_blocks=[
            {
                "type": "text",
                "text": f"""Dado el siguiente plan nutricional en PDF y este JSON con preguntas, rellena TODOS los campos "answer" basándote ÚNICAMENTE en la información del PDF.

IMPORTANTE:
- Responde de manera concisa y precisa
- Si la información no está en el PDF, responde "No se especifica en el plan"
- Devuelve SOLAMENTE el JSON completo con las respuestas rellenadas, sin explicaciones adicionales
- Mantén el mismo formato y estructura del JSON

JSON con preguntas:
{test_json_str}""",
            },
            {
                "type": "file",
                "base64": pdf_base64,
                "mime_type": "application/pdf",
            },
        ]
    )

    # Invoke model
    print("Enviando PDF y preguntas al modelo...")
    response = model.invoke([message])

    # Extract text from AIMessage content
    if isinstance(response.content, list):
        # Content is a list of blocks, extract text from first text block
        predicted_json = next(
            (
                block["text"]
                for block in response.content
                if block.get("type") == "text"
            ),
            "",
        )
    else:
        # Content is a simple string
        predicted_json = response.content

    print(f"\nRespuesta recibida ({len(predicted_json)} caracteres)")
    print("\nPrimeras líneas de la respuesta:")
    print(predicted_json[:500])
    print("...\n")

    return predicted_json


def evaluate_answers(model, predicted_json: str) -> dict:
    """
    Step 2: Compare predicted JSON with ground truth using LLM as judge.
    """
    print(f"\n{'=' * 60}")
    print("Step 2: Evaluating answers")
    print(f"{'=' * 60}\n")

    # Load ground truth
    ground_truth = load_json(GROUND_TRUTH_PATH)
    ground_truth_str = json.dumps(ground_truth, indent=2, ensure_ascii=False)

    # Create evaluation message
    message = HumanMessage(
        content=f"""Compara las respuestas predichas con las respuestas correctas (ground truth).

GROUND TRUTH (respuestas correctas):
{ground_truth_str}

RESPUESTAS PREDICHAS:
{predicted_json}

Evalúa la precisión general considerando:
1. Exactitud factual (¿los números/valores son correctos?)
2. Equivalencia semántica (¿significan lo mismo aunque usen palabras diferentes?)
3. Completitud (¿incluye toda la información necesaria?)

Proporciona tu evaluación en formato JSON con la siguiente estructura:
{{
  "score": <número de 0 a 100>,
  "correct": <número de respuestas correctas>,
  "partial": <número de respuestas parcialmente correctas>,
  "incorrect": <número de respuestas incorrectas>,
  "reasoning": "<explicación breve de tu evaluación>",
  "examples": {{
    "correct": ["ejemplo de pregunta respondida correctamente"],
    "incorrect": ["ejemplo de pregunta respondida incorrectamente"]
  }}
}}

Devuelve SOLAMENTE el JSON, sin explicaciones adicionales."""
    )

    print("Enviando evaluación al juez...")
    response = model.invoke([message])

    # Extract text from AIMessage content
    if isinstance(response.content, list):
        # Content is a list of blocks, extract text from first text block
        evaluation_text = next(
            (
                block["text"]
                for block in response.content
                if block.get("type") == "text"
            ),
            "",
        )
    else:
        # Content is a simple string
        evaluation_text = response.content

    print("\nEvaluación recibida:\n")
    print(evaluation_text)

    # Parse JSON from response
    try:
        # Try to extract JSON if wrapped in markdown
        if "```json" in evaluation_text:
            json_start = evaluation_text.find("```json") + 7
            json_end = evaluation_text.find("```", json_start)
            evaluation_text = evaluation_text[json_start:json_end].strip()
        elif "```" in evaluation_text:
            json_start = evaluation_text.find("```") + 3
            json_end = evaluation_text.find("```", json_start)
            evaluation_text = evaluation_text[json_start:json_end].strip()

        evaluation = json.loads(evaluation_text)
    except json.JSONDecodeError as e:
        print(f"\nError parsing JSON: {e}")
        evaluation = {
            "error": "Could not parse evaluation JSON",
            "raw": evaluation_text,
        }

    return evaluation


def display_results(evaluation: dict):
    """Display evaluation results in a readable format."""
    print(f"\n{'=' * 60}")
    print("RESULTADOS DE LA EVALUACIÓN")
    print(f"{'=' * 60}\n")

    if "error" in evaluation:
        print(f"Error: {evaluation['error']}")
        return

    print(f"Puntuación general: {evaluation.get('score', 'N/A')}/100")
    print(f"Respuestas correctas: {evaluation.get('correct', 'N/A')}")
    print(f"Respuestas parciales: {evaluation.get('partial', 'N/A')}")
    print(f"Respuestas incorrectas: {evaluation.get('incorrect', 'N/A')}")
    print("\nRazonamiento:")
    print(evaluation.get("reasoning", "N/A"))

    if "examples" in evaluation:
        print("\nEjemplos de respuestas correctas:")
        for ex in evaluation["examples"].get("correct", [])[:3]:
            print(f"  - {ex}")

        print("\nEjemplos de respuestas incorrectas:")
        for ex in evaluation["examples"].get("incorrect", [])[:3]:
            print(f"  - {ex}")


def main():
    """Run the full evaluation pipeline."""
    print("\n🧪 Evaluación de Modelo LLM para Planes Nutricionales")
    print(f"{'=' * 60}\n")

    # Initialize model (model-agnostic)
    model = init_chat_model("google_genai:gemini-3-flash-preview", temperature=0)

    # Step 1: Generate answers
    predicted_json = generate_answers(model)

    # Step 2: Evaluate answers
    evaluation = evaluate_answers(model, predicted_json)

    # Display results
    display_results(evaluation)

    # Save results
    results_path = DATA_DIR / "evaluation_results.json"
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(
            {"predicted": predicted_json, "evaluation": evaluation},
            f,
            indent=2,
            ensure_ascii=False,
        )
    print(f"\n✅ Resultados guardados en: {results_path}")


if __name__ == "__main__":
    main()
