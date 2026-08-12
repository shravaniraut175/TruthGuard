# TruthGuard White-Box Detector Module
"""White-box token confidence detector using Hugging Face models."""

from typing import Optional
from dataclasses import dataclass

from .config import settings


@dataclass
class WhiteBoxResult:
    """Result from white-box token confidence detection."""
    score: float  # 0.0 to 1.0, higher means more confident
    mean_token_probability: float
    min_token_probability: float
    max_token_probability: float
    num_tokens: int
    explanation: str
    available: bool = True  # False if model is unavailable


class WhiteBoxDetector:
    """
    White-box token confidence detector.

    Uses a local Hugging Face causal language model to calculate
    mean token probability for response tokens.
    Disabled by default to avoid heavy dependencies.
    """

    def __init__(self):
        self.enabled = settings.WHITEBOX_ENABLED
        self.model_name = settings.WHITEBOX_MODEL
        self._model = None
        self._tokenizer = None
        self._initialized = False
        self._initialization_error: Optional[str] = None

    def _ensure_initialized(self) -> None:
        """Lazy initialization of the model."""
        if self._initialized:
            return

        if not self.enabled:
            self._initialization_error = "White-box detector is disabled"
            return

        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer

            # Load tokenizer
            self._tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=True
            )

            # Set pad token if not set
            if self._tokenizer.pad_token is None:
                self._tokenizer.pad_token = self._tokenizer.eos_token

            # Load model
            self._model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                trust_remote_code=True,
                torch_dtype=torch.float32,
                device_map="auto" if torch.cuda.is_available() else None
            )

            if not torch.cuda.is_available():
                self._model = self._model.cpu()

            self._model.eval()
            self._initialized = True

        except ImportError as e:
            self._initialization_error = f"Required libraries not installed: {str(e)}"
        except Exception as e:
            self._initialization_error = f"Failed to load model: {str(e)}"

    def detect(self, prompt: str, response: str) -> WhiteBoxResult:
        """
        Detect hallucination using white-box token confidence.

        Args:
            prompt: User prompt
            response: LLM response to verify

        Returns:
            WhiteBoxResult with confidence score and details
        """
        self._ensure_initialized()

        if not self.enabled:
            return WhiteBoxResult(
                score=0.5,
                mean_token_probability=0.5,
                min_token_probability=0.5,
                max_token_probability=0.5,
                num_tokens=0,
                explanation="White-box detector is disabled",
                available=False
            )

        if self._initialization_error:
            return WhiteBoxResult(
                score=0.5,
                mean_token_probability=0.5,
                min_token_probability=0.5,
                max_token_probability=0.5,
                num_tokens=0,
                explanation=f"White-box detector unavailable: {self._initialization_error}",
                available=False
            )

        try:
            return self._calculate_token_confidence(prompt, response)
        except Exception as e:
            return WhiteBoxResult(
                score=0.5,
                mean_token_probability=0.5,
                min_token_probability=0.5,
                max_token_probability=0.5,
                num_tokens=0,
                explanation=f"Error during token confidence calculation: {str(e)}",
                available=True
            )

    def _calculate_token_confidence(self, prompt: str, response: str) -> WhiteBoxResult:
        """
        Calculate token-level confidence scores.

        Args:
            prompt: User prompt
            response: LLM response

        Returns:
            WhiteBoxResult with confidence metrics
        """
        import torch

        # Tokenize input
        full_text = f"{prompt} {response}"
        inputs = self._tokenizer(full_text, return_tensors="pt")

        # Get prompt length to isolate response tokens
        prompt_inputs = self._tokenizer(prompt, return_tensors="pt")
        prompt_length = prompt_inputs.input_ids.shape[1]

        # Move to appropriate device
        if torch.cuda.is_available():
            inputs = {k: v.cuda() for k, v in inputs.items()}
        else:
            inputs = {k: v.cpu() for k, v in inputs.items()}

        # Get model predictions
        with torch.no_grad():
            outputs = self._model(**inputs)
            logits = outputs.logits

        # Extract probabilities for response tokens only
        token_probs = []
        shift_logits = logits[:, prompt_length - 1:-1, :]
        shift_labels = inputs.input_ids[:, prompt_length:]

        # Calculate softmax probabilities
        probs = torch.softmax(shift_logits, dim=-1)

        # Get probability of actual next token
        for i in range(shift_labels.shape[1]):
            label = shift_labels[0, i].item()
            prob = probs[0, i, label].item()
            token_probs.append(prob)

        if not token_probs:
            return WhiteBoxResult(
                score=0.5,
                mean_token_probability=0.5,
                min_token_probability=0.5,
                max_token_probability=0.5,
                num_tokens=0,
                explanation="No response tokens to analyze",
                available=True
            )

        # Calculate statistics
        mean_prob = sum(token_probs) / len(token_probs)
        min_prob = min(token_probs)
        max_prob = max(token_probs)

        # Score is mean token probability (higher = more confident)
        score = mean_prob

        # Generate explanation
        explanation = self._generate_explanation(
            score, mean_prob, min_prob, max_prob, len(token_probs)
        )

        return WhiteBoxResult(
            score=score,
            mean_token_probability=mean_prob,
            min_token_probability=min_prob,
            max_token_probability=max_prob,
            num_tokens=len(token_probs),
            explanation=explanation,
            available=True
        )

    def _generate_explanation(
        self,
        score: float,
        mean_prob: float,
        min_prob: float,
        max_prob: float,
        num_tokens: int
    ) -> str:
        """Generate human-readable explanation."""
        if score >= 0.8:
            confidence_level = "highly confident"
        elif score >= 0.6:
            confidence_level = "moderately confident"
        elif score >= 0.4:
            confidence_level = "somewhat uncertain"
        else:
            confidence_level = "highly uncertain"

        explanation = (
            f"The model is {confidence_level} in its response tokens. "
            f"Mean token probability: {mean_prob:.2f}, "
            f"range: [{min_prob:.2f}, {max_prob:.2f}], "
            f"over {num_tokens} tokens."
        )

        return explanation
