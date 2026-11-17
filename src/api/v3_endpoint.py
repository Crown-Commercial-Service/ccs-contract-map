"""
FastAPI v3 Endpoint - Production-ready contract classification API.
"""

import os
import sys
import time
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

# Ensure src/contractmap is importable when running from project root
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from fastapi import FastAPI, HTTPException, status, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
import structlog

# Redis & Cache Imports
from redis.asyncio import Redis
from redis_entraid.cred_provider import create_from_default_azure_credential
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.backends.inmemory import InMemoryBackend

# ContractMap imports
from contractmap import get_classifier, ClassificationResult
from contractmap.classifier import ClassifierSettings

# =============================================================================
# Logging Configuration - File + Console
# =============================================================================

LOGS_DIR = REPO_ROOT / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOGS_DIR / "ccs_contract_map.log"

# Configure standard Python logging to write to file + console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)

# Add file handler to uvicorn and other loggers
_file_handler = logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8")
_file_handler.setFormatter(logging.Formatter("%(asctime)s | %(name)s | %(levelname)s | %(message)s"))
for _logger_name in ["uvicorn", "uvicorn.access", "uvicorn.error", "fastapi", "contractmap", "redis"]:
    logging.getLogger(_logger_name).addHandler(_file_handler)

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)
logger.info("logging_initialized", log_file=str(LOG_FILE))


class ContractDescription(BaseModel):
    """Input contract description with validation."""
    description: str = Field(..., min_length=1, max_length=10000, description="Contract description text")

    @field_validator('description')
    @classmethod
    def sanitize_description(cls, v: str) -> str:
        cleaned = ''.join(c for c in v if c == '\n' or c == '\t' or ord(c) >= 32)
        cleaned = ' '.join(cleaned.split())
        if not cleaned:
            raise ValueError("Description cannot be empty after sanitisation")
        return cleaned


class ClassificationResponse(BaseModel):
    """Full classification response with metadata."""
    AI_label: str
    method: str
    confidence: float
    heuristic_score: int
    latency_ms: float
    tokens_used: int = 0
    cache_hit: bool = False
    runner_up: Optional[str] = None
    runner_up_score: int = 0


class StatsResponse(BaseModel):
    categories_loaded: int
    scoring_config: dict
    llm_config: dict
    cache_size: Optional[int] = None


class SimpleRateLimiter:
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = {}

    def is_allowed(self, client_ip: str) -> bool:
        now = time.time()
        if client_ip not in self._requests:
            self._requests[client_ip] = []

        self._requests[client_ip] = [
            t for t in self._requests[client_ip]
            if now - t < self.window_seconds
        ]

        if len(self._requests[client_ip]) >= self.max_requests:
            return False

        self._requests[client_ip].append(now)
        return True


rate_limiter = SimpleRateLimiter(
    max_requests=int(os.getenv("RATE_LIMIT_REQUESTS", "100")),
    window_seconds=int(os.getenv("RATE_LIMIT_WINDOW", "60"))
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown."""
    logger.info("api_starting", version="0.2.1")

    redis_client: Optional[Redis] = None
    REDIS_SCOPE = ("https://redis.azure.com/.default",)
    redis_host = os.getenv("REDIS_HOST")

    if redis_host:
        try:
            cred_provider = create_from_default_azure_credential(
                scopes=REDIS_SCOPE
            )

            redis_client = Redis(
                host=redis_host,
                port=6380,
                ssl=True,
                credential_provider=cred_provider,
                socket_timeout=5,
            )

            await redis_client.ping()

            FastAPICache.init(
                RedisBackend(redis_client), prefix="ccs-mapper-cache"
            )
            logger.info("redis_cache_initialized", host=redis_host)
        except Exception as e:
            logger.warning(
                "redis_connection_failed_fallback_inmemory",
                error=str(e),
                exc_info=True,
            )
            redis_client = None
            FastAPICache.init(InMemoryBackend(), prefix="ccs-mapper-cache")
    else:
        logger.info("redis_host_not_set_using_inmemory_cache")
        FastAPICache.init(InMemoryBackend(), prefix="ccs-mapper-cache")

    try:
        classifier = get_classifier()
        app.state.classifier = classifier

        stats = classifier.get_stats()
        logger.info("classifier_initialized", **stats)
    except Exception as e:
        logger.error("classifier_init_failed", error=str(e), exc_info=True)
        if redis_client is not None:
            await redis_client.aclose()
        raise

    yield
    logger.info("api_shutting_down")

    if redis_client is not None:
        try:
            await redis_client.aclose()
            logger.info("redis_connection_closed")
        except Exception as e:
            logger.warning("redis_close_failed", error=str(e))


# FastAPI App
app = FastAPI(
    title="CCS Contract Map API",
    description="Hybrid keyword + LLM classifier for CCS contract categories",
    version="0.2.1",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


@app.get("/healthz", tags=["Health"])
async def health_check():
    """Kubernetes liveness probe - basic health check."""
    return {"status": "healthy", "version": "0.2.1"}


@app.get("/readyz", tags=["Health"])
async def readiness_check():
    """Kubernetes readiness probe - checks dependencies."""
    checks = {"api": "ok"}
    try:
        classifier = get_classifier()
        if classifier.heuristic._categories:
            checks["classifier"] = "ok"
        else:
            checks["classifier"] = "no_categories_loaded"
    except Exception as e:
        checks["classifier"] = f"error: {type(e).__name__}"

    all_healthy = all(v == "ok" for v in checks.values())
    status_code = 200 if all_healthy else 503
    return JSONResponse(
        status_code=status_code,
        content={"status": "ready" if all_healthy else "not_ready", "checks": checks}
    )


@app.get("/stats", response_model=StatsResponse, tags=["Monitoring"])
async def get_stats(request: Request):
    """Get classifier statistics."""
    classifier = getattr(request.app.state, "classifier", None) or get_classifier()
    return classifier.get_stats()


@app.post(
    "/v0.2.1/map",
    response_model=ClassificationResponse,
    tags=["Classification"],
)
async def classify_contract(body: ContractDescription, request: Request):
    classifier = getattr(request.app.state, "classifier", None) or get_classifier()

    try:
        result: ClassificationResult = await classifier.classify(body.description)

        logger.info(
            "classification_completed",
            category=result.category,
            method=result.method,
            confidence=result.confidence,
            latency_ms=result.latency_ms
        )

        return ClassificationResponse(
            AI_label=result.category,
            method=result.method,
            confidence=result.confidence,
            heuristic_score=result.heuristic_score,
            latency_ms=result.latency_ms,
            tokens_used=result.tokens_used,
            cache_hit=result.cache_hit,
            runner_up=result.runner_up,
            runner_up_score=result.runner_up_score,
        )

    except Exception as e:
        logger.error("classification_failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Classification failed. Please try again."
        )


# Backward Compatibility Endpoint
@app.post("/v0.2.0/map", tags=["Legacy"])
async def legacy_map(body: ContractDescription, request: Request):
    classifier = getattr(request.app.state, "classifier", None) or get_classifier()
    result = await classifier.classify(body.description)
    return {"AI_label": result.category}