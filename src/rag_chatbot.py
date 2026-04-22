from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential
import os


def ask_assurance_question(question: str, context: str) -> str:
    credential = DefaultAzureCredential()

    client = AzureOpenAI(
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        azure_ad_token_provider=credential,
        api_version="2024-02-01"
    )

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