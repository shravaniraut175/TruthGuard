# TruthGuard Black-Box Detector Module
"""Black-box consistency detector using semantic similarity."""

from typing import Optional
from dataclasses import dataclass

from .config import settings
from .llm import get_llm_provider
from .embeddings import get_embedding_model


@dataclass
class BlackBoxResult:
    """Result from black-box consistency detection."""
    score: float  # 0.0 to 1.0, higher means more consistent
    samples: list[str]  # Generated samples for comparison
    similarities: list[float]  # Similarity scores for each sample
    mean_similarity: float
    std_similarity: float
    explanation: str


class BlackBoxDetector:
    """
    Black-box consistency detector.

    Generates multiple samples from the base model at different temperatures
    and measures semantic similarity between the original response and samples.
    """

    def __init__(self):
        self.num_samples = settings.NUM_BLACKBOX_SAMPLES
        self.temperatures = [0.3, 0.7, 1.0][:self.num_samples]  # Vary temperatures
        self._embedding_model = None

    def _get_embedding_model(self):
        """Lazy load embedding model."""
        if self._embedding_model is None:
            self._embedding_model = get_embedding_model()
        return self._embedding_model

    def detect(
        self,
        prompt: str,
        response: str,
        provider: str,
        model_name: str
    ) -> BlackBoxResult:
        """
        Detect hallucination using black-box consistency.

        Args:
            prompt: User prompt
            response: LLM response to verify
            provider: LLM provider name
            model_name: Model name

        Returns:
            BlackBoxResult with consistency score and details
        """
        try:
            llm = get_llm_provider(provider, model_name)
        except Exception as e:
            return BlackBoxResult(
                score=0.5,
                samples=[],
                similarities=[],
                mean_similarity=0.5,
                std_similarity=0.0,
                explanation=f"Failed to initialize LLM provider: {str(e)}"
            )

        # Generate samples at different temperatures
        samples = []
        for temp in self.temperatures[:self.num_samples]:
            try:
                sample = llm.generate(prompt, temperature=temp)
                if sample.strip():
                    samples.append(sample.strip())
            except Exception as e:
                # Skip failed generations
                print(f"Sample generation failed at temperature {temp}: {e}")
                continue

        if not samples:
            return BlackBoxResult(
                score=0.5,
                samples=[],
                similarities=[],
                mean_similarity=0.5,
                std_similarity=0.0,
                explanation="Failed to generate any samples for consistency check"
            )

        # Calculate semantic similarities
        try:
            embedding_model = self._get_embedding_model()
            similarities = embedding_model.batch_similarity(response, samples)
        except Exception as e:
            # Fallback to simple string matching
            similarities = self._fallback_similarity(response, samples)

        # Calculate statistics
        mean_sim = sum(similarities) / len(similarities) if similarities else 0.5
        
        if len(similarities) > 1:
            variance = sum((s - mean_sim) ** 2 for s in similarities) / len(similarities)
            std_sim = variance ** 0.5
        else:
            std_sim = 0.0

        # Score is the mean similarity (higher = more consistent = less likely hallucinated)
        score = mean_sim

        # Generate explanation
        explanation = self._generate_explanation(score, mean_sim, std_sim, len(samples))

        return BlackBoxResult(
            score=score,
            samples=samples,
            similarities=similarities,
            mean_similarity=mean_sim,
            std_similarity=std_sim,
            explanation=explanation
        )

    def _fallback_similarity(self, reference: str, candidates: list[str]) -> list[float]:
        """
        Fallback similarity calculation using simple string matching.

        Args:
            reference: Reference text
            candidates: List of candidate texts

        Returns:
            List of similarity scores
        """
        similarities = []
        ref_lower = reference.lower()

        for candidate in candidates:
            cand_lower = candidate.lower()

            # Simple word overlap ratio
            ref_words = set(ref_lower.split())
            cand_words = set(cand_lower.split())

            if not ref_words or not cand_words:
                similarities.append(0.5)
            else:
                intersection = len(ref_words & cand_words)
                union = len(ref_words | cand_words)
                jaccard = intersection / union if union > 0 else 0.0
                # Scale to 0.5-1.0 range for fallback
                similarities.append(0.5 + 0.5 * jaccard)

        return similarities

    def _generate_explanation(
        self,
        score: float,
        mean_sim: float,
        std_sim: float,
        num_samples: int
    ) -> str:
        """Generate human-readable explanation."""
        if score >= 0.8:
            consistency_level = "highly consistent"
        elif score >= 0.6:
            consistency_level = "moderately consistent"
        elif score >= 0.4:
            consistency_level = "somewhat inconsistent"
        else:
            consistency_level = "highly inconsistent"

        explanation = (
            f"The response is {consistency_level} across {num_samples} generated samples. "
            f"Mean semantic similarity: {mean_sim:.2f}"
        )

        if std_sim > 0.15:
            explanation += (
                f" with high variance ({std_sim:.2f}), indicating unstable model behavior."
            )
        else:
            explanation += f" with low variance ({std_sim:.2f})."

        return explanation
