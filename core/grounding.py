# TruthGuard Grounding Module
"""External grounding verification using web search."""

from typing import Optional
from dataclasses import dataclass

from .config import settings
from .search import get_search_provider, SearchResult
from .llm import get_llm_provider


@dataclass
class GroundingResult:
    """Result from external grounding verification."""
    score: float  # 0.0 to 1.0, higher means better grounded
    supported: bool  # Evidence supports the response
    contradicted: bool  # Evidence contradicts the response
    insufficient: bool  # Not enough evidence
    explanation: str
    evidence: list[dict]  # Formatted evidence snippets
    sources: list[dict]  # Source information (title, url)
    search_query: str


class GroundingModule:
    """
    External grounding module.

    Searches the web for evidence related to the prompt and response,
    then uses the judge model to determine if evidence supports,
    contradicts, or is insufficient.
    """

    def __init__(self):
        self.search_provider = get_search_provider(settings.SEARCH_PROVIDER)
        self.max_results = settings.MAX_SEARCH_RESULTS
        self._judge_llm = None
        self._initialization_error: Optional[str] = None

    def _ensure_initialized(self) -> None:
        """Lazy initialization of the judge LLM for evidence evaluation."""
        if self._judge_llm is not None:
            return

        try:
            # Use judge provider for evidence evaluation
            self._judge_llm = get_llm_provider(
                settings.JUDGE_PROVIDER,
                settings.JUDGE_MODEL
            )
        except Exception as e:
            self._initialization_error = str(e)

    def verify(self, prompt: str, response: str) -> GroundingResult:
        """
        Verify response against external evidence.

        Args:
            prompt: User prompt
            response: LLM response to verify

        Returns:
            GroundingResult with score and evidence
        """
        self._ensure_initialized()

        # Generate search query
        search_query = self._generate_search_query(prompt, response)

        # Perform search
        try:
            search_results = self.search_provider.search(
                search_query,
                num_results=self.max_results
            )
        except Exception as e:
            search_results = []

        if not search_results:
            return GroundingResult(
                score=0.5,
                supported=False,
                contradicted=False,
                insufficient=True,
                explanation="No external evidence found. Unable to verify claims.",
                evidence=[],
                sources=[],
                search_query=search_query
            )

        # Format evidence
        evidence = [
            {
                "title": r.title,
                "url": r.url,
                "snippet": r.snippet,
                "source": r.source
            }
            for r in search_results
        ]

        sources = [
            {"title": r.title, "url": r.url}
            for r in search_results
        ]

        # Evaluate evidence against response
        if self._initialization_error:
            # Fallback: simple keyword matching
            result = self._fallback_evaluate(prompt, response, evidence)
        else:
            result = self._evaluate_evidence(prompt, response, evidence)

        return GroundingResult(
            score=result["score"],
            supported=result["supported"],
            contradicted=result["contradicted"],
            insufficient=result["insufficient"],
            explanation=result["explanation"],
            evidence=evidence,
            sources=sources,
            search_query=search_query
        )

    def _generate_search_query(self, prompt: str, response: str) -> str:
        """Generate a concise search query from prompt and response."""
        # Extract key terms from response (first 100 chars, remove common words)
        response_preview = response[:150].split('\n')[0]

        # Simple approach: combine prompt and key response terms
        query = f"{prompt} {response_preview}".strip()

        # Truncate if too long
        if len(query) > 200:
            query = query[:200].rsplit(' ', 1)[0]

        return query

    def _evaluate_evidence(
        self,
        prompt: str,
        response: str,
        evidence: list[dict]
    ) -> dict:
        """Use LLM to evaluate whether evidence supports or contradicts response."""

        evidence_str = "\n\n".join([
            f"Source: {e['title']}\nURL: {e['url']}\nContent: {e['snippet']}"
            for e in evidence[:5]
        ])

        eval_prompt = f"""You are a fact-checker evaluating whether web evidence supports or contradicts an AI response.

User Question: {prompt}

AI Response: {response}

Web Evidence:
{evidence_str}

Determine if the evidence SUPPORTS, CONTRADICTS, or is INSUFFICIENT to verify the response.

Respond with ONLY a valid JSON object:
{{
    "verdict": "supported" | "contradicted" | "insufficient",
    "score": <float 0.0-1.0>,
    "explanation": "<brief explanation>"
}}

Scoring:
- supported: score 0.7-1.0 based on how well evidence confirms the response
- contradicted: score 0.0-0.35 based on how strongly evidence contradicts
- insufficient: score 0.35-0.7 when evidence is ambiguous or incomplete"""

        try:
            raw_response = self._judge_llm.generate_json(eval_prompt, temperature=0.3)

            verdict = str(raw_response.get("verdict", "insufficient")).lower()
            score = float(raw_response.get("score", 0.5))
            explanation = str(raw_response.get("explanation", ""))

            # Clamp score
            score = max(0.0, min(1.0, score))

            supported = verdict == "supported"
            contradicted = verdict == "contradicted"
            insufficient = verdict == "insufficient" or (not supported and not contradicted)

            return {
                "score": score,
                "supported": supported,
                "contradicted": contradicted,
                "insufficient": insufficient,
                "explanation": explanation or "Evidence evaluation completed."
            }

        except Exception as e:
            return self._fallback_evaluate(prompt, response, evidence)

    def _fallback_evaluate(
        self,
        prompt: str,
        response: str,
        evidence: list[dict]
    ) -> dict:
        """Fallback evaluation using simple keyword matching."""
        response_lower = response.lower()

        # Count positive and negative signals
        positive_signals = 0
        negative_signals = 0

        for e in evidence:
            snippet_lower = e.get("snippet", "").lower()
            title_lower = e.get("title", "").lower()

            # Check for overlapping key terms
            response_words = set(response_lower.split())
            snippet_words = set(snippet_lower.split())

            overlap = len(response_words & snippet_words)
            if overlap > 3:
                positive_signals += 1

            # Check for contradiction indicators
            contradiction_words = ["false", "incorrect", "wrong", "debunked", "myth", "fake"]
            if any(word in snippet_lower for word in contradiction_words):
                negative_signals += 1

        total = len(evidence) if evidence else 1

        if negative_signals > positive_signals:
            score = 0.2 + (0.15 * (negative_signals / total))
            return {
                "score": min(score, 0.35),
                "supported": False,
                "contradicted": True,
                "insufficient": False,
                "explanation": f"Evidence contains {negative_signals} potential contradiction signals."
            }
        elif positive_signals > 0:
            score = 0.5 + (0.4 * (positive_signals / total))
            return {
                "score": min(score, 0.85),
                "supported": True,
                "contradicted": False,
                "insufficient": False,
                "explanation": f"Evidence contains {positive_signals} supporting signals."
            }
        else:
            return {
                "score": 0.5,
                "supported": False,
                "contradicted": False,
                "insufficient": True,
                "explanation": "Insufficient evidence to make a determination."
            }
