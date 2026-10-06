from __future__ import annotations

from sentence_transformers import CrossEncoder


class BGEReranker:
    """
    Multilingual cross-encoder reranker.

    The reranker receives:
        (user query, product text)

    and produces a relevance score for each pair.
    """

    MODEL_NAME = "BAAI/bge-reranker-v2-m3"

    def __init__(self) -> None:
        self.model = CrossEncoder(
            self.MODEL_NAME,
            max_length=512,
            device="cpu",
        )

    def score(
        self,
        query: str,
        documents: list[str],
    ) -> list[float]:
        if not query.strip():
            raise ValueError("Query cannot be empty.")

        if not documents:
            return []

        pairs = [
            [query, document]
            for document in documents
        ]

        scores = self.model.predict(
            pairs,
            batch_size=2,
            show_progress_bar=False,
        )

        return [float(score) for score in scores]

    def rerank(
        self,
        query: str,
        documents: list[dict],
        top_k: int = 10,
    ) -> list[dict]:
        if not query.strip():
            raise ValueError("Query cannot be empty.")

        if not documents:
            return []

        texts = [
            document["text"]
            for document in documents
        ]

        scores = self.score(
            query=query,
            documents=texts,
        )

        reranked = []

        for document, score in zip(
            documents,
            scores,
            strict=True,
        ):
            reranked.append(
                {
                    **document,
                    "rerank_score": score,
                }
            )

        reranked.sort(
            key=lambda item: item["rerank_score"],
            reverse=True,
        )

        return reranked[:top_k]