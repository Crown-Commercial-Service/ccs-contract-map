"""CCS Contract Map - Hybrid Keyword + LLM Classifier for CCS Categories."""

from .classifier import (
    AsyncHeuristicClassifier,
    BaseLLMCache,
    ClassificationResult,
    ClassifierSettings,
    ContractClassifier,
    LLMCache,
    OptimizedLLMClassifier,
    RedisLLMCache,
    ScoringConfig,
    get_classifier,
    init_classifier,
    reset_classifier,
)

# Backward compatibility
from .compat import (
    HeuristicClassifier,
    keywords_and_llm,
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
