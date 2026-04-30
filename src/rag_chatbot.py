from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
import os
from typing import Tuple, Optional, Any

from token_cost_tracker import TokenUsageMetrics, extract_token_usage


SYSTEM_PROMPT = """You are an assurance assistant.
Answer with concise, practical guidance using only the provided service signals.
If the context is insufficient, clearly say what additional signal is needed.
"""


def _query_chat(client, question: str, context: str, model: str) -> Tuple[str, Optional[TokenUsageMetrics]]:
    response = client.chat.completions.create(
        model=model,
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
        # Favor deterministic outputs for repeated questions in same context.
        temperature=0.0
    )
    answer = response.choices[0].message.content
    metrics = extract_token_usage(response, model)
    if metrics:
        metrics.question_length = len(question)
        metrics.answer_length = len(answer)
    return answer, metrics


def _query_responses(client, question: str, context: str, model: str) -> Tuple[str, Optional[TokenUsageMetrics]]:
    response = client.responses.create(
        model=model,
        input=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": f"""
Question:
{question}

Derived Service Signals:
{context}
""",
            },
        ],
        # Favor deterministic outputs for repeated questions in same context.
        temperature=0.0,
    )

    if getattr(response, "output_text", None):
        answer = response.output_text
    else:
        # Defensive extraction fallback for SDK shape variations.
        try:
            answer = response.output[0].content[0].text  # type: ignore[index]
        except Exception as exc:
            raise RuntimeError("Unable to extract text from responses API output") from exc
    
    metrics = extract_token_usage(response, model)
    if metrics:
        metrics.question_length = len(question)
        metrics.answer_length = len(answer)
    return answer, metrics


def ask_assurance_question(question: str, context: str = "") -> str:
    """Ask an assurance question and return answer (backwards compatible)."""
    answer, _ = ask_assurance_question_with_metrics(question, context)
    return answer


def ask_assurance_question_with_metrics(question: str, context: str = "") -> Tuple[str, Optional[TokenUsageMetrics]]:
    """Ask an assurance question and return answer with token usage metrics."""
    endpoint = os.environ["AZURE_OPENAI_ENDPOINT"].strip().strip('"').strip("'")
    model = os.environ["AZURE_OPENAI_MODEL"]
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    configured_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-06-01")

    if api_key:
        # Local/container path: API key auth without az/managed identity setup.
        from openai import AzureOpenAI, OpenAI

        # Foundry OpenAI-compatible endpoint path (v1 protocol) does not use Azure API versions.
        if "/protocols/openai/v1" in endpoint:
            base_url = endpoint
            if base_url.endswith("/responses"):
                base_url = base_url[: -len("/responses")]
            candidate_versions = [
                configured_version,
                "2024-10-21",
                "2024-08-01-preview",
                "2024-06-01",
                "2024-05-01-preview",
                "2024-02-15-preview",
            ]
            tried = set()
            last_error = None

            for api_version in candidate_versions:
                if api_version in tried:
                    continue
                tried.add(api_version)

                try:
                    client = OpenAI(
                        api_key=api_key,
                        base_url=base_url,
                        default_query={"api-version": api_version},
                    )
                    return _query_responses(client, question, context, model)
                except Exception as exc:
                    last_error = exc
                    message = str(exc).lower()
                    if "api version" in message and "not supported" in message:
                        continue
                    if "missing required query parameter" in message and "api-version" in message:
                        continue
                    raise

            if last_error is not None:
                raise last_error
            raise RuntimeError("Foundry OpenAI-compatible request failed for unknown reason")

        # Try configured version first, then common Azure OpenAI versions.
        candidate_versions = [
            configured_version,
            "2024-06-01",
            "2024-02-15-preview",
            "2023-12-01-preview",
        ]
        tried = set()
        last_error = None

        for api_version in candidate_versions:
            if api_version in tried:
                continue
            tried.add(api_version)

            try:
                client = AzureOpenAI(
                    api_key=api_key,
                    api_version=api_version,
                    azure_endpoint=endpoint,
                )
                return _query_chat(client, question, context, model)
            except Exception as exc:
                last_error = exc
                message = str(exc).lower()
                if "api version" in message and "not supported" in message:
                    continue
                raise

        if last_error is not None:
            raise last_error
        raise RuntimeError("Azure OpenAI request failed for unknown reason")
    else:
        project_client = AIProjectClient(
            endpoint=endpoint,
            credential=DefaultAzureCredential(),
        )
        client = project_client.get_openai_client()
        return _query_chat(client, question, context, model)