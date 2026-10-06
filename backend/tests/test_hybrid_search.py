import pytest

from embedding.bge_m3 import BGEEmbeddingModel
from search.hybrid_search import HybridSearch
from shared.db import SessionLocal
from sparse.bm25 import BM25SparseModel
from vector_store.qdrant import QdrantVectorStore


def test_rrf_fusion_combines_dense_and_sparse_results() -> None:
    search = HybridSearch.__new__(HybridSearch)

    dense_results = [
        {
            "product_id": 1,
            "rank": 1,
            "score": 0.9,
        },
        {
            "product_id": 2,
            "rank": 2,
            "score": 0.8,
        },
    ]

    sparse_results = [
        {
            "product_id": 2,
            "rank": 1,
            "score": 1.0,
        },
        {
            "product_id": 3,
            "rank": 2,
            "score": 0.7,
        },
    ]

    results = search._rrf_fusion(
        dense_results=dense_results,
        sparse_results=sparse_results,
        top_k=3,
    )

    assert len(results) == 3
    assert results[0]["product_id"] == 2
    assert results[0]["dense_rank"] == 2
    assert results[0]["sparse_rank"] == 1


@pytest.mark.integration
def test_real_hybrid_search_returns_results() -> None:
    """
    Integration test for the complete hybrid retrieval pipeline.

    Requires:
    - PostgreSQL catalogue
    - Qdrant hybrid collection
    - BGE-M3 model
    - BM25 sparse model
    """

    query = "comfortable beach outfit for summer"

    embedding_model = BGEEmbeddingModel()
    sparse_model = BM25SparseModel()
    vector_store = QdrantVectorStore()

    assert vector_store.hybrid_collection_exists()
    assert vector_store.count_hybrid_points() == 20_000

    hybrid_search = HybridSearch(
        embedding_model=embedding_model,
        sparse_model=sparse_model,
        vector_store=vector_store,
    )

    with SessionLocal() as db:
        results = hybrid_search.search(
            query=query,
            db=db,
            dense_top_k=50,
            sparse_top_k=50,
            final_top_k=10,
        )

    assert results
    assert len(results) <= 10

    for result in results:
        assert result["product"] is not None
        assert result["product"].id > 0
        assert result["score"] > 0
        assert (
            result["dense_rank"] is not None
            or result["sparse_rank"] is not None
        )
def test_hybrid_search_supports_reranker() -> None:
    class FakeEmbeddingModel:
        def embed(self, text: str) -> list[float]:
            return [0.0] * 1024

    class FakeSparseModel:
        def embed(self, text: str) -> tuple[list[int], list[float]]:
            return [1], [1.0]

    class FakeReranker:
        def rerank(
            self,
            query: str,
            documents: list[dict],
            top_k: int,
        ) -> list[dict]:
            ranked = sorted(
                documents,
                key=lambda item: item["product_id"],
                reverse=True,
            )

            return ranked[:top_k]

    search = HybridSearch(
        embedding_model=FakeEmbeddingModel(),
        sparse_model=FakeSparseModel(),
        vector_store=None,
        reranker=FakeReranker(),
    )

    candidates = [
        {
            "product_id": 1,
            "text": "product one",
            "product": object(),
            "rrf_score": 0.1,
            "dense_rank": 1,
            "sparse_rank": 2,
        },
        {
            "product_id": 2,
            "text": "product two",
            "product": object(),
            "rrf_score": 0.2,
            "dense_rank": 2,
            "sparse_rank": 1,
        },
    ]

    reranked = search.reranker.rerank(
        query="test query",
        documents=candidates,
        top_k=2,
    )

    assert reranked[0]["product_id"] == 2
    assert reranked[1]["product_id"] == 1