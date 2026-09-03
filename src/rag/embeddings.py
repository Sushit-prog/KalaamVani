"""Embedding wrapper around sentence-transformers."""

from sentence_transformers import SentenceTransformer


class EmbeddingModel:
    """Wraps a sentence-transformers model for batch and query embedding."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Batch embed a list of texts."""
        return self.model.encode(texts, show_progress_bar=True).tolist()

    def embed_query(self, query: str) -> list[float]:
        """Embed a single query string."""
        return self.model.encode([query])[0].tolist()
