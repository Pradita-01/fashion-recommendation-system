from embedding.bge_m3 import BGEEmbeddingModel
from search.semantic_search import SemanticSearch
from shared.db import SessionLocal
from vector_store.qdrant import QdrantVectorStore


def test_semantic_search_returns_results() -> None:
    embedding_model = BGEEmbeddingModel()
    vector_store = QdrantVectorStore()

    search = SemanticSearch(
        embedding_model=embedding_model,
        vector_store=vector_store,
    )

    with SessionLocal() as db:
        results = search.search(
            query="comfortable beach outfit for summer",
            db=db,
            top_k=5,
        )

    assert len(results) > 0