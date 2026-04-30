import json
import logging
import os
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List

from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel

SRC_DIR = Path(__file__).resolve().parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

from rag_chatbot import ask_assurance_question, ask_assurance_question_with_metrics  # noqa: E402
from insight_generator import generate_insight  # noqa: E402


class ChatRequest(BaseModel):
    question: str
    context: Dict[str, Any] | None = None


app = FastAPI(title="chat-service", version="0.1.0")
INTERNAL_API_TOKEN = os.getenv("INTERNAL_API_TOKEN", "")
LOGGER = logging.getLogger("chat-service")
if not LOGGER.handlers:
    logging.basicConfig(level=logging.INFO)


def _log_event(event: str, **kwargs) -> None:
    LOGGER.info(json.dumps({"event": event, **kwargs}, default=str))


@app.middleware("http")
async def correlation_middleware(request: Request, call_next):
    correlation_id = request.headers.get("x-correlation-id") or str(uuid.uuid4())
    request.state.correlation_id = correlation_id
    start = time.time()
    response = await call_next(request)
    response.headers["x-correlation-id"] = correlation_id
    _log_event(
        "request",
        correlation_id=correlation_id,
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        latency_ms=int((time.time() - start) * 1000),
    )
    return response


def _require_internal_token(x_internal_token: str | None) -> None:
    if not INTERNAL_API_TOKEN:
        return
    if x_internal_token != INTERNAL_API_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "chat-service"}


@app.post("/ask")
def ask(payload: ChatRequest, x_internal_token: str | None = Header(default=None, alias="x-internal-token")) -> dict:
    _require_internal_token(x_internal_token)

    if not payload.question.strip():
        raise HTTPException(status_code=400, detail="question must not be empty")

    context_text = ""
    if payload.context:
        context_text = json.dumps(payload.context, indent=2)

    try:
        answer, metrics = ask_assurance_question_with_metrics(payload.question, context_text)
        response_data: Dict[str, Any] = {"answer": answer}
        
        # Include token metrics if available
        if metrics:
            response_data["tokens"] = metrics.to_dict()
            _log_event("chat_completed", metrics=metrics.to_dict())
        else:
            _log_event("chat_completed")
        
        return response_data
    except Exception as exc:
        fallback_context = payload.context or {}
        signals = fallback_context.get("signals", [])
        assurance = fallback_context.get("assurance", {})

        if not assurance:
            assurance = {
                "assurance_domain": ["UNKNOWN"],
                "service_impact": "UNKNOWN",
                "root_cause_likelihood": "UNDETERMINED",
            }

        answer = (
            "LLM backend unavailable. Showing deterministic assurance summary from extracted signals.\n\n"
            + generate_insight(signals, assurance)
        )
        _log_event("chat_fallback", error=str(exc))
        return {"answer": answer, "fallback": True, "reason": "LLM backend unavailable"}
