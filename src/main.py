from log_reader import read_logs
from signal_engine import extract_service_signals
from assurance_model import classify_assurance
from rag_indexer import index_signals
from rag_chatbot import ask_assurance_question


def main():
    logs = read_logs("logs/sample_telco_oss_logs.txt")
    signals = extract_service_signals(logs)

    # Index only high‑signal artifacts
    index_signals(signals)

    print("\nAzure AI Foundry Service Assurance Bot\n")
    while True:
        question = input("Question (or 'exit'): ")
        if question.lower() == "exit":
            break

        answer = ask_assurance_question(question)
        print("\n" + answer + "\n")


if __name__ == "__main__":
    main()