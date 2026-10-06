import pytest

from embedding.bge_m3 import BGEEmbeddingModel
from reranking.bge_reranker import BGEReranker
from search.hybrid_search import HybridSearch
from shared.db import SessionLocal
from sparse.bm25 import BM25SparseModel
from vector_store.qdrant import QdrantVectorStore


@pytest.mark.integration
def test_real_hybrid_search_with_reranker() -> None:
    query = "comfortable beach outfit for summer"

    embedding_model = BGEEmbeddingModel()
    sparse_model = BM25SparseModel()
    reranker = BGEReranker()
    vector_store = QdrantVectorStore()

    assert vector_store.hybrid_collection_exists()
    assert vector_store.count_hybrid_points() == 20_000

    search = HybridSearch(
        embedding_model=embedding_model,
        sparse_model=sparse_model,
        vector_store=vector_store,
        reranker=reranker,
    )

    with SessionLocal() as db:
        results = search.search(
            query=query,
            db=db,
            dense_top_k=50,
            sparse_top_k=50,
            fusion_top_k=20,
            final_top_k=10,
        )

    assert results
    assert len(results) <= 10

    for result in results:
        assert result["product"] is not None
        assert result["rerank_score"] is not None
        assert result["rrf_score"] > 0