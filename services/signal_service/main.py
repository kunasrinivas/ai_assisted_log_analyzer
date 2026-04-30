import csv
import io
import json
import logging
import os
import sys
import time
import uuid
from pathlib import Path
from typing import List

from fastapi import FastAPI, File, Header, HTTPException, Request, UploadFile
from pydantic import BaseModel

SRC_DIR = Path(__file__).resolve().parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

from assurance_model import classify_assurance  # noqa: E402
from log_reader import LogEvent  # noqa: E402
from signal_engine import extract_service_signals  # noqa: E402


class AnalyzeRequest(BaseModel):
    raw_logs: str


app = FastAPI(title="signal-service", version="0.1.0")
INTERNAL_API_TOKEN = os.getenv("INTERNAL_API_TOKEN", "")
MAX_FILE_BYTES = int(os.getenv("MAX_FILE_BYTES", "5242880"))
MAX_RAW_LOG_CHARS = int(os.getenv("MAX_RAW_LOG_CHARS", "500000"))
LOGGER = logging.getLogger("signal-service")
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


def _to_events(raw_logs: str) -> List[LogEvent]:
    events: List[LogEvent] = []
    reader = csv.reader(io.StringIO(raw_logs))
    for row in reader:
        if not row or row[0].strip().startswith("#"):
            continue
        if len(row) < 4:
            continue
        events.append(
            LogEvent(
                timestamp=row[0].strip(),
                level=row[1].strip(),
                system=row[2].strip(),
                message=row[3].strip(),
            )
        )
    return events


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "signal-service"}


@app.post("/analyze")
def analyze(payload: AnalyzeRequest, x_internal_token: str | None = Header(default=None, alias="x-internal-token")) -> dict:
    _require_internal_token(x_internal_token)

    if len(payload.raw_logs) > MAX_RAW_LOG_CHARS:
        raise HTTPException(status_code=413, detail="raw_logs payload too large")

    events = _to_events(payload.raw_logs)
    if not events:
        raise HTTPException(status_code=400, detail="No valid log events found")

    signals = extract_service_signals(events)
    assurance = classify_assurance(signals)
    _log_event("analyze_completed", signal_count=len(signals))
    return {"signals": signals, "assurance": assurance}


@app.post("/analyze-file")
async def analyze_file(
    file: UploadFile = File(...),
    x_internal_token: str | None = Header(default=None, alias="x-internal-token"),
) -> dict:
    _require_internal_token(x_internal_token)

    content_bytes = await file.read()
    if len(content_bytes) > MAX_FILE_BYTES:
        raise HTTPException(status_code=413, detail="Uploaded file too large")

    content = content_bytes.decode("utf-8", errors="ignore")
    return analyze(AnalyzeRequest(raw_logs=content), x_internal_token=x_internal_token)
