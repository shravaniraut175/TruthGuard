# TruthGuard Embeddings Module
"""Semantic similarity using sentence transformers."""

from typing import Optional
import numpy as np


class EmbeddingModel:
    """Sentence transformer embedding model for semantic similarity."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the embedding model.

        Args:
            model_name: Hugging Face model name for sentence transformers
        """
        self.model_name = model_name
        self._model = None
        self._initialized = False

    def _ensure_initialized(self) -> None:
        """Lazy initialization of the model."""
        if not self._initialized:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
                self._initialized = True
            except Exception as e:
                raise RuntimeError(f"Failed to load embedding model: {str(e)}")

    def encode(self, texts: list[str], batch_size: int = 32) -> np.ndarray:
        """
        Encode texts into embeddings.

        Args:
            texts: List of text strings to encode
            batch_size: Batch size for encoding

        Returns:
            Numpy array of embeddings
        """
        self._ensure_initialized()
        return self._model.encode(texts, batch_size=batch_size, convert_to_numpy=True)

    def similarity(self, text1: str, text2: str) -> float:
        """
        Calculate cosine similarity between two texts.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Cosine similarity score (0.0 to 1.0)
        """
        self._ensure_initialized()
        embeddings = self._model.encode([text1, text2], convert_to_numpy=True)
        
        # Calculate cosine similarity
        norm1 = np.linalg.norm(embeddings[0])
        norm2 = np.linalg.norm(embeddings[1])
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        similarity = np.dot(embeddings[0], embeddings[1]) / (norm1 * norm2)
        
        # Normalize to 0-1 range (cosine similarity is -1 to 1)
        return float((similarity + 1) / 2)

    def batch_similarity(self, reference: str, candidates: list[str]) -> list[float]:
        """
        Calculate similarity between a reference text and multiple candidates.

        Args:
            reference: Reference text
            candidates: List of candidate texts

        Returns:
            List of similarity scores
        """
        self._ensure_initialized()
        all_texts = [reference] + candidates
        embeddings = self._model.encode(all_texts, convert_to_numpy=True)
        
        reference_embedding = embeddings[0]
        candidate_embeddings = embeddings[1:]
        
        similarities = []
        for cand_emb in candidate_embeddings:
            norm_ref = np.linalg.norm(reference_embedding)
            norm_cand = np.linalg.norm(cand_emb)
            
            if norm_ref == 0 or norm_cand == 0:
                similarities.append(0.0)
            else:
                sim = np.dot(reference_embedding, cand_emb) / (norm_ref * norm_cand)
                similarities.append(float((sim + 1) / 2))
        
        return similarities


# Global embedding model instance (lazy loaded)
_embedding_model: Optional[EmbeddingModel] = None


def get_embedding_model(model_name: str = "all-MiniLM-L6-v2") -> EmbeddingModel:
    """
    Get or create the global embedding model instance.

    Args:
        model_name: Model name for sentence transformers

    Returns:
        EmbeddingModel instance
    """
    global _embedding_model
    if _embedding_model is None or _embedding_model.model_name != model_name:
        _embedding_model = EmbeddingModel(model_name)
    return _embedding_model
