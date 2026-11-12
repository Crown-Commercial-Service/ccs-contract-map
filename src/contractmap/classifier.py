"""
Unified Contract Classifier - Hybrid Keyword + LLM with Cost Optimization.

This module replaces classification_v1.py, v2.py, v5.py, v2_mix_v5.py
with a single, configurable, production-ready classifier.
"""

import json
import os
import re
import logging
import hashlib
import time
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Any, Protocol
from functools import lru_cache

import structlog
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from langchain_openai import AzureChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

# Local imports
from .calibration import HeuristicScoreCalibrator
# from .semantic_cache import SemanticCache, HybridCache

# Configure structured logging with file output
import sys

_LOGS_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
_LOGS_DIR.mkdir(parents=True, exist_ok=True)
_LOG_FILE = _LOGS_DIR / "ccs_contract_map.log"

if not logging.getLogger().handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler(_LOG_FILE, mode="a", encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )

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


# =============================================================================
# Configuration
# =============================================================================

class ClassifierSettings(BaseSettings):
    """All classifier settings via environment variables."""
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Azure OpenAI
    azure_openai_endpoint: str = Field(..., alias="AZURE_OPENAI_ENDPOINT")
    azure_openai_key: str = Field(..., alias="AZURE_OPENAI_KEY")
    deployment_name: str = Field(..., alias="DEPLOYMENT_NAME")
    azure_openai_api_version: str = Field("2024-02-01", alias="AZURE_OPENAI_API_VERSION")

    # Classifier behavior
    keyword_threshold: int = Field(3, alias="KEYWORD_THRESHOLD")
    keyword_margin: int = Field(5, alias="KEYWORD_MARGIN")
    max_tokens: int = Field(50, alias="MAX_TOKENS")  # Increased from 6 for reliability
    temperature: float = Field(0.0, alias="TEMPERATURE")
    llm_timeout: float = Field(30.0, alias="LLM_TIMEOUT")

    # Paths
    semantic_anchors_path: Path = Field(Path("semantic_anchors.json"), alias="SEMANTIC_ANCHORS_PATH")
    system_prompt_path: Path = Field(Path("prompts/system_prompt_v2.md"), alias="SYSTEM_PROMPT_PATH")

    # Cost optimization
    enable_llm_cache: bool = Field(True, alias="ENABLE_LLM_CACHE")
    cache_ttl_seconds: int = Field(3600, alias="CACHE_TTL_SECONDS")  # 1 hour
    redis_key_prefix: str = Field("llm_classifier:", alias="REDIS_KEY_PREFIX")
    max_description_length: int = Field(10000, alias="MAX_DESCRIPTION_LENGTH")

    # Semantic cache settings
    # enable_semantic_cache: bool = Field(True, alias="ENABLE_SEMANTIC_CACHE")
    # semantic_cache_model: str = Field("all-MiniLM-L6-v2", alias="SEMANTIC_CACHE_MODEL")
    # semantic_cache_threshold: float = Field(0.92, alias="SEMANTIC_CACHE_THRESHOLD")
    # semantic_cache_max_size: int = Field(10000, alias="SEMANTIC_CACHE_MAX_SIZE")
    # semantic_cache_persist_path: Optional[Path] = Field(None, alias="SEMANTIC_CACHE_PERSIST_PATH")

    # Scoring weights (configurable)
    rm_keyword_points: int = Field(50, alias="RM_KEYWORD_POINTS")
    primary_keyword_points: int = Field(5, alias="PRIMARY_KEYWORD_POINTS")
    secondary_keyword_points: int = Field(1, alias="SECONDARY_KEYWORD_POINTS")
    

@dataclass(frozen=True)
class ScoringConfig:
    """Immutable scoring configuration."""
    rm_keyword_points: int
    primary_keyword_points: int
    secondary_keyword_points: int
    threshold: float = float(os.getenv("SCORING_THRESHOLD", 3))
    margin: float = float(os.getenv("SCORING_MARGIN", 5))

    # Specific categories keep 1.0x; broad umbrella categories are discounted
    # so specific domain hits win when both match.
    umbrella_categories: frozenset = frozenset({
        "Digital and Technology Services",
        "Professional and Business Services",
    })
    umbrella_multiplier: float = 0.75

    # Deterministic tie-breaker: higher number = more specific = wins ties
    category_priority: Dict[str, int] = field(default_factory=lambda: {
        "Outside New Taxonomy": 15,
        "Network Services": 10,
        "Cloud and Hosting": 10,
        "Software": 10,
        "Hardware": 10,
        "Fleet": 10,
        "Energy": 10,
        "Construction": 10,
        "Facilities Management": 10,
        "Travel, Accommodation and Venues": 10,
        "Financial Services": 9,
        "HR & Workforce Services": 9,
        "Digital and Technology Services": 3,
        "Professional and Business Services": 2,
    })

@dataclass
class ClassificationResult:
    """Result of classification with full metadata."""
    category: str
    method: str  # "heuristic" | "llm" | "cache"
    confidence: float  # 0.0 - 1.0
    heuristic_score: int
    latency_ms: float
    tokens_used: int = 0
    cache_hit: bool = False
    runner_up: Optional[str] = None
    runner_up_score: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "method": self.method,
            "confidence": round(self.confidence, 4),
            "heuristic_score": self.heuristic_score,
            "latency_ms": round(self.latency_ms, 2),
            "tokens_used": self.tokens_used,
            "cache_hit": self.cache_hit,
            "runner_up": self.runner_up,
            "runner_up_score": self.runner_up_score,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ClassificationResult":
        return cls(
            category=data["category"],
            method=data.get("method", "cache"),
            confidence=float(data.get("confidence", 0.0)),
            heuristic_score=int(data.get("heuristic_score", 0)),
            latency_ms=float(data.get("latency_ms", 0.0)),
            tokens_used=int(data.get("tokens_used", 0)),
            cache_hit=True,
            runner_up=data.get("runner_up"),
            runner_up_score=int(data.get("runner_up_score", 0)),
        )


# =============================================================================
# Cache Interfaces (In-Memory & Redis)
# =============================================================================

class BaseLLMCache:
    """Abstract base/protocol for async LLM cache operations."""
    async def get(self, description: str, prompt_hash: str) -> Optional[ClassificationResult]:
        raise NotImplementedError

    async def set(self, description: str, prompt_hash: str, result: ClassificationResult) -> None:
        raise NotImplementedError

    async def clear(self) -> None:
        raise NotImplementedError


class LLMCache(BaseLLMCache):
    """Fallback in-memory cache for LLM responses with TTL."""

    def __init__(self, ttl_seconds: int = 3600):
        self._cache: Dict[str, Tuple[ClassificationResult, float]] = {}
        self._ttl = ttl_seconds

    def _make_key(self, description: str, prompt_hash: str) -> str:
        desc_hash = hashlib.sha256(description.encode()).hexdigest()[:16]
        return f"{prompt_hash}:{desc_hash}"

    async def get(self, description: str, prompt_hash: str) -> Optional[ClassificationResult]:
        key = self._make_key(description, prompt_hash)
        if key in self._cache:
            result, timestamp = self._cache[key]
            if time.time() - timestamp < self._ttl:
                result.cache_hit = True
                logger.info("llm_memory_cache_hit", key=key[:32])
                return result
            else:
                del self._cache[key]
        return None

    async def set(self, description: str, prompt_hash: str, result: ClassificationResult) -> None:
        key = self._make_key(description, prompt_hash)
        self._cache[key] = (result, time.time())
        logger.info("llm_memory_cache_set", key=key[:32], cache_size=len(self._cache))

    async def clear(self) -> None:
        self._cache.clear()


class RedisLLMCache(BaseLLMCache):
    """
    Redis cache implementation using an async Redis client (e.g. from redis.asyncio).
    """

    def __init__(self, redis_client: Any, ttl_seconds: int = 3600, prefix: str = "llm_classifier:"):
        self.redis = redis_client
        self.ttl = ttl_seconds
        self.prefix = prefix

    def _make_key(self, description: str, prompt_hash: str) -> str:
        desc_hash = hashlib.sha256(description.encode()).hexdigest()[:16]
        return f"{self.prefix}{prompt_hash}:{desc_hash}"

    async def get(self, description: str, prompt_hash: str) -> Optional[ClassificationResult]:
        key = self._make_key(description, prompt_hash)
        try:
            raw_val = await self.redis.get(key)
            if raw_val is not None:
                if isinstance(raw_val, bytes):
                    raw_val = raw_val.decode("utf-8")
                data = json.loads(raw_val)
                result = ClassificationResult.from_dict(data)
                result.cache_hit = True
                result.method = "cache"
                logger.info("redis_cache_hit", key=key[:32])
                return result
        except Exception as e:
            logger.warning("redis_cache_get_failed", error=str(e), key=key[:32])
        return None

    async def set(self, description: str, prompt_hash: str, result: ClassificationResult) -> None:
        key = self._make_key(description, prompt_hash)
        try:
            data = result.to_dict()
            # Store in redis with TTL
            await self.redis.set(key, json.dumps(data), ex=self.ttl)
            logger.info("redis_cache_set", key=key[:32], ttl=self.ttl)
        except Exception as e:
            logger.warning("redis_cache_set_failed", error=str(e), key=key[:32])

    async def clear(self) -> None:
        try:
            # Clear keys matching prefix
            cursor = 0
            while True:
                cursor, keys = await self.redis.scan(cursor=cursor, match=f"{self.prefix}*")
                if keys:
                    await self.redis.delete(*keys)
                if cursor == 0:
                    break
        except Exception as e:
            logger.warning("redis_cache_clear_failed", error=str(e))


# =============================================================================
# Heuristic Classifier (Async, No Thread Pool)
# =============================================================================

class AsyncHeuristicClassifier:
    """
    Fully async heuristic classifier using pre-compiled regex.
    No blocking I/O, no thread pool needed.
    """

    def __init__(self, registry_path: Path, scoring: ScoringConfig):
        self.registry_path = registry_path
        self.scoring = scoring
        self._registry: Dict = {}
        self._compiled: Dict[str, Tuple[List[Tuple[re.Pattern, int]], List[re.Pattern]]] = {}
        self._categories: List[str] = []
        self._load_and_compile()

    def _load_and_compile(self) -> None:
        with open(self.registry_path, "r", encoding="utf-8") as f:
            self._registry = json.load(f)

        self._categories = sorted(self._registry.keys())

        for category, (primary_list, secondary_list) in self._registry.items():
            compiled_primary = []
            for word in primary_list:
                pattern = re.compile(rf"\b{re.escape(word.lower())}\b")
                points = self.scoring.rm_keyword_points if word.lower().startswith("rm") else self.scoring.primary_keyword_points
                compiled_primary.append((pattern, points))

            compiled_secondary = [
                re.compile(rf"\b{re.escape(word.lower())}\b") for word in secondary_list
            ]

            self._compiled[category] = (compiled_primary, compiled_secondary)

        logger.info("heuristic_classifier_loaded", categories=len(self._categories))

    async def classify(self, description: str) -> Tuple[Optional[str], float, Optional[str], float]:
        if not description:
            return None, 0, None, 0

        start = time.perf_counter()
        desc_lower = description.lower()
        category_scores: Dict[str, float] = {}

        for category, (primary_patterns, secondary_patterns) in self._compiled.items():
            score = 0.0
            for pattern, points in primary_patterns:
                if pattern.search(desc_lower):
                    score += points

            for pattern in secondary_patterns:
                if pattern.search(desc_lower):
                    score += self.scoring.secondary_keyword_points

            # Apply specificity discount to broad umbrella categories
            if score > 0 and category in self.scoring.umbrella_categories:
                score = max(1, round(score * self.scoring.umbrella_multiplier))

            category_scores[category] = score

        # Sort by (1) weighted score descending, then (2) category specificity priority descending
        sorted_results = sorted(
            category_scores.items(),
            key=lambda x: (x[1], self.scoring.category_priority.get(x[0], 5)),
            reverse=True,
        )

        if not sorted_results or sorted_results[0][1] == 0:
            return None, 0, None, 0

        best_cat, best_score = sorted_results[0]
        runner_up_cat, runner_up_score = sorted_results[1] if len(sorted_results) > 1 else (None, 0)

        latency = (time.perf_counter() - start) * 1000
        logger.debug(
            "heuristic_classified",
            best_cat=best_cat,
            best_score=best_score,
            runner_up=runner_up_cat,
            runner_up_score=runner_up_score,
            latency_ms=latency,
        )

        return best_cat, best_score, runner_up_cat, runner_up_score
    
    def should_use_llm(self, best_score: int, runner_up_score: int) -> bool:
        if best_score < self.scoring.threshold:
            return True
        if (best_score - runner_up_score) < self.scoring.margin:
            return True
        return False


# =============================================================================
# LLM Classifier with Cost Optimization
# =============================================================================

class OptimizedLLMClassifier:
    """
    LLM classifier with cost optimization:
    - Response caching (Redis / In-memory)
    - Truncated token usage
    - Structured output validation
    - Timeout and retry logic
    """

    VALID_CATEGORIES = frozenset([
        "Financial Services", "Fleet", "HR & Workforce Services",
        "Professional and Business Services", "Travel, Accommodation and Venues",
        "Construction", "Energy", "Facilities Management",
        "Cloud and Hosting", "Digital and Technology Services",
        "Network Services", "Software", "Hardware",
        "Outside New Taxonomy"
    ])

    def __init__(
        self,
        settings: ClassifierSettings,
        system_prompt: str,
        cache: Optional[BaseLLMCache] = None
    ):
        self.settings = settings
        self.system_prompt = system_prompt
        self._prompt_hash = hashlib.sha256(system_prompt.encode()).hexdigest()[:16]
        self.cache: Optional[BaseLLMCache] = cache

        # Build LLM with optimized settings
        self.llm = AzureChatOpenAI(
            azure_endpoint=settings.azure_openai_endpoint,
            openai_api_key=settings.azure_openai_key,
            azure_deployment=settings.deployment_name,
            openai_api_version=settings.azure_openai_api_version,
            temperature=settings.temperature,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            seed=42,
            max_tokens=settings.max_tokens,
            request_timeout=settings.llm_timeout,
            max_retries=2,
        )

        logger.info("llm_classifier_initialized",
                    deployment=settings.deployment_name,
                    max_tokens=settings.max_tokens,
                    exact_cache_enabled=settings.enable_llm_cache,
                    cache_type=type(self.cache).__name__ if self.cache else "None")

    def _truncate_description(self, description: str) -> str:
        if len(description) > self.settings.max_description_length:
            truncated = description[:self.settings.max_description_length]
            logger.warning("description_truncated", original_len=len(description), truncated_len=len(truncated))
            return truncated
        return description

    def _validate_category(self, response: str) -> str:
        cleaned = response.strip().strip('"\'').strip()
        if cleaned in self.VALID_CATEGORIES:
            return cleaned
        for cat in self.VALID_CATEGORIES:
            if cat.lower() == cleaned.lower():
                return cat
        logger.warning("llm_invalid_category", response=cleaned, valid=list(self.VALID_CATEGORIES))
        return "Outside New Taxonomy"

    async def classify(
        self,
        description: str,
        heuristic_score: float,
        heuristic_cat: Optional[str] = None,
        runner_up: Optional[str] = None,
        runner_up_score: float = 0,
    ) -> ClassificationResult:
        """Classify with async cache checks and validation."""
        start = time.perf_counter()
        description = self._truncate_description(description)

        hint_block = ""
        if heuristic_cat and heuristic_score >= self.settings.keyword_threshold:
            hint_block = (
                f"\n\n[Keyword Candidates: 1st='{heuristic_cat}' (score={heuristic_score})"
                + (f", 2nd='{runner_up}' (score={runner_up_score})" if runner_up and runner_up_score > 0 else "")
                + ". Prefer the most specific matching category over broad umbrella categories, unless the contract is genuinely outside the taxonomy (e.g. local school transport, social care, waste, or general goods).]"
            )

        llm_input = f"{description}{hint_block}"

        # 1. Check cache first (Redis or Memory)
        if self.settings.enable_llm_cache and self.cache:
            cached = await self.cache.get(llm_input, self._prompt_hash)
            if cached:
                cached.latency_ms = (time.perf_counter() - start) * 1000
                return cached

        # 2. Build messages
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=llm_input),
        ]

        # 3. Call LLM
        try:
            response = await self.llm.ainvoke(messages)
            raw_category = response.content.strip()
            category = self._validate_category(raw_category)

            tokens_used = len(self.system_prompt.split()) + len(llm_input.split()) + len(raw_category.split())

            result = ClassificationResult(
                category=category,
                method="llm",
                confidence=0.85,
                heuristic_score=heuristic_score,
                latency_ms=(time.perf_counter() - start) * 1000,
                tokens_used=tokens_used,
            )

            # 4. Cache result
            if self.settings.enable_llm_cache and self.cache:
                await self.cache.set(llm_input, self._prompt_hash, result)

            logger.info("llm_classified", category=category, tokens=tokens_used, latency_ms=result.latency_ms)
            return result

        except Exception as e:
            logger.error("llm_classification_failed", error=str(e), exc_info=True)
            return ClassificationResult(
                category="Outside New Taxonomy",
                method="llm_fallback",
                confidence=0.0,
                heuristic_score=heuristic_score,
                latency_ms=(time.perf_counter() - start) * 1000,
            )


# =============================================================================
# Unified Classifier
# =============================================================================

class ContractClassifier:
    """
    Main classifier combining heuristic + LLM with full observability.
    Supports either Redis cache (passed in from lifespan) or in-memory cache.
    """

    def __init__(
        self,
        settings: Optional[ClassifierSettings] = None,
        redis_client: Optional[Any] = None,
        cache: Optional[BaseLLMCache] = None,
    ):
        self.settings = settings or ClassifierSettings()
        self.scoring = ScoringConfig(
            rm_keyword_points=self.settings.rm_keyword_points,
            primary_keyword_points=self.settings.primary_keyword_points,
            secondary_keyword_points=self.settings.secondary_keyword_points,
            threshold=self.settings.keyword_threshold,
            margin=self.settings.keyword_margin,
        )

        with open(self.settings.system_prompt_path, "r", encoding="utf-8") as f:
            self.system_prompt = f.read()

        self.calibrator = self._load_calibrator()

        self.heuristic = AsyncHeuristicClassifier(
            self.settings.semantic_anchors_path,
            self.scoring
        )

        # Determine caching backend
        if cache:
            self.llm_cache = cache
        elif redis_client:
            self.llm_cache = RedisLLMCache(
                redis_client=redis_client,
                ttl_seconds=self.settings.cache_ttl_seconds,
                prefix=self.settings.redis_key_prefix,
            )
        elif self.settings.enable_llm_cache:
            self.llm_cache = LLMCache(self.settings.cache_ttl_seconds)
        else:
            self.llm_cache = None

        self.llm = OptimizedLLMClassifier(self.settings, self.system_prompt, self.llm_cache)

        logger.info("contract_classifier_initialized",
                    threshold=self.scoring.threshold,
                    margin=self.scoring.margin,
                    categories=len(self.heuristic._categories),
                    cache_backend=type(self.llm_cache).__name__ if self.llm_cache else "None",
                    calibrator_loaded=self.calibrator.is_fitted)

    def _load_calibrator(self) -> HeuristicScoreCalibrator:
        calibrator_path = Path("calibrator.pkl")
        if calibrator_path.exists():
            try:
                return HeuristicScoreCalibrator.load(calibrator_path)
            except Exception as e:
                logger.warning("failed_to_load_calibrator", error=str(e))
        return HeuristicScoreCalibrator()

    def _calibrate_heuristic_confidence(self, score: int) -> float:
        if self.calibrator.is_fitted:
            return self.calibrator.calibrate(score)
        return min(0.95, max(0.05, score / 100.0))

    async def classify(self, description: str) -> ClassificationResult:  # <-- ONLY description here!
        total_start = time.perf_counter()

        # Step 1: Heuristic classification
        best_cat, best_score, runner_up, runner_up_score = await self.heuristic.classify(description)

        # Step 2: Check if heuristic is confident enough
        if best_cat and not self.heuristic.should_use_llm(best_score, runner_up_score):
            return ClassificationResult(
                category=best_cat,
                method="heuristic",
                confidence=self._calibrate_heuristic_confidence(best_score),
                heuristic_score=best_score,
                latency_ms=(time.perf_counter() - total_start) * 1000,
                runner_up=runner_up,
                runner_up_score=runner_up_score,
            )

        # Step 3: Fallback to LLM (pass heuristic candidates here)
        logger.info("falling_back_to_llm",
                    heuristic_cat=best_cat,
                    heuristic_score=best_score,
                    runner_up=runner_up,
                    margin=best_score - runner_up_score,
                    required_margin=self.scoring.margin)

        llm_result = await self.llm.classify(
            description=description,
            heuristic_score=best_score,
            heuristic_cat=best_cat,
            runner_up=runner_up,
            runner_up_score=runner_up_score,
        )
        llm_result.latency_ms = (time.perf_counter() - total_start) * 1000
        llm_result.runner_up = runner_up
        llm_result.runner_up_score = runner_up_score

        return llm_result

    async def classify_batch(self, descriptions: List[str]) -> List[ClassificationResult]:
        import asyncio
        tasks = [self.classify(desc) for desc in descriptions]
        return await asyncio.gather(*tasks)

    def get_stats(self) -> Dict[str, Any]:
        stats = {
            "categories_loaded": len(self.heuristic._categories),
            "scoring_config": {
                "threshold": self.scoring.threshold,
                "margin": self.scoring.margin,
                "rm_points": self.scoring.rm_keyword_points,
                "primary_points": self.scoring.primary_keyword_points,
                "secondary_points": self.scoring.secondary_keyword_points,
            },
            "llm_config": {
                "max_tokens": self.settings.max_tokens,
                "temperature": self.settings.temperature,
                "exact_cache_enabled": self.settings.enable_llm_cache,
                "cache_backend": type(self.llm_cache).__name__ if self.llm_cache else "None",
                "cache_ttl": self.settings.cache_ttl_seconds,
            },
        }
        if self.llm_cache:
            if hasattr(self.llm_cache, '_cache'):
                stats["cache_size"] = len(self.llm_cache._cache)
            elif hasattr(self.llm_cache, 'stats'):
                stats["cache"] = self.llm_cache.stats()
        return stats


# =============================================================================
# Factory / Dependency Injection Functions
# =============================================================================

_classifier_instance: Optional[ContractClassifier] = None


def init_classifier(redis_client: Optional[Any] = None, settings: Optional[ClassifierSettings] = None) -> ContractClassifier:
    """
    Initialize the singleton classifier instance (typically called inside lifespan).
    """
    global _classifier_instance
    _classifier_instance = ContractClassifier(settings=settings, redis_client=redis_client)
    return _classifier_instance


def get_classifier(redis_client: Optional[Any] = None) -> ContractClassifier:
    """
    Get or create singleton classifier instance.
    If already initialized during lifespan, returns existing instance.
    """
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = ContractClassifier(redis_client=redis_client)
    elif redis_client is not None and not isinstance(_classifier_instance.llm_cache, RedisLLMCache):
        # Attach redis if it was initialized later
        _classifier_instance.llm_cache = RedisLLMCache(redis_client, _classifier_instance.settings.cache_ttl_seconds)
        _classifier_instance.llm.cache = _classifier_instance.llm_cache
    return _classifier_instance


def reset_classifier() -> None:
    """Reset singleton (useful for testing)."""
    global _classifier_instance
    _classifier_instance = None