from vector_store.qdrant import QdrantVectorStore


def test_qdrant_collection_creation() -> None:
    store = QdrantVectorStore()

    store.create_collection()

    assert store.collection_exists()


def test_qdrant_hybrid_collection_creation() -> None:
    store = QdrantVectorStore()

    store.create_hybrid_collection()

    assert store.hybrid_collection_exists()


def test_qdrant_hybrid_collection_contains_catalogue() -> None:
    store = QdrantVectorStore()

    store.create_hybrid_collection()

    assert store.count_hybrid_points() == 20_000