from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
import os


SYSTEM_PROMPT = """You are an assurance assistant.
Answer with concise, practical guidance using only the provided service signals.
If the context is insufficient, clearly say what additional signal is needed.
"""


def ask_assurance_question(question: str, context: str = "") -> str:
    project_client = AIProjectClient(
        endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        credential=DefaultAzureCredential(),
    )
    client = project_client.get_openai_client()

    response = client.chat.completions.create(
        model=os.environ["AZURE_OPENAI_MODEL"],
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": f"""
Question:
{question}

Derived Service Signals:
{context}
"""
            }
        ],
        temperature=0.2
    )

    return response.choices[0].message.content