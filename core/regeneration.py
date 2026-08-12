# TruthGuard Regeneration Module
"""Response regeneration for safer answers."""

from typing import Optional
from dataclasses import dataclass

from .config import settings
from .llm import get_llm_provider


@dataclass
class RegenerationResult:
    """Result from response regeneration."""
    regenerated_response: str
    explanation: str
    original_response: str
    regeneration_triggered: bool


class ResponseRegenerator:
    """
    Response regeneration module.

    Generates a safer response when hallucination probability is high.
    The regenerated response acknowledges uncertainty and cites available evidence.
    """

    def __init__(self):
        self.threshold = settings.HALLUCINATION_THRESHOLD
        self._llm = None
        self._initialization_error: Optional[str] = None

    def _ensure_initialized(self, provider: str, model_name: str) -> None:
        """Lazy initialization of the LLM for regeneration."""
        if self._llm is not None:
            return

        try:
            self._llm = get_llm_provider(provider, model_name)
        except Exception as e:
            self._initialization_error = str(e)

    def regenerate(
        self,
        prompt: str,
        original_response: str,
        evidence: list[dict],
        hallucination_probability: float,
        provider: str,
        model_name: str
    ) -> RegenerationResult:
        """
        Regenerate a safer response if hallucination probability is high.

        Args:
            prompt: User prompt
            original_response: Original LLM response
            evidence: List of evidence dictionaries from grounding
            hallucination_probability: Current hallucination probability
            provider: LLM provider name
            model_name: Model name

        Returns:
            RegenerationResult with new response or original
        """
        # Check if regeneration is needed
        if hallucination_probability < self.threshold:
            return RegenerationResult(
                regenerated_response=original_response,
                explanation="Hallucination probability below threshold. No regeneration needed.",
                original_response=original_response,
                regeneration_triggered=False
            )

        self._ensure_initialized(provider, model_name)

        if self._initialization_error:
            return RegenerationResult(
                regenerated_response=original_response,
                explanation=f"Cannot regenerate: {self._initialization_error}",
                original_response=original_response,
                regeneration_triggered=True
            )

        # Build regeneration prompt
        regen_prompt = self._build_regeneration_prompt(
            prompt, original_response, evidence, hallucination_probability
        )

        try:
            new_response = self._llm.generate(regen_prompt, temperature=0.5)
            
            explanation = (
                f"Response regenerated due to high hallucination probability "
                f"({hallucination_probability:.2f} >= {self.threshold:.2f}). "
                f"The new response acknowledges uncertainty and relies on verified information."
            )

            return RegenerationResult(
                regenerated_response=new_response.strip(),
                explanation=explanation,
                original_response=original_response,
                regeneration_triggered=True
            )

        except Exception as e:
            return RegenerationResult(
                regenerated_response=original_response,
                explanation=f"Regeneration failed: {str(e)}. Returning original response.",
                original_response=original_response,
                regeneration_triggered=True
            )

    def _build_regeneration_prompt(
        self,
        prompt: str,
        original_response: str,
        evidence: list[dict],
        hallucination_probability: float
    ) -> str:
        """Build the prompt for regenerating a safer response."""

        evidence_context = ""
        if evidence:
            evidence_items = []
            for e in evidence[:5]:
                snippet = e.get("snippet", "")[:300]
                title = e.get("title", "Unknown source")
                evidence_items.append(f"- From '{title}': {snippet}")
            evidence_context = "\n\nVerified Information from External Sources:\n" + "\n".join(evidence_items)
        else:
            evidence_context = "\n\nNote: No external verification was possible."

        regen_prompt = f"""You need to provide a safer, more careful response to a question because your previous answer may contain inaccurate or unverified information.

Original Question: {prompt}

Previous AI Response (may contain inaccuracies):
{original_response}

Hallucination Risk Score: {hallucination_probability:.1%} (high risk)
{evidence_context}

Please generate a NEW response that:
1. Acknowledges uncertainty where appropriate
2. Only states information that can be verified or is well-established
3. Clearly distinguishes between facts and speculation
4. If evidence is insufficient, explicitly say "This cannot be verified with available sources"
5. Cites the available evidence where relevant
6. Avoids making specific claims that cannot be supported

Your response should be helpful but cautious. It's better to acknowledge uncertainty than to potentially mislead the user."""

        return regen_prompt
