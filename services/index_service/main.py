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

from rag_indexer import index_signals  # noqa: E402


class IndexRequest(BaseModel):
    signals: List[Dict[str, Any]]


app = FastAPI(title="index-service", version="0.1.0")
INTERNAL_API_TOKEN = os.getenv("INTERNAL_API_TOKEN", "")
LOGGER = logging.getLogger("index-service")
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
    return {"status": "ok", "service": "index-service"}


@app.post("/index")
def index(payload: IndexRequest, x_internal_token: str | None = Header(default=None, alias="x-internal-token")) -> dict:
    _require_internal_token(x_internal_token)

    if not payload.signals:
        raise HTTPException(status_code=400, detail="signals must not be empty")

    try:
        index_signals(payload.signals)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Indexing backend failure") from exc

    _log_event("index_completed", signal_count=len(payload.signals))
    return {"indexed": len(payload.signals)}
