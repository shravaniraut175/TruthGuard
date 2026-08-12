# TruthGuard Utility Functions
"""Utility functions for TruthGuard."""

import json
from typing import Any, Optional


def calculate_risk_level(hallucination_probability: float) -> str:
    """
    Calculate risk level based on hallucination probability.

    Args:
        hallucination_probability: Probability of hallucination (0.0 to 1.0)

    Returns:
        Risk level string: 'low', 'medium', 'high', or 'critical'
    """
    if hallucination_probability < 0.30:
        return "low"
    elif hallucination_probability < 0.50:
        return "medium"
    elif hallucination_probability < 0.70:
        return "high"
    else:
        return "critical"


def safe_json_parse(json_string: str, fallback_value: Any = None) -> Optional[dict]:
    """
    Safely parse a JSON string with fallback value.

    Args:
        json_string: JSON string to parse
        fallback_value: Value to return if parsing fails

    Returns:
        Parsed dictionary or fallback value
    """
    try:
        # Try to extract JSON from markdown code blocks if present
        if "```json" in json_string:
            start = json_string.find("```json") + len("```json")
            end = json_string.find("```", start)
            json_string = json_string[start:end].strip()
        elif "```" in json_string:
            start = json_string.find("```") + len("```")
            end = json_string.find("```", start)
            json_string = json_string[start:end].strip()

        result = json.loads(json_string)
        if isinstance(result, dict):
            return result
        return fallback_value
    except (json.JSONDecodeError, ValueError, TypeError):
        return fallback_value


def truncate_text(text: str, max_length: int = 500) -> str:
    """
    Truncate text to maximum length while preserving word boundaries.

    Args:
        text: Text to truncate
        max_length: Maximum length in characters

    Returns:
        Truncated text with ellipsis if needed
    """
    if len(text) <= max_length:
        return text

    # Find last space before max_length
    truncated = text[:max_length]
    last_space = truncated.rfind(' ')

    if last_space > max_length * 0.8:
        return truncated[:last_space] + "..."
    return truncated + "..."


def format_sources(sources: list[dict]) -> list[str]:
    """
    Format source dictionaries into readable strings.

    Args:
        sources: List of source dictionaries with 'title' and 'url' keys

    Returns:
        List of formatted source strings
    """
    formatted = []
    for i, source in enumerate(sources, 1):
        title = source.get("title", "Untitled")
        url = source.get("url", "")
        if url:
            formatted.append(f"[{i}] {title}: {url}")
        else:
            formatted.append(f"[{i}] {title}")
    return formatted


def clean_response_text(text: str) -> str:
    """
    Clean response text by removing markdown artifacts and extra whitespace.

    Args:
        text: Raw response text

    Returns:
        Cleaned text
    """
    import re

    # Remove markdown code blocks but keep content
    text = re.sub(r"```[\w]*\n?", "", text)
    text = re.sub(r"```\n?", "", text)

    # Remove excessive newlines
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Strip leading/trailing whitespace
    text = text.strip()

    return text
