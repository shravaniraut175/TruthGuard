# TruthGuard API Module
"""FastAPI application for TruthGuard."""

from .main import app
from .schemas import (
    VerifyRequest,
    GenerateAndVerifyRequest,
    VerificationResponse,
    HealthResponse,
    WelcomeResponse
)

__all__ = [
    "app",
    "VerifyRequest",
    "GenerateAndVerifyRequest",
    "VerificationResponse",
    "HealthResponse",
    "WelcomeResponse"
]
