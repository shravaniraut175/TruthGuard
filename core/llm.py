# TruthGuard LLM Provider Module
"""LLM provider abstraction for multiple backends."""

from enum import auto
import os
from abc import ABC, abstractmethod
from typing import Optional

from click import prompt

from pathlib import types

from .config import settings
from google import genai



class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def generate(self, prompt: str, temperature: float = 0.7) -> str:
        """Generate a response from the model."""
        pass

    @abstractmethod
    def generate_json(self, prompt: str, temperature: float = 0.3) -> dict:
        """Generate a JSON response from the model."""
        pass


class OpenRouterProvider(BaseLLMProvider):
    """OpenRouter provider using OpenAI-compatible API."""

    def __init__(self, model_name: str):
        self.model_name = model_name
        self.api_key = settings.OPENROUTER_API_KEY
        self.base_url = "https://openrouter.ai/api/v1"

        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY is not set")

        # Import here to avoid issues if not installed
        from openai import OpenAI
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

    def generate(self, prompt: str, temperature: float = 0.7) -> str:
        """Generate a response from the model."""
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            raise RuntimeError(f"OpenRouter generation failed: {str(e)}")

    def generate_json(self, prompt: str, temperature: float = 0.3) -> dict:
        """Generate a JSON response from the model."""
        prompt_with_json_instruction = (
            f"{prompt}\n\nPlease respond with ONLY a valid JSON object. "
            "Do not include any markdown formatting or additional text."
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt_with_json_instruction}],
                temperature=temperature,
            )
            content = response.choices[0].message.content or ""

            # Try to parse JSON from response
            import json
            from core.utils import safe_json_parse

            result = safe_json_parse(content)
            if result is None:
                # Fallback: try to find JSON in the content
                start = content.find("{")
                end = content.rfind("}") + 1
                if start >= 0 and end > start:
                    json_str = content[start:end]
                    result = safe_json_parse(json_str, {})
                else:
                    result = {}
            return result
        except Exception as e:
            raise RuntimeError(f"OpenRouter JSON generation failed: {str(e)}")


class GoogleGeminiProvider(BaseLLMProvider):
    """Google Gemini provider."""

    def __init__(self, model_name: str):
        self.model_name = model_name
        self.api_key = settings.GOOGLE_API_KEY

        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY is not set")

        from google import genai
        self.client = genai.Client(api_key=self.api_key)

    def generate(self, prompt: str, temperature: float = 0.7) -> str:
        """Generate a response from the model."""
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=temperature,
                    automatic_function_calling=types.AutomaticFunctionCallingConfig(
                        disable=True
                    )
                )
            )
            return response.text or ""

        except Exception as e:
            raise RuntimeError(
                f"Google Gemini generation failed: {str(e)}"
            )

    def generate_json(self, prompt: str, temperature: float = 0.3) -> dict:
        """Generate a JSON response from the model."""

        prompt_with_json_instruction = (
            f"{prompt}\n\n"
            "Please respond with ONLY a valid JSON object. "
            "Do not include any markdown formatting or additional text."
        )

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt_with_json_instruction,
                config=types.GenerateContentConfig(
                    temperature=temperature,
                    automatic_function_calling=types.AutomaticFunctionCallingConfig(
                        disable=True
                    )
                )       
            )

            content = response.text or ""

            from core.utils import safe_json_parse

            result = safe_json_parse(content)

            if result is None:
                start = content.find("{")
                end = content.rfind("}") + 1

                if start >= 0 and end > start:
                    json_str = content[start:end]
                    result = safe_json_parse(json_str, {})
                else:
                    result = {}

            return result

        except Exception as e:
            raise RuntimeError(
                f"Google Gemini JSON generation failed: {str(e)}"
            )

class OpenAIProvider(BaseLLMProvider):
    """OpenAI provider."""

    def __init__(self, model_name: str):
        self.model_name = model_name
        self.api_key = settings.OPENAI_API_KEY

        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is not set")

        from openai import OpenAI
        self.client = OpenAI(api_key=self.api_key)

    def generate(self, prompt: str, temperature: float = 0.7) -> str:
        """Generate a response from the model."""
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            raise RuntimeError(f"OpenAI generation failed: {str(e)}")

    def generate_json(self, prompt: str, temperature: float = 0.3) -> dict:
        """Generate a JSON response from the model."""
        prompt_with_json_instruction = (
            f"{prompt}\n\nPlease respond with ONLY a valid JSON object. "
            "Do not include any markdown formatting or additional text."
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt_with_json_instruction}],
                temperature=temperature,
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content or ""

            import json
            from core.utils import safe_json_parse

            result = safe_json_parse(content)
            if result is None:
                start = content.find("{")
                end = content.rfind("}") + 1
                if start >= 0 and end > start:
                    json_str = content[start:end]
                    result = safe_json_parse(json_str, {})
                else:
                    result = {}
            return result
        except Exception as e:
            raise RuntimeError(f"OpenAI JSON generation failed: {str(e)}")


class LLMProvider:
    """Factory class for creating LLM providers."""

    _providers = {
        "openrouter": OpenRouterProvider,
        "google": GoogleGeminiProvider,
        "openai": OpenAIProvider,
    }

    @classmethod
    def create(cls, provider: str, model_name: str) -> BaseLLMProvider:
        """
        Create an LLM provider instance.

        Args:
            provider: Provider name (openrouter, google, openai)
            model_name: Model name/identifier

        Returns:
            LLM provider instance

        Raises:
            ValueError: If provider is not supported
        """
        provider_lower = provider.lower()
        if provider_lower not in cls._providers:
            raise ValueError(
                f"Unsupported provider: {provider}. "
                f"Supported providers: {list(cls._providers.keys())}"
            )
        return cls._providers[provider_lower](model_name)


def get_llm_provider(provider: str, model_name: str) -> BaseLLMProvider:
    """
    Get an LLM provider instance.

    Args:
        provider: Provider name
        model_name: Model name

    Returns:
        LLM provider instance
    """
    return LLMProvider.create(provider, model_name)
