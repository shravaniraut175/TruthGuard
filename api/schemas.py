# TruthGuard API Schemas
"""Pydantic schemas for API requests and responses."""

from typing import Optional, Any
from pydantic import BaseModel, Field


class VerifyRequest(BaseModel):
    """Request schema for /verify endpoint."""
    prompt: str = Field(..., description="User prompt")
    response: str = Field(..., description="LLM response to verify")
    regenerate: bool = Field(default=False, description="Whether to regenerate if hallucination probability is high")


class GenerateAndVerifyRequest(BaseModel):
    """Request schema for /generate-and-verify endpoint."""
    prompt: str = Field(..., description="User prompt")
    regenerate: bool = Field(default=False, description="Whether to regenerate if hallucination probability is high")


class ModuleScores(BaseModel):
    """Schema for individual module scores."""
    blackbox: Optional[float] = Field(None, description="Black-box consistency score")
    whitebox: Optional[float] = Field(None, description="White-box token confidence score")
    judge: Optional[float] = Field(None, description="Judge model overall score")
    grounding: Optional[float] = Field(None, description="External grounding score")


class EvidenceItem(BaseModel):
    """Schema for evidence item."""
    title: str = Field(..., description="Source title")
    url: str = Field(..., description="Source URL")
    snippet: str = Field(..., description="Evidence snippet")
    source: str = Field(default="", description="Source provider name")


class SourceItem(BaseModel):
    """Schema for source reference."""
    title: str = Field(..., description="Source title")
    url: str = Field(..., description="Source URL")


class VerificationResponse(BaseModel):
    """Response schema for verification endpoints."""
    # Input echo
    prompt: str = Field(..., description="Original prompt")
    response: str = Field(..., description="Verified response")

    # Core metrics
    truth_score: float = Field(..., ge=0.0, le=1.0, description="Truth score (0-1)")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0-1)")
    hallucination_probability: float = Field(..., ge=0.0, le=1.0, description="Hallucination probability (0-1)")
    risk_level: str = Field(..., description="Risk level: low, medium, high, or critical")

    # Explanations
    explanation: str = Field(..., description="Overall explanation")
    grounding_explanation: str = Field(default="", description="Grounding-specific explanation")

    # Module scores
    module_scores: ModuleScores = Field(..., description="Individual module scores")

    # Evidence
    evidence: list[dict] = Field(default_factory=list, description="Evidence snippets")
    sources: list[dict] = Field(default_factory=list, description="Source references")

    # Regeneration
    regenerated_response: Optional[str] = Field(None, description="Regenerated safer response")
    regeneration_triggered: bool = Field(default=False, description="Whether regeneration was triggered")
    regeneration_explanation: Optional[str] = Field(None, description="Explanation for regeneration")

    # Veto information
    veto_applied: bool = Field(default=False, description="Whether any veto was applied")
    veto_reason: Optional[str] = Field(None, description="Reason for veto if applied")

    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "What is the capital of France?",
                "response": "The capital of France is Paris.",
                "truth_score": 0.95,
                "confidence_score": 0.92,
                "hallucination_probability": 0.05,
                "risk_level": "low",
                "explanation": "The response is highly likely to be accurate (truth score: 0.95).",
                "grounding_explanation": "External grounding: Evidence supports the claim. Status: supported.",
                "module_scores": {
                    "blackbox": 0.98,
                    "whitebox": None,
                    "judge": 0.95,
                    "grounding": 0.92
                },
                "evidence": [],
                "sources": [],
                "regenerated_response": None,
                "regeneration_triggered": False,
                "veto_applied": False,
                "veto_reason": None
            }
        }


class GenerateAndVerifyResponse(VerificationResponse):
    """Response schema for /generate-and-verify endpoint (extends VerificationResponse)."""
    generated_response: str = Field(..., description="The generated response before verification")


class HealthResponse(BaseModel):
    """Response schema for /health endpoint."""
    status: str = Field(..., description="Health status")
    version: str = Field(..., description="API version")
    config: dict = Field(default_factory=dict, description="Current configuration summary")


class WelcomeResponse(BaseModel):
    """Response schema for / endpoint."""
    message: str = Field(..., description="Welcome message")
    version: str = Field(..., description="API version")
    endpoints: dict = Field(..., description="Available endpoints")
