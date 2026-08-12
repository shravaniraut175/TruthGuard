# TruthGuard Pipeline Module
"""Main verification pipeline orchestrating all modules."""

from typing import Optional
from dataclasses import dataclass, asdict

from .config import settings
from .blackbox import BlackBoxDetector, BlackBoxResult
from .whitebox import WhiteBoxDetector, WhiteBoxResult
from .grounding import GroundingModule, GroundingResult
from .judge import JudgeModule, JudgeResult
from .fusion import ScoreFusion, FusionResult
from .regeneration import ResponseRegenerator, RegenerationResult


@dataclass
class VerificationResult:
    """Complete verification result from the pipeline."""
    # Input
    prompt: str
    response: str

    # Core metrics
    truth_score: float
    confidence_score: float
    hallucination_probability: float
    risk_level: str

    # Explanations
    explanation: str
    grounding_explanation: str

    # Module scores
    module_scores: dict[str, Optional[float]]

    # Evidence
    evidence: list[dict]
    sources: list[dict]

    # Regeneration
    regenerated_response: Optional[str]
    regeneration_triggered: bool
    regeneration_explanation: Optional[str]

    # Veto information
    veto_applied: bool
    veto_reason: Optional[str]

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


class VerificationPipeline:
    """
    Main verification pipeline.

    Orchestrates all detection modules and combines their results
    through score fusion.
    """

    def __init__(self):
        self.blackbox_detector = BlackBoxDetector()
        self.whitebox_detector = WhiteBoxDetector()
        self.grounding_module = GroundingModule()
        self.judge_module = JudgeModule()
        self.score_fusion = ScoreFusion()
        self.regenerator = ResponseRegenerator()

    def verify(
        self,
        prompt: str,
        response: str,
        regenerate: bool = False
    ) -> VerificationResult:
        """
        Run the complete verification pipeline.

        Args:
            prompt: User prompt
            response: LLM response to verify
            regenerate: Whether to regenerate if hallucination probability is high

        Returns:
            VerificationResult with all metrics and explanations
        """
        # Run black-box detector
        blackbox_result = self.blackbox_detector.detect(
            prompt=prompt,
            response=response,
            provider=settings.BASE_PROVIDER,
            model_name=settings.BASE_MODEL
        )

        # Run white-box detector (may return unavailable)
        whitebox_result = self.whitebox_detector.detect(
            prompt=prompt,
            response=response
        )

        # Run grounding module
        grounding_result = self.grounding_module.verify(
            prompt=prompt,
            response=response
        )

        # Run judge module (with evidence from grounding)
        judge_result = self.judge_module.evaluate(
            prompt=prompt,
            response=response,
            evidence=grounding_result.evidence if grounding_result else None
        )

        # Fuse scores
        fusion_result = self.score_fusion.fuse(
            blackbox_result=blackbox_result,
            whitebox_result=whitebox_result if whitebox_result.available else None,
            judge_result=judge_result,
            grounding_result=grounding_result
        )

        # Handle regeneration
        regeneration_result: Optional[RegenerationResult] = None
        if regenerate and fusion_result.hallucination_probability >= settings.HALLUCINATION_THRESHOLD:
            regeneration_result = self.regenerator.regenerate(
                prompt=prompt,
                original_response=response,
                evidence=grounding_result.evidence if grounding_result else [],
                hallucination_probability=fusion_result.hallucination_probability,
                provider=settings.BASE_PROVIDER,
                model_name=settings.BASE_MODEL
            )

        # Build final result
        return VerificationResult(
            prompt=prompt,
            response=response,
            truth_score=fusion_result.truth_score,
            confidence_score=fusion_result.confidence_score,
            hallucination_probability=fusion_result.hallucination_probability,
            risk_level=fusion_result.risk_level,
            explanation=fusion_result.explanation,
            grounding_explanation=fusion_result.grounding_explanation,
            module_scores=fusion_result.module_scores,
            evidence=grounding_result.evidence if grounding_result else [],
            sources=grounding_result.sources if grounding_result else [],
            regenerated_response=regeneration_result.regenerated_response if regeneration_result else None,
            regeneration_triggered=regeneration_result.regeneration_triggered if regeneration_result else False,
            regeneration_explanation=regeneration_result.explanation if regeneration_result else None,
            veto_applied=fusion_result.veto_applied,
            veto_reason=fusion_result.veto_reason
        )

    def generate_and_verify(
        self,
        prompt: str,
        regenerate: bool = False
    ) -> tuple[str, VerificationResult]:
        """
        Generate a response and verify it.

        Args:
            prompt: User prompt
            regenerate: Whether to regenerate if hallucination probability is high

        Returns:
            Tuple of (generated_response, VerificationResult)
        """
        from .llm import get_llm_provider

        # Generate response using base model
        try:
            llm = get_llm_provider(settings.BASE_PROVIDER, settings.BASE_MODEL)
            generated_response = llm.generate(prompt, temperature=0.7)
        except Exception as e:
            # Return error as response
            generated_response = f"Error generating response: {str(e)}"

        # Verify the generated response
        verification_result = self.verify(
            prompt=prompt,
            response=generated_response,
            regenerate=regenerate
        )

        return generated_response, verification_result
