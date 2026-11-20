"""Local embedding service using sentence-transformers.

Runs entirely offline — no external embedding API calls.
"""

from typing import List, Optional

from sentence_transformers import SentenceTransformer


class EmbeddingService:
    """Generates local embeddings for text chunks."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model: Optional[SentenceTransformer] = None

    @property
    def model(self) -> SentenceTransformer:
        """Lazy-load the embedding model."""
        if self._model is None:
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of texts, returning a list of float vectors."""
        if not texts:
            return []
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()

    def embed_text(self, text: str) -> List[float]:
        """Embed a single text, returning a float vector."""
        return self.embed_texts([text])[0]
