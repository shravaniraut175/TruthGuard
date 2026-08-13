# TruthGuard Pipeline Module

"""Main verification pipeline orchestrating all modules."""

from typing import Callable, Optional
from dataclasses import dataclass, asdict

from .config import settings
from .blackbox import BlackBoxDetector
from .grounding import GroundingModule
from .judge import JudgeModule
from .fusion import ScoreFusion
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
    Main TruthGuard verification pipeline.

    Orchestrates all detection modules and combines their results
    through score fusion.
    """

    def __init__(self):
        self.blackbox_detector = BlackBoxDetector()
        self.whitebox_detector = None
        self.grounding_module = GroundingModule()
        self.judge_module = JudgeModule()
        self.score_fusion = ScoreFusion()
        self.regenerator = ResponseRegenerator()

    def _report_progress(
        self,
        progress_callback: Optional[Callable[[str, str, int], None]],
        stage: str,
        message: str,
        progress: int,
    ) -> None:
        """Report pipeline progress if a callback is provided."""
        if progress_callback:
            try:
                progress_callback(stage, message, progress)
            except Exception:
                # Progress reporting must never break the verification pipeline.
                pass

    def verify(
        self,
        prompt: str,
        response: str,
        regenerate: bool = False,
        progress_callback: Optional[
            Callable[[str, str, int], None]
        ] = None,
    ) -> VerificationResult:
        """
        Run the complete verification pipeline.

        Args:
            prompt: User prompt.
            response: LLM response to verify.
            regenerate: Whether to regenerate if hallucination probability is high.
            progress_callback: Optional callback receiving
                (stage, message, progress).

        Returns:
            VerificationResult with all metrics and explanations.
        """

        # -----------------------------------------------------------
        # Stage 1: Black-box consistency
        # -----------------------------------------------------------
        self._report_progress(
            progress_callback,
            "blackbox",
            "Checking response consistency...",
            25,
        )

        blackbox_result = self.blackbox_detector.detect(
            prompt=prompt,
            response=response,
            provider=settings.BASE_PROVIDER,
            model_name=settings.BASE_MODEL,
        )
progress_callback(
    "blackbox",
    "Checking response consistency...",
    25
)

        # -----------------------------------------------------------
        # Stage 2: White-box confidence
        # -----------------------------------------------------------
        if settings.WHITEBOX_ENABLED:
            self._report_progress(
                progress_callback,
                "whitebox",
                "Checking token-level confidence...",
                45,
            )
        else:
            self._report_progress(
                progress_callback,
                "whitebox",
                "White-box analysis disabled.",
                45,
            )

        whitebox_result = None

        self._report_progress(
            progress_callback,
            "whitebox",
            (
                "White-box confidence analysis completed."
                if whitebox_result.available
                else "White-box analysis unavailable."
            ),
            50,
        )

        # -----------------------------------------------------------
        # Stage 3: External grounding
        # -----------------------------------------------------------
        self._report_progress(
            progress_callback,
            "grounding",
            "Searching for external evidence...",
            55,
        )

        grounding_result = self.grounding_module.verify(
            prompt=prompt,
            response=response,
        )

        self._report_progress(
            progress_callback,
            "grounding",
            "External grounding completed.",
            70,
        )

        # -----------------------------------------------------------
        # Stage 4: LLM-as-a-Judge
        # -----------------------------------------------------------
        self._report_progress(
            progress_callback,
            "judge",
            "LLM judge is evaluating factual accuracy...",
            75,
        )

        judge_result = self.judge_module.evaluate(
            prompt=prompt,
            response=response,
            evidence=(
                grounding_result.evidence
                if grounding_result
                else None
            ),
        )

        self._report_progress(
            progress_callback,
            "judge",
            "LLM-as-a-Judge evaluation completed.",
            85,
        )

        # -----------------------------------------------------------
        # Stage 5: Score fusion
        # -----------------------------------------------------------
        self._report_progress(
            progress_callback,
            "fusion",
            "Combining verification scores...",
            90,
        )

        fusion_result = self.score_fusion.fuse(
            blackbox_result=blackbox_result,
            whitebox_result= None,
            judge_result=judge_result,
            grounding_result=grounding_result,
        )

        self._report_progress(
            progress_callback,
            "fusion",
            "Score fusion completed.",
            95,
        )

        # -----------------------------------------------------------
        # Stage 6: Optional regeneration
        # -----------------------------------------------------------
        regeneration_result: Optional[RegenerationResult] = None

        if (
            regenerate
            and fusion_result.hallucination_probability
            >= settings.HALLUCINATION_THRESHOLD
        ):
            self._report_progress(
                progress_callback,
                "regeneration",
                "High hallucination risk detected. Regenerating response...",
                97,
            )

            regeneration_result = self.regenerator.regenerate(
                prompt=prompt,
                original_response=response,
                evidence=(
                    grounding_result.evidence
                    if grounding_result
                    else []
                ),
                hallucination_probability=(
                    fusion_result.hallucination_probability
                ),
                provider=settings.BASE_PROVIDER,
                model_name=settings.BASE_MODEL,
            )

        # -----------------------------------------------------------
        # Stage 7: Complete
        # -----------------------------------------------------------
        self._report_progress(
            progress_callback,
            "complete",
            "TruthGuard verification completed.",
            100,
        )

        # -----------------------------------------------------------
        # Build final result
        # -----------------------------------------------------------
        return VerificationResult(
            prompt=prompt,
            response=response,
            truth_score=fusion_result.truth_score,
            confidence_score=fusion_result.confidence_score,
            hallucination_probability=(
                fusion_result.hallucination_probability
            ),
            risk_level=fusion_result.risk_level,
            explanation=fusion_result.explanation,
            grounding_explanation=fusion_result.grounding_explanation,
            module_scores=fusion_result.module_scores,
            evidence=(
                grounding_result.evidence
                if grounding_result
                else []
            ),
            sources=(
                grounding_result.sources
                if grounding_result
                else []
            ),
            regenerated_response=(
                regeneration_result.regenerated_response
                if regeneration_result
                else None
            ),
            regeneration_triggered=(
                regeneration_result.regeneration_triggered
                if regeneration_result
                else False
            ),
            regeneration_explanation=(
                regeneration_result.explanation
                if regeneration_result
                else None
            ),
            veto_applied=fusion_result.veto_applied,
            veto_reason=fusion_result.veto_reason,
        )

    def generate_and_verify(
        self,
        prompt: str,
        regenerate: bool = False,
        progress_callback: Optional[
            Callable[[str, str, int], None]
        ] = None,
    ) -> tuple[str, VerificationResult]:
        """
        Generate a response and verify it.

        Args:
            prompt: User prompt.
            regenerate: Whether to regenerate if hallucination probability is high.
            progress_callback: Optional callback receiving
                (stage, message, progress).

        Returns:
            Tuple of (generated_response, VerificationResult).
        """

        from .llm import get_llm_provider

        # -----------------------------------------------------------
        # Stage 1: Generate response
        # -----------------------------------------------------------
        self._report_progress(
            progress_callback,
            "generation",
            "Generating response with Gemini...",
            10,
        )

        try:
            llm = get_llm_provider(
                settings.BASE_PROVIDER,
                settings.BASE_MODEL,
            )

            generated_response = llm.generate(
                prompt,
                temperature=0.7,
            )

        except Exception as e:
            generated_response = (
                f"Error generating response: {str(e)}"
            )

        self._report_progress(
            progress_callback,
            "generation",
            "Response generation completed.",
            20,
        )

        # -----------------------------------------------------------
        # Stage 2 onwards: Verify generated response
        # -----------------------------------------------------------
        verification_result = self.verify(
            prompt=prompt,
            response=generated_response,
            regenerate=regenerate,
            progress_callback=progress_callback,
        )

        return generated_response, verification_result