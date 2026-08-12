# TruthGuard Fusion Module
"""Score fusion logic with veto mechanisms."""

from typing import Optional
from dataclasses import dataclass

from .config import settings
from .blackbox import BlackBoxResult
from .whitebox import WhiteBoxResult
from .judge import JudgeResult
from .grounding import GroundingResult


@dataclass
class FusionResult:
    """Result from score fusion."""
    truth_score: float  # 0.0 to 1.0, higher means more truthful
    confidence_score: float  # 0.0 to 1.0, how confident we are in the truth score
    hallucination_probability: float  # 1 - truth_score
    risk_level: str  # low, medium, high, critical
    explanation: str
    grounding_explanation: str
    module_scores: dict[str, Optional[float]]  # Individual module scores
    veto_applied: bool  # Whether any veto was applied
    veto_reason: Optional[str]  # Reason for veto if applied


class ScoreFusion:
    """
    Score fusion module.

    Combines black-box, white-box, judge, and grounding scores with
    weighted averaging and applies veto mechanisms.
    """

    def __init__(self):
        self.weights = settings.get_normalized_weights(whitebox_available=True)
        self.hallucination_threshold = settings.HALLUCINATION_THRESHOLD

    def fuse(
        self,
        blackbox_result: Optional[BlackBoxResult],
        whitebox_result: Optional[WhiteBoxResult],
        judge_result: Optional[JudgeResult],
        grounding_result: Optional[GroundingResult]
    ) -> FusionResult:
        """
        Fuse scores from multiple detectors.

        Args:
            blackbox_result: Result from black-box detector (or None)
            whitebox_result: Result from white-box detector (or None)
            judge_result: Result from judge module (or None)
            grounding_result: Result from grounding module (or None)

        Returns:
            FusionResult with combined scores and explanations
        """
        # Collect available scores
        scores = {}
        explanations = {}

        if blackbox_result:
            scores["blackbox"] = blackbox_result.score
            explanations["blackbox"] = blackbox_result.explanation
        else:
            scores["blackbox"] = None
            explanations["blackbox"] = "Not available"

        if whitebox_result and whitebox_result.available:
            scores["whitebox"] = whitebox_result.score
            explanations["whitebox"] = whitebox_result.explanation
        else:
            scores["whitebox"] = None
            explanations["whitebox"] = "Disabled or unavailable"

        if judge_result:
            scores["judge"] = judge_result.overall_score
            explanations["judge"] = judge_result.explanation
        else:
            scores["judge"] = None
            explanations["judge"] = "Not available"

        if grounding_result:
            scores["grounding"] = grounding_result.score
            explanations["grounding"] = grounding_result.explanation
        else:
            scores["grounding"] = None
            explanations["grounding"] = "Not available"

        # Recalculate weights based on available modules
        available_weights = self._normalize_weights(scores)

        # Calculate weighted average
        weighted_sum = 0.0
        total_weight = 0.0

        for module, score in scores.items():
            if score is not None:
                weight = available_weights.get(module, 0.0)
                weighted_sum += score * weight
                total_weight += weight

        base_truth_score = weighted_sum / total_weight if total_weight > 0 else 0.5

        # Apply veto mechanisms
        final_truth_score, veto_applied, veto_reason = self._apply_vetos(
            base_truth_score,
            judge_result,
            grounding_result
        )

        # Calculate confidence score (based on agreement between modules and evidence strength)
        confidence_score = self._calculate_confidence(
            scores,
            grounding_result
        )

        # Calculate hallucination probability
        hallucination_probability = 1.0 - final_truth_score

        # Determine risk level
        risk_level = self._calculate_risk_level(hallucination_probability)

        # Generate overall explanation
        explanation = self._generate_explanation(
            final_truth_score,
            scores,
            veto_applied,
            veto_reason
        )

        grounding_explanation = ""
        if grounding_result:
            grounding_explanation = (
                f"External grounding: {grounding_result.explanation} "
                f"Status: {'supported' if grounding_result.supported else 'contradicted' if grounding_result.contradicted else 'insufficient'}."
            )

        return FusionResult(
            truth_score=final_truth_score,
            confidence_score=confidence_score,
            hallucination_probability=hallucination_probability,
            risk_level=risk_level,
            explanation=explanation,
            grounding_explanation=grounding_explanation,
            module_scores=scores,
            veto_applied=veto_applied,
            veto_reason=veto_reason
        )

    def _normalize_weights(self, scores: dict[str, Optional[float]]) -> dict[str, float]:
        """Normalize weights based on available modules."""
        original_weights = settings.get_normalized_weights(whitebox_available=True)
        
        available_weight_sum = sum(
            original_weights.get(k, 0.0)
            for k, v in scores.items()
            if v is not None
        )

        if available_weight_sum == 0:
            # All modules unavailable, use equal weights
            available_modules = [k for k, v in scores.items() if v is not None]
            if available_modules:
                equal_weight = 1.0 / len(available_modules)
                return {k: equal_weight for k in scores.keys()}
            return {k: 0.25 for k in scores.keys()}

        normalized = {}
        for module in scores.keys():
            if scores[module] is not None:
                normalized[module] = original_weights.get(module, 0.0) / available_weight_sum
            else:
                normalized[module] = 0.0

        return normalized

    def _apply_vetos(
        self,
        base_score: float,
        judge_result: Optional[JudgeResult],
        grounding_result: Optional[GroundingResult]
    ) -> tuple[float, bool, Optional[str]]:
        """
        Apply veto mechanisms to reduce truth score.

        Args:
            base_score: Base truth score from weighted fusion
            judge_result: Judge result
            grounding_result: Grounding result

        Returns:
            Tuple of (adjusted_score, veto_applied, veto_reason)
        """
        final_score = base_score
        veto_applied = False
        veto_reason = None

        # External contradiction veto
        if grounding_result and grounding_result.contradicted:
            if grounding_result.score < 0.35:
                # Strong contradiction - apply strong penalty
                reduction = 0.4 * (1.0 - grounding_result.score)
                final_score = max(0.0, final_score - reduction)
                veto_applied = True
                veto_reason = (
                    f"External evidence strongly contradicts the response "
                    f"(grounding score: {grounding_result.score:.2f}). "
                    f"Truth score reduced by {reduction:.2f}."
                )

        # Judge factual accuracy veto
        if judge_result and judge_result.factual_accuracy < 0.20:
            # Very low factual accuracy - apply penalty
            reduction = 0.35 * (1.0 - judge_result.factual_accuracy * 5)
            final_score = max(0.0, final_score - reduction)
            veto_applied = True
            reason_addition = (
                f"Judge model rated factual accuracy very low "
                f"({judge_result.factual_accuracy:.2f}). "
                f"Truth score reduced by {reduction:.2f}."
            )
            if veto_reason:
                veto_reason += " " + reason_addition
            else:
                veto_reason = reason_addition

        return final_score, veto_applied, veto_reason

    def _calculate_confidence(
        self,
        scores: dict[str, Optional[float]],
        grounding_result: Optional[GroundingResult]
    ) -> float:
        """
        Calculate confidence score based on module agreement and evidence.

        Args:
            scores: Dictionary of module scores
            grounding_result: Grounding result

        Returns:
            Confidence score from 0.0 to 1.0
        """
        available_scores = [s for s in scores.values() if s is not None]

        if len(available_scores) < 2:
            # Not enough modules to assess agreement
            base_confidence = 0.5
        else:
            # Calculate standard deviation as measure of disagreement
            mean_score = sum(available_scores) / len(available_scores)
            variance = sum((s - mean_score) ** 2 for s in available_scores) / len(available_scores)
            std_dev = variance ** 0.5

            # Lower std_dev = higher confidence
            base_confidence = max(0.3, 1.0 - std_dev)

        # Boost confidence if external evidence supports
        if grounding_result and grounding_result.supported:
            base_confidence = min(1.0, base_confidence + 0.15)
        elif grounding_result and grounding_result.contradicted:
            base_confidence = max(0.2, base_confidence - 0.2)

        # Boost confidence if we have more modules available
        num_modules = len(available_scores)
        if num_modules >= 3:
            base_confidence = min(1.0, base_confidence + 0.1)

        return base_confidence

    def _calculate_risk_level(self, hallucination_probability: float) -> str:
        """Calculate risk level from hallucination probability."""
        if hallucination_probability < 0.30:
            return "low"
        elif hallucination_probability < 0.50:
            return "medium"
        elif hallucination_probability < 0.70:
            return "high"
        else:
            return "critical"

    def _generate_explanation(
        self,
        truth_score: float,
        scores: dict[str, Optional[float]],
        veto_applied: bool,
        veto_reason: Optional[str]
    ) -> str:
        """Generate human-readable explanation."""
        if truth_score >= 0.8:
            quality = "highly likely to be accurate"
        elif truth_score >= 0.6:
            quality = "likely accurate"
        elif truth_score >= 0.4:
            quality = "potentially unreliable"
        else:
            quality = "likely hallucinated or inaccurate"

        explanation = f"The response is {quality} (truth score: {truth_score:.2f})."

        if veto_applied and veto_reason:
            explanation += f" {veto_reason}"

        return explanation
