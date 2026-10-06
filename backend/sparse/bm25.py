from __future__ import annotations

from fastembed import SparseTextEmbedding


class BM25SparseModel:
    """BM25 sparse embedding model backed by FastEmbed."""

    MODEL_NAME = "Qdrant/bm25"

    def __init__(self) -> None:
        self.model = SparseTextEmbedding(
            model_name=self.MODEL_NAME,
        )

    def embed(self, text: str) -> tuple[list[int], list[float]]:
        """
        Convert text into a BM25 sparse representation.

        Returns:
            A tuple containing:
            - sparse token indices
            - corresponding sparse values
        """
        if not text.strip():
            raise ValueError("Text cannot be empty.")

        embeddings = list(self.model.embed([text]))

        if not embeddings:
            raise RuntimeError(
                "BM25 model returned no embedding."
            )

        embedding = embeddings[0]

        return (
            embedding.indices.tolist(),
            embedding.values.tolist(),
        )