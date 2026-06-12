"""Production AI agent for the Day 12 final lab."""

import json
import logging
import signal
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, Request, Response, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel, Field
import uvicorn

from app.config import settings
from utils.mock_llm import ask as llm_ask

try:
    import redis as redis_lib
except Exception:  # pragma: no cover - optional dependency path
    redis_lib = None


logging.basicConfig(level=logging.DEBUG if settings.debug else logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

START_TIME = time.time()
_is_ready = False
_request_count = 0
_error_count = 0
_rate_windows: dict[str, deque] = defaultdict(deque)
_daily_cost = 0.0
_cost_reset_day = time.strftime("%Y-%m-%d")
redis_client = None


if settings.redis_url and redis_lib is not None:
    try:
        redis_client = redis_lib.from_url(settings.redis_url, decode_responses=True)
        redis_client.ping()
        logger.info(json.dumps({"event": "redis_connected", "url": settings.redis_url}))
    except Exception as exc:
        logger.warning(json.dumps({"event": "redis_unavailable", "error": str(exc)}))
        redis_client = None


def _json_log(event: str, **fields) -> None:
    payload = {"event": event, **fields}
    logger.info(json.dumps(payload))


def _cost_key() -> str:
    return f"cost:{time.strftime('%Y-%m-%d')}"


def _estimate_cost(input_tokens: int, output_tokens: int) -> float:
    return (input_tokens / 1000) * 0.00015 + (output_tokens / 1000) * 0.0006


def check_rate_limit(bucket: str) -> None:
    now = time.time()
    if redis_client is not None:
        key = f"rate:{bucket}"
        redis_client.zremrangebyscore(key, 0, now - 60)
        current = int(redis_client.zcard(key))
        if current >= settings.rate_limit_per_minute:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded: {settings.rate_limit_per_minute} req/min",
                headers={"Retry-After": "60"},
            )
        redis_client.zadd(key, {str(now): now})
        redis_client.expire(key, 60)
        return

    window = _rate_windows[bucket]
    while window and window[0] < now - 60:
        window.popleft()
    if len(window) >= settings.rate_limit_per_minute:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded: {settings.rate_limit_per_minute} req/min",
            headers={"Retry-After": "60"},
        )
    window.append(now)


def check_and_record_cost(input_tokens: int, output_tokens: int) -> None:
    global _daily_cost, _cost_reset_day

    today = time.strftime("%Y-%m-%d")
    if today != _cost_reset_day:
        _daily_cost = 0.0
        _cost_reset_day = today

    cost = _estimate_cost(input_tokens, output_tokens)
    if cost <= 0:
        return

    if redis_client is not None:
        key = _cost_key()
        current = float(redis_client.get(key) or 0.0)
        if current + cost > settings.daily_budget_usd:
            raise HTTPException(status_code=503, detail="Daily budget exhausted. Try tomorrow.")
        redis_client.incrbyfloat(key, cost)
        redis_client.expire(key, 32 * 24 * 3600)
        return

    if _daily_cost + cost > settings.daily_budget_usd:
        raise HTTPException(status_code=503, detail="Daily budget exhausted. Try tomorrow.")
    _daily_cost += cost


api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    if not api_key or api_key != settings.agent_api_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key. Include header: X-API-Key: <key>",
        )
    return api_key


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _is_ready
    _json_log(
        "startup",
        app=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
    )
    _is_ready = True
    yield
    _is_ready = False
    _json_log("shutdown")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key"],
)


@app.middleware("http")
async def request_middleware(request: Request, call_next):
    global _request_count, _error_count
    start = time.time()
    _request_count += 1
    try:
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        if "server" in response.headers:
            del response.headers["server"]
        _json_log(
            "request",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            ms=round((time.time() - start) * 1000, 1),
        )
        return response
    except Exception as exc:
        _error_count += 1
        _json_log("request_error", method=request.method, path=request.url.path, error=str(exc))
        raise


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000, description="Your question for the agent")


class AskResponse(BaseModel):
    question: str
    answer: str
    model: str
    timestamp: str


@app.get("/", tags=["Info"])
def root():
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "endpoints": {
            "ask": "POST /ask (requires X-API-Key)",
            "health": "GET /health",
            "ready": "GET /ready",
        },
    }


@app.post("/ask", response_model=AskResponse, tags=["Agent"])
async def ask_agent(
    body: AskRequest,
    request: Request,
    _key: str = Depends(verify_api_key),
):
    check_rate_limit(_key[:8])

    input_tokens = len(body.question.split()) * 2
    check_and_record_cost(input_tokens, 0)

    _json_log(
        "agent_call",
        q_len=len(body.question),
        client=str(request.client.host) if request.client else "unknown",
    )

    answer = llm_ask(body.question)
    output_tokens = len(answer.split()) * 2
    check_and_record_cost(0, output_tokens)

    return AskResponse(
        question=body.question,
        answer=answer,
        model=settings.llm_model,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@app.get("/health", tags=["Operations"])
def health():
    redis_status = "disabled"
    if settings.redis_url:
        redis_status = "ok" if redis_client is not None else "unavailable"
    return {
        "status": "ok",
        "version": settings.app_version,
        "environment": settings.environment,
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "total_requests": _request_count,
        "checks": {
            "llm": "mock" if not settings.openai_api_key else "openai",
            "redis": redis_status,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/ready", tags=["Operations"])
def ready():
    if not _is_ready:
        raise HTTPException(status_code=503, detail="Not ready")
    if settings.redis_url and redis_client is None:
        raise HTTPException(status_code=503, detail="Redis unavailable")
    return {"ready": True}


@app.get("/metrics", tags=["Operations"])
def metrics(_key: str = Depends(verify_api_key)):
    daily_cost = redis_client.get(_cost_key()) if redis_client is not None else _daily_cost
    daily_cost = float(daily_cost or 0.0)
    return {
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "total_requests": _request_count,
        "error_count": _error_count,
        "daily_cost_usd": round(daily_cost, 4),
        "daily_budget_usd": settings.daily_budget_usd,
        "budget_used_pct": round(daily_cost / settings.daily_budget_usd * 100, 1),
    }


def _handle_signal(signum, _frame):
    _json_log("signal", signum=signum)


signal.signal(signal.SIGTERM, _handle_signal)


if __name__ == "__main__":
    logger.info(f"Starting {settings.app_name} on {settings.host}:{settings.port}")
    logger.info(f"API Key prefix: {settings.agent_api_key[:4]}****")
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        timeout_graceful_shutdown=30,
    )
