"""
Embedding generation module using sentence-transformers.
Handles the conversion of text into dense vector representations.
"""

from sentence_transformers import SentenceTransformer
from typing import List, Union
import numpy as np
from app.settings import settings


class EmbeddingGenerator:
    """
    Generates embeddings using sentence-transformers.
    Uses a lightweight model suitable for local execution.
    """

    def __init__(self, model_name: str = None):
        """
        Initialize the embedding model.

        Args:
            model_name: Name of the sentence-transformer model to use
        """
        self.model_name = model_name or settings.embedding_model
        print(f"Loading embedding model: {self.model_name}")
        self.model = SentenceTransformer(self.model_name)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        print(f"Model loaded. Embedding dimension: {self.embedding_dim}")

    def encode(self, texts: Union[str, List[str]], batch_size: int = 32) -> np.ndarray:
        """
        Generate embeddings for input text(s).

        Args:
            texts: Single text string or list of text strings
            batch_size: Batch size for processing multiple texts

        Returns:
            numpy array of embeddings
        """
        if isinstance(texts, str):
            texts = [texts]

        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=len(texts) > 10,
            convert_to_numpy=True
        )

        return embeddings

    def encode_single(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Input text string

        Returns:
            List of floats representing the embedding
        """
        embedding = self.encode(text)
        return embedding[0].tolist()

    def encode_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a batch of texts.

        Args:
            texts: List of text strings

        Returns:
            List of embeddings (each embedding is a list of floats)
        """
        embeddings = self.encode(texts)
        return embeddings.tolist()


# Global embedding generator instance
_embedding_generator = None


def get_embedding_generator() -> EmbeddingGenerator:
    """
    Get or create the global embedding generator instance.
    Singleton pattern to avoid loading the model multiple times.

    Returns:
        EmbeddingGenerator instance
    """
    global _embedding_generator
    if _embedding_generator is None:
        _embedding_generator = EmbeddingGenerator()
    return _embedding_generator
