import os
import json
import logging
import time
import uuid
import hashlib
import re
from typing import Any, Dict

import httpx
import jwt
from redis import asyncio as redis
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

SIGNAL_SERVICE_URL = os.getenv("SIGNAL_SERVICE_URL", "http://signal-service:8001")
INDEX_SERVICE_URL = os.getenv("INDEX_SERVICE_URL", "http://index-service:8002")
CHAT_SERVICE_URL = os.getenv("CHAT_SERVICE_URL", "http://chat-service:8003")
INTERNAL_API_TOKEN = os.getenv("INTERNAL_API_TOKEN", "")
BFF_API_KEY = os.getenv("BFF_API_KEY", "")
MAX_FILE_BYTES = int(os.getenv("MAX_FILE_BYTES", "5242880"))
MAX_RAW_LOG_CHARS = int(os.getenv("MAX_RAW_LOG_CHARS", "500000"))
MAX_QUESTION_CHARS = int(os.getenv("MAX_QUESTION_CHARS", "2000"))
MAX_SESSIONS = int(os.getenv("MAX_SESSIONS", "1000"))
SESSION_TTL_SECONDS = int(os.getenv("SESSION_TTL_SECONDS", "3600"))
REDIS_URL = os.getenv("REDIS_URL", "")
REDIS_SOCKET_CONNECT_TIMEOUT = float(os.getenv("REDIS_SOCKET_CONNECT_TIMEOUT", "5.0"))
REDIS_SOCKET_TIMEOUT = float(os.getenv("REDIS_SOCKET_TIMEOUT", "5.0"))
REDIS_SOCKET_KEEPALIVE = os.getenv("REDIS_SOCKET_KEEPALIVE", "true").lower() in {"1", "true", "yes", "on"}
REDIS_MAX_RETRIES = int(os.getenv("REDIS_MAX_RETRIES", "3"))
REDIS_RETRY_BACKOFF_MS = int(os.getenv("REDIS_RETRY_BACKOFF_MS", "100"))
CHAT_CACHE_TTL_SECONDS = int(os.getenv("CHAT_CACHE_TTL_SECONDS", "900"))
MAX_CHAT_CACHE_ITEMS = int(os.getenv("MAX_CHAT_CACHE_ITEMS", "5000"))
CHAT_SIMILARITY_THRESHOLD = float(os.getenv("CHAT_SIMILARITY_THRESHOLD", "0.50"))
JWT_REQUIRED = os.getenv("JWT_REQUIRED", "false").lower() in {"1", "true", "yes", "on"}
JWT_SECRET = os.getenv("JWT_SECRET", "")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ISSUER = os.getenv("JWT_ISSUER", "")
JWT_AUDIENCE = os.getenv("JWT_AUDIENCE", "")
CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:8080,http://127.0.0.1:8080").split(",")
    if origin.strip()
]

app = FastAPI(title="presentation-bff", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["Content-Type", "X-API-Key"],
)

SESSION_CONTEXT: Dict[str, Dict[str, Any]] = {}
CHAT_CACHE_CONTEXT: Dict[str, Dict[str, Any]] = {}
REDIS_CLIENT: redis.Redis | None = None
LOGGER = logging.getLogger("bff")
if not LOGGER.handlers:
    logging.basicConfig(level=logging.INFO)


class ChatPayload(BaseModel):
    session_id: str
    question: str


def _log_event(event: str, **kwargs: Any) -> None:
    payload = {"event": event, **kwargs}
    LOGGER.info(json.dumps(payload, default=str))


def _prune_sessions() -> None:
    now = time.time()
    expired = [
        session_id
        for session_id, value in SESSION_CONTEXT.items()
        if now - float(value.get("created_at", now)) > SESSION_TTL_SECONDS
    ]
    for session_id in expired:
        SESSION_CONTEXT.pop(session_id, None)

    # Bound memory growth under abusive or unattended workloads.
    while len(SESSION_CONTEXT) > MAX_SESSIONS:
        oldest_session = min(
            SESSION_CONTEXT.items(),
            key=lambda item: float(item[1].get("created_at", now)),
        )[0]
        SESSION_CONTEXT.pop(oldest_session, None)


def _prune_chat_cache() -> None:
    now = time.time()
    expired = [
        cache_key
        for cache_key, value in CHAT_CACHE_CONTEXT.items()
        if now - float(value.get("created_at", now)) > CHAT_CACHE_TTL_SECONDS
    ]
    for cache_key in expired:
        CHAT_CACHE_CONTEXT.pop(cache_key, None)

    while len(CHAT_CACHE_CONTEXT) > MAX_CHAT_CACHE_ITEMS:
        oldest_key = min(
            CHAT_CACHE_CONTEXT.items(),
            key=lambda item: float(item[1].get("created_at", now)),
        )[0]
        CHAT_CACHE_CONTEXT.pop(oldest_key, None)


def _normalize_question(question: str) -> str:
    return " ".join(question.strip().lower().split())


STOP_WORDS = {
    "a", "an", "the", "is", "are", "am", "to", "of", "in", "on", "for", "and", "or",
    "what", "which", "how", "why", "can", "could", "would", "should", "do", "does", "did",
    "this", "that", "these", "those", "with", "from", "about", "there", "here", "see", "any",
    "you", "we", "i", "it", "me", "my", "our", "your", "their", "logs", "log", "present",
}

TOKEN_SYNONYMS = {
    "abnormal": "anomaly",
    "abnormality": "anomaly",
    "anomalies": "anomaly",
    "unusual": "anomaly",
    "issue": "problem",
    "issues": "problem",
    "errors": "error",
    "failures": "failure",
    "behaviour": "behavior",
    "degradation": "degrade",
    "degraded": "degrade",
    "impacting": "impact",
    "impacted": "impact",
}

_NEGATION_WORDS = {"not", "no", "never", "without", "none", "neither"}

_TEMPORAL_PARAM_WORDS = {
    "yesterday", "today", "tomorrow", "morning", "afternoon",
    "evening", "night", "midnight", "noon",
}

_PARAM_RE = re.compile(
    r"\b\d{1,2}:\d{2}(?::\d{2})?\b"          # HH:MM or HH:MM:SS
    r"|\b\d+\s*(?:am|pm)\b"                   # 9am, 11 pm
    r"|\b\d{4}[-/]\d{2}[-/]\d{2}\b"           # YYYY-MM-DD
    r"|\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b"     # MM/DD/YYYY
    r"|\b\d{1,3}(?:\.\d{1,3}){3}\b"           # IP addresses
    r"|\b\d+\b",                               # standalone numbers
    re.IGNORECASE,
)


def _extract_params(question: str) -> list[str]:
    """Extract concrete parameter values (numbers, times, dates, IPs, temporal
    words) from a question.  Two questions with identical intent but different
    parameters must NOT share a cache entry."""
    normalized = _normalize_question(question)
    params = _PARAM_RE.findall(normalized)
    result = [" ".join(p.split()) for p in params]
    words = set(re.findall(r"[a-z]+", normalized))
    result.extend(sorted(words & _TEMPORAL_PARAM_WORDS))
    return sorted(set(result))


def _tokenize_intent(question: str) -> list[str]:
    words = re.findall(r"[a-z0-9]+", _normalize_question(question))
    intent_tokens: list[str] = []
    for word in words:
        if word in STOP_WORDS and word not in _NEGATION_WORDS:
            continue
        canonical = TOKEN_SYNONYMS.get(word, word)
        if len(canonical) < 3 and word not in _NEGATION_WORDS:
            continue
        intent_tokens.append(canonical)
    # Keep stable ordering while deduplicating.
    return list(dict.fromkeys(intent_tokens))


def _intent_similarity(tokens_a: list[str], tokens_b: list[str]) -> float:
    if not tokens_a or not tokens_b:
        return 0.0
    a = set(tokens_a)
    b = set(tokens_b)
    intersection = len(a & b)
    union = len(a | b)
    if union == 0:
        return 0.0
    return intersection / union


def _chat_cache_key(session_id: str, question: str) -> str:
    normalized = _normalize_question(question)
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return f"chatcache:{session_id}:{digest}"


async def _set_chat_cache(session_id: str, question: str, response_payload: Dict[str, Any]) -> None:
    key = _chat_cache_key(session_id, question)
    normalized = _normalize_question(question)
    intent_tokens = _tokenize_intent(question)
    params = _extract_params(question)
    entry = {
        "q": normalized,
        "tokens": intent_tokens,
        "params": params,
        "payload": response_payload,
        "created_at": time.time(),
    }

    if REDIS_CLIENT is not None:
        await REDIS_CLIENT.setex(key, CHAT_CACHE_TTL_SECONDS, json.dumps(response_payload))
        index_key = f"chatcache-index:{session_id}"
        raw = await REDIS_CLIENT.get(index_key)
        index_entries = json.loads(raw) if raw else []
        index_entries.append(entry)
        # Keep only newest N entries to bound lookup cost.
        index_entries = index_entries[-100:]
        await REDIS_CLIENT.setex(index_key, CHAT_CACHE_TTL_SECONDS, json.dumps(index_entries))
        return

    _prune_chat_cache()
    CHAT_CACHE_CONTEXT[key] = entry


async def _get_similar_chat_cache(session_id: str, question: str) -> tuple[Dict[str, Any] | None, float]:
    query_tokens = _tokenize_intent(question)
    query_params = _extract_params(question)
    best_payload: Dict[str, Any] | None = None
    best_score = 0.0

    if REDIS_CLIENT is not None:
        index_key = f"chatcache-index:{session_id}"
        raw = await REDIS_CLIENT.get(index_key)
        if not raw:
            return None, 0.0
        entries = json.loads(raw)
    else:
        _prune_chat_cache()
        prefix = f"chatcache:{session_id}:"
        entries = [
            value
            for cache_key, value in CHAT_CACHE_CONTEXT.items()
            if cache_key.startswith(prefix)
        ]

    for entry in entries:
        # Parameters (numbers, times, dates, IPs, temporal words) must
        # match exactly — otherwise the questions target different data
        # even when their intent tokens are similar.
        entry_params = entry.get("params", [])
        if entry_params != query_params:
            continue
        score = _intent_similarity(query_tokens, entry.get("tokens", []))
        if score > best_score:
            best_score = score
            best_payload = entry.get("payload")

    if best_payload is None or best_score < CHAT_SIMILARITY_THRESHOLD:
        return None, best_score
    return best_payload, best_score


async def _get_chat_cache(session_id: str, question: str) -> Dict[str, Any] | None:
    key = _chat_cache_key(session_id, question)
    if REDIS_CLIENT is not None:
        payload = await REDIS_CLIENT.get(key)
        if not payload:
            return None
        return json.loads(payload)

    _prune_chat_cache()
    cached = CHAT_CACHE_CONTEXT.get(key)
    if not cached:
        return None
    return cached.get("payload")


@app.on_event("startup")
async def startup_event() -> None:
    global REDIS_CLIENT
    if REDIS_URL:
        REDIS_CLIENT = redis.from_url(
            REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=REDIS_SOCKET_CONNECT_TIMEOUT,
            socket_timeout=REDIS_SOCKET_TIMEOUT,
            socket_keepalive=REDIS_SOCKET_KEEPALIVE,
            max_retries=REDIS_MAX_RETRIES,
            retry_on_timeout=True,
        )
        try:
            await REDIS_CLIENT.ping()
            _log_event(
                "redis_connected",
                connect_timeout=REDIS_SOCKET_CONNECT_TIMEOUT,
                socket_timeout=REDIS_SOCKET_TIMEOUT,
                max_retries=REDIS_MAX_RETRIES,
                ttl_seconds=SESSION_TTL_SECONDS,
            )
        except Exception as e:
            REDIS_CLIENT = None
            _log_event("redis_unavailable_fallback_memory", error=str(e))


@app.on_event("shutdown")
async def shutdown_event() -> None:
    if REDIS_CLIENT is not None:
        await REDIS_CLIENT.close()


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


def _require_api_key(request: Request) -> None:
    # Optional control for local dev; enforce in production by setting BFF_API_KEY.
    if not BFF_API_KEY:
        return

    provided = request.headers.get("x-api-key", "")
    if provided != BFF_API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")


def _require_jwt(request: Request) -> None:
    if not JWT_REQUIRED:
        return
    if not JWT_SECRET:
        raise HTTPException(status_code=500, detail="JWT configuration missing")

    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")

    token = auth_header.split(" ", 1)[1].strip()
    options = {"verify_aud": bool(JWT_AUDIENCE), "verify_iss": bool(JWT_ISSUER)}
    try:
        jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
            audience=JWT_AUDIENCE or None,
            issuer=JWT_ISSUER or None,
            options=options,
        )
    except Exception:
        raise HTTPException(status_code=401, detail="Unauthorized")


def _internal_headers(correlation_id: str) -> Dict[str, str]:
    headers: Dict[str, str] = {"x-correlation-id": correlation_id}
    if not INTERNAL_API_TOKEN:
        return headers
    headers["x-internal-token"] = INTERNAL_API_TOKEN
    return headers


async def _set_session(session_id: str, context: Dict[str, Any]) -> None:
    if REDIS_CLIENT is not None:
        await REDIS_CLIENT.setex(f"session:{session_id}", SESSION_TTL_SECONDS, json.dumps(context))
        return

    _prune_sessions()
    SESSION_CONTEXT[session_id] = {**context, "created_at": time.time()}


async def _get_session(session_id: str) -> Dict[str, Any] | None:
    if REDIS_CLIENT is not None:
        payload = await REDIS_CLIENT.get(f"session:{session_id}")
        if not payload:
            return None
        return json.loads(payload)

    _prune_sessions()
    return SESSION_CONTEXT.get(session_id)


@app.get("/api/health")
async def health() -> dict:
    async with httpx.AsyncClient(timeout=20.0) as client:
        checks = {}
        for name, url in {
            "signal-service": f"{SIGNAL_SERVICE_URL}/health",
            "index-service": f"{INDEX_SERVICE_URL}/health",
            "chat-service": f"{CHAT_SERVICE_URL}/health",
        }.items():
            try:
                response = await client.get(url)
                checks[name] = response.status_code == 200
            except Exception:
                checks[name] = False
        if REDIS_URL:
            try:
                checks["redis"] = REDIS_CLIENT is not None and bool(await REDIS_CLIENT.ping())
            except Exception:
                checks["redis"] = False
    return {"status": "ok", "dependencies": checks}


@app.post("/api/analyze-and-index")
async def analyze_and_index(
    request: Request,
    file: UploadFile | None = File(default=None),
    raw_logs: str | None = Form(default=None),
) -> dict:
    _require_api_key(request)
    _require_jwt(request)

    correlation_id = request.state.correlation_id

    if file is None and (not raw_logs or not raw_logs.strip()):
        raise HTTPException(status_code=400, detail="Provide either file or raw_logs")

    if raw_logs and len(raw_logs) > MAX_RAW_LOG_CHARS:
        raise HTTPException(status_code=413, detail="raw_logs payload too large")

    async with httpx.AsyncClient(timeout=60.0) as client:
        if file is not None:
            content = await file.read()
            if len(content) > MAX_FILE_BYTES:
                raise HTTPException(status_code=413, detail="Uploaded file too large")
            analyze_response = await client.post(
                f"{SIGNAL_SERVICE_URL}/analyze-file",
                files={"file": (file.filename or "logs.txt", content, "text/plain")},
                headers=_internal_headers(correlation_id),
            )
        else:
            analyze_response = await client.post(
                f"{SIGNAL_SERVICE_URL}/analyze",
                json={"raw_logs": raw_logs},
                headers=_internal_headers(correlation_id),
            )

        if analyze_response.status_code != 200:
            raise HTTPException(status_code=502, detail="Signal service unavailable")

        analyze_data = analyze_response.json()
        signals = analyze_data.get("signals", [])

        index_response = await client.post(
            f"{INDEX_SERVICE_URL}/index",
            json={"signals": signals},
            headers=_internal_headers(correlation_id),
        )
        index_result: Dict[str, Any]
        if index_response.status_code == 200:
            index_result = index_response.json()
        else:
            # Keep chat flow available even when search indexing/auth is unavailable.
            index_result = {
                "warning": "Indexing failed; continuing with in-session context only.",
                "status_code": index_response.status_code,
                "detail": "Indexing backend unavailable",
            }

        session_id = str(uuid.uuid4())
        context = {
            "signals": signals,
            "assurance": analyze_data.get("assurance", {}),
        }
        await _set_session(session_id, context)

    _log_event("analysis_completed", correlation_id=correlation_id, session_id=session_id, signal_count=len(signals))

    return {
        "session_id": session_id,
        "signals": signals,
        "assurance": analyze_data.get("assurance", {}),
        "index": index_result,
    }


@app.post("/api/chat")
async def chat(payload: ChatPayload, request: Request) -> dict:
    _require_api_key(request)
    _require_jwt(request)

    correlation_id = request.state.correlation_id

    if not payload.question or not payload.question.strip():
        raise HTTPException(status_code=400, detail="question must not be empty")
    if len(payload.question) > MAX_QUESTION_CHARS:
        raise HTTPException(status_code=413, detail="question payload too large")

    context = await _get_session(payload.session_id)
    if context is None:
        raise HTTPException(status_code=404, detail="Unknown session_id")

    cached = await _get_chat_cache(payload.session_id, payload.question)
    if cached is not None:
        _log_event("chat_cache_hit", correlation_id=correlation_id, session_id=payload.session_id)
        return {**cached, "cache_hit": True, "cache_match": "exact", "cache_similarity_score": 1.0}

    similar_cached, similar_score = await _get_similar_chat_cache(payload.session_id, payload.question)
    if similar_cached is not None:
        _log_event(
            "chat_cache_similar_hit",
            correlation_id=correlation_id,
            session_id=payload.session_id,
            similarity=round(similar_score, 3),
        )
        return {
            **similar_cached,
            "cache_hit": True,
            "cache_match": "similar",
            "cache_similarity_score": round(similar_score, 3),
        }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{CHAT_SERVICE_URL}/ask",
            json={"question": payload.question, "context": context},
            headers=_internal_headers(correlation_id),
        )

    if response.status_code != 200:
        raise HTTPException(status_code=502, detail="Chat backend unavailable")
    response_payload = response.json()
    await _set_chat_cache(payload.session_id, payload.question, response_payload)
    _log_event("chat_completed", correlation_id=correlation_id, session_id=payload.session_id)
    return {
        **response_payload,
        "cache_hit": False,
        "cache_match": "none",
        "cache_similarity_score": 0.0,
    }
