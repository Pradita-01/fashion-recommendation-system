from sentence_transformers import SentenceTransformer


class BGEEmbeddingModel:
    """Local multilingual embedding model based on BGE-M3."""

    MODEL_NAME = "BAAI/bge-m3"

    def __init__(self) -> None:
        self.model = SentenceTransformer(self.MODEL_NAME)

    def embed(self, text: str) -> list[float]:
        vector = self.model.encode(
            text,
            normalize_embeddings=True,
        )

        return vector.tolist()