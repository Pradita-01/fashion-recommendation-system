from reranking.bge_reranker import BGEReranker


class FakeReranker(BGEReranker):
    def __init__(self) -> None:
        pass

    def score(
        self,
        query: str,
        documents: list[str],
    ) -> list[float]:
        return [
            0.2,
            0.9,
            0.5,
        ]


def test_reranker_sorts_by_relevance() -> None:
    reranker = FakeReranker()

    documents = [
        {"product_id": 1, "text": "red shirt"},
        {"product_id": 2, "text": "linen beach outfit"},
        {"product_id": 3, "text": "black jacket"},
    ]

    results = reranker.rerank(
        query="comfortable beach outfit",
        documents=documents,
        top_k=3,
    )

    assert len(results) == 3

    assert results[0]["product_id"] == 2
    assert results[1]["product_id"] == 3
    assert results[2]["product_id"] == 1

    assert results[0]["rerank_score"] == 0.9