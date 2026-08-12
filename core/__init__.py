# TruthGuard Core Module
"""Core components for TruthGuard hallucination detection framework."""

from .config import settings, Settings
from .utils import calculate_risk_level, safe_json_parse
from .llm import LLMProvider, get_llm_provider
from .search import SearchProvider, get_search_provider
from .embeddings import EmbeddingModel, get_embedding_model
from .blackbox import BlackBoxDetector
from .whitebox import WhiteBoxDetector
from .grounding import GroundingModule
from .judge import JudgeModule
from .fusion import ScoreFusion
from .regeneration import ResponseRegenerator
from .pipeline import VerificationPipeline

__all__ = [
    "settings",
    "Settings",
    "calculate_risk_level",
    "safe_json_parse",
    "LLMProvider",
    "get_llm_provider",
    "SearchProvider",
    "get_search_provider",
    "EmbeddingModel",
    "get_embedding_model",
    "BlackBoxDetector",
    "WhiteBoxDetector",
    "GroundingModule",
    "JudgeModule",
    "ScoreFusion",
    "ResponseRegenerator",
    "VerificationPipeline",
]
