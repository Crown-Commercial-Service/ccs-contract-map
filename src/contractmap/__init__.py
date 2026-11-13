"""CCS Contract Map - Hybrid Keyword + LLM Classifier for CCS Categories."""

from .classifier import (
    ContractClassifier,
    ClassificationResult,
    ClassifierSettings,
    get_classifier,
    init_classifier,
    reset_classifier,
    AsyncHeuristicClassifier,
    BaseLLMCache,
    LLMCache,
    RedisLLMCache,
    OptimizedLLMClassifier,
    ScoringConfig,
)

# Backward compatibility
from .compat import (
    keywords_and_llm,
    HeuristicClassifier,
)

__version__ = "0.2.1"
__all__ = [
    "ContractClassifier",
    "ClassificationResult",
    "ClassifierSettings",
    "get_classifier",
    "init_classifier",
    "reset_classifier",
    "AsyncHeuristicClassifier",
    "BaseLLMCache",
    "LLMCache",
    "RedisLLMCache",
    "OptimizedLLMClassifier",
    "ScoringConfig",
    # Backward compatibility
    "keywords_and_llm",
    "HeuristicClassifier",
]