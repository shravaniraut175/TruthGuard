# TruthGuard Configuration Module
"""Configuration management for TruthGuard."""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Keys
    OPENROUTER_API_KEY: str = Field(default="", description="OpenRouter API key")
    GOOGLE_API_KEY: str = Field(default="", description="Google API key for Gemini")
    OPENAI_API_KEY: str = Field(default="", description="OpenAI API key")

    # Base Model Configuration
    BASE_PROVIDER: str = Field(
        default="openrouter",
        description="Provider for base model (openrouter, google, openai)"
    )
    BASE_MODEL: str = Field(
        default="qwen/qwen2.5-72b-instruct",
        description="Model name for base generation"
    )

    # Judge Model Configuration
    JUDGE_PROVIDER: str = Field(
        default="openrouter",
        description="Provider for judge model (openrouter, google, openai)"
    )
    JUDGE_MODEL: str = Field(
        default="anthropic/claude-3.5-sonnet",
        description="Model name for judging"
    )

    # Search Configuration
    SEARCH_PROVIDER: str = Field(
        default="duckduckgo",
        description="Search provider (duckduckgo)"
    )
    MAX_SEARCH_RESULTS: int = Field(
        default=5,
        description="Maximum number of search results"
    )
    NUM_BLACKBOX_SAMPLES: int = Field(
        default=3,
        description="Number of samples for black-box consistency check"
    )

    # White-box Configuration
    WHITEBOX_ENABLED: bool = Field(
        default=False,
        description="Enable white-box token confidence scoring"
    )
    WHITEBOX_MODEL: str = Field(
        default="Qwen/Qwen2.5-7B-Instruct",
        description="Hugging Face model for white-box scoring"
    )

    # Thresholds
    HALLUCINATION_THRESHOLD: float = Field(
        default=0.60,
        description="Threshold for triggering regeneration"
    )

    # Score Weights
    BLACKBOX_WEIGHT: float = Field(default=0.20, description="Black-box score weight")
    WHITEBOX_WEIGHT: float = Field(default=0.10, description="White-box score weight")
    JUDGE_WEIGHT: float = Field(default=0.35, description="Judge score weight")
    GROUNDING_WEIGHT: float = Field(default=0.35, description="Grounding score weight")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"

    def validate_api_keys(self) -> list[str]:
        """Validate that required API keys are present."""
        missing_keys = []

        if self.BASE_PROVIDER == "openrouter" and not self.OPENROUTER_API_KEY:
            missing_keys.append("OPENROUTER_API_KEY")
        elif self.BASE_PROVIDER == "google" and not self.GOOGLE_API_KEY:
            missing_keys.append("GOOGLE_API_KEY")
        elif self.BASE_PROVIDER == "openai" and not self.OPENAI_API_KEY:
            missing_keys.append("OPENAI_API_KEY")

        if self.JUDGE_PROVIDER == "openrouter" and not self.OPENROUTER_API_KEY:
            if "OPENROUTER_API_KEY" not in missing_keys:
                missing_keys.append("OPENROUTER_API_KEY")
        elif self.JUDGE_PROVIDER == "google" and not self.GOOGLE_API_KEY:
            if "GOOGLE_API_KEY" not in missing_keys:
                missing_keys.append("GOOGLE_API_KEY")
        elif self.JUDGE_PROVIDER == "openai" and not self.OPENAI_API_KEY:
            if "OPENAI_API_KEY" not in missing_keys:
                missing_keys.append("OPENAI_API_KEY")

        return missing_keys

    def get_normalized_weights(self, whitebox_available: bool = True) -> dict[str, float]:
        """Get normalized weights based on available modules."""
        weights = {
            "blackbox": self.BLACKBOX_WEIGHT,
            "whitebox": self.WHITEBOX_WEIGHT if whitebox_available else 0.0,
            "judge": self.JUDGE_WEIGHT,
            "grounding": self.GROUNDING_WEIGHT,
        }

        total = sum(weights.values())
        if total > 0:
            weights = {k: v / total for k, v in weights.items()}

        return weights


# Global settings instance
settings = Settings()
