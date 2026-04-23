import os
import json
from dotenv import load_dotenv, dotenv_values

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ENV_PATH = os.path.join(_BASE_DIR, ".env")


def export_required_env_vars() -> None:
    """
    Loads required settings from .env and explicitly exports them to os.environ.
    """
    load_dotenv(_ENV_PATH)
    file_values = dotenv_values(_ENV_PATH)

    required_vars = [
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_MODEL",
        "AZURE_SEARCH_ENDPOINT",
        "AZURE_SEARCH_INDEX",
    ]

    missing = []
    for key in required_vars:
        existing_value = os.getenv(key)
        if existing_value is not None and str(existing_value).strip() != "":
            continue

        file_value = file_values.get(key)
        if file_value is None or str(file_value).strip() == "":
            missing.append(key)
            continue
        os.environ[key] = str(file_value)

    if missing:
        missing_csv = ", ".join(missing)
        raise RuntimeError(f"Missing required environment variables: {missing_csv}")


export_required_env_vars()

from log_reader import read_logs
from signal_engine import extract_service_signals
from assurance_model import classify_assurance
from rag_indexer import index_signals
from rag_chatbot import ask_assurance_question

def main():
    logs = read_logs(os.path.join(_BASE_DIR, "logs", "sample_oss_logs.txt"))
    signals = extract_service_signals(logs)
    assurance = classify_assurance(signals)
    context = json.dumps(
        {
            "signals": signals,
            "assurance": assurance,
        },
        indent=2,
    )

    # Index only high‑signal artifacts
    index_signals(signals)

    print("\nAzure AI Foundry Service Assurance Bot\n")
    while True:
        question = input("Question (or 'exit'): ")
        if question.lower() == "exit":
            break

        answer = ask_assurance_question(question, context)
        print("\n" + answer + "\n")


if __name__ == "__main__":
    main()