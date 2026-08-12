# TruthGuard Judge Module
"""LLM-as-a-Judge evaluation module."""

from typing import Optional
from dataclasses import dataclass

from .config import settings
from .llm import get_llm_provider
from .utils import safe_json_parse


@dataclass
class JudgeResult:
    """Result from LLM-as-a-Judge evaluation."""
    factual_accuracy: float  # 0.0 to 1.0
    grounding: float  # 0.0 to 1.0
    coherence: float  # 0.0 to 1.0
    overall_score: float  # 0.0 to 1.0
    explanation: str
    raw_response: str


class JudgeModule:
    """
    LLM-as-a-Judge module.

    Uses a configurable judge model (can be from a different provider than base)
    to evaluate factual accuracy, grounding, coherence, and provide explanations.
    """

    def __init__(self):
        self.judge_provider = settings.JUDGE_PROVIDER
        self.judge_model = settings.JUDGE_MODEL
        self._llm = None
        self._initialization_error: Optional[str] = None

    def _ensure_initialized(self) -> None:
        """Lazy initialization of the judge LLM."""
        if self._llm is not None:
            return

        try:
            self._llm = get_llm_provider(self.judge_provider, self.judge_model)
        except Exception as e:
            self._initialization_error = str(e)

    def evaluate(
        self,
        prompt: str,
        response: str,
        evidence: Optional[list[dict]] = None
    ) -> JudgeResult:
        """
        Evaluate a response using LLM-as-a-Judge.

        Args:
            prompt: User prompt
            response: LLM response to evaluate
            evidence: Optional list of evidence dictionaries from search

        Returns:
            JudgeResult with scores and explanation
        """
        self._ensure_initialized()

        if self._initialization_error:
            return JudgeResult(
                factual_accuracy=0.5,
                grounding=0.5,
                coherence=0.5,
                overall_score=0.5,
                explanation=f"Judge model unavailable: {self._initialization_error}",
                raw_response=""
            )

        # Build evaluation prompt
        eval_prompt = self._build_eval_prompt(prompt, response, evidence)

        try:
            raw_response = self._llm.generate_json(eval_prompt, temperature=0.3)
            return self._parse_judge_response(raw_response)
        except Exception as e:
            return JudgeResult(
                factual_accuracy=0.5,
                grounding=0.5,
                coherence=0.5,
                overall_score=0.5,
                explanation=f"Judge evaluation failed: {str(e)}. Using fallback scores.",
                raw_response=""
            )

    def _build_eval_prompt(
        self,
        prompt: str,
        response: str,
        evidence: Optional[list[dict]] = None
    ) -> str:
        """Build the evaluation prompt for the judge model."""
        
        evidence_context = ""
        if evidence:
            evidence_str = "\n".join([
                f"- {e.get('snippet', '')[:200]} (Source: {e.get('title', 'Unknown')})"
                for e in evidence[:5]
            ])
            evidence_context = f"\n\nAvailable Evidence:\n{evidence_str}"

        eval_prompt = f"""You are an expert fact-checker evaluating an AI-generated response.

User Question: {prompt}

AI Response: {response}
{evidence_context}

Evaluate the response on these criteria:
1. Factual Accuracy: Are the claims in the response factually correct?
2. Grounding: Is the response well-grounded in verifiable information?
3. Coherence: Is the response logically consistent and well-structured?

Respond with ONLY a valid JSON object in this exact format:
{{
    "factual_accuracy": <float 0.0-1.0>,
    "grounding": <float 0.0-1.0>,
    "coherence": <float 0.0-1.0>,
    "explanation": "<brief explanation of your evaluation>"
}}

Scoring guidelines:
- 0.9-1.0: Excellent, highly reliable
- 0.7-0.9: Good, mostly accurate
- 0.5-0.7: Fair, some concerns
- 0.3-0.5: Poor, significant issues
- 0.0-0.3: Very poor, likely hallucinated

Be strict about factual accuracy. If claims cannot be verified or contradict known facts, score lower."""

        return eval_prompt

    def _parse_judge_response(self, raw_response: dict) -> JudgeResult:
        """Parse the judge model's JSON response."""
        
        # Extract values with defaults
        factual_accuracy = float(raw_response.get("factual_accuracy", 0.5))
        grounding = float(raw_response.get("grounding", 0.5))
        coherence = float(raw_response.get("coherence", 0.5))
        explanation = str(raw_response.get("explanation", "No explanation provided."))

        # Clamp values to 0-1 range
        factual_accuracy = max(0.0, min(1.0, factual_accuracy))
        grounding = max(0.0, min(1.0, grounding))
        coherence = max(0.0, min(1.0, coherence))

        # Calculate overall score (weighted average)
        overall_score = (
            factual_accuracy * 0.5 +
            grounding * 0.3 +
            coherence * 0.2
        )

        return JudgeResult(
            factual_accuracy=factual_accuracy,
            grounding=grounding,
            coherence=coherence,
            overall_score=overall_score,
            explanation=explanation,
            raw_response=str(raw_response)
        )
