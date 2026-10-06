from embedding.bge_m3 import BGEEmbeddingModel
from sparse.bm25 import BM25SparseModel
from vector_store.qdrant import QdrantVectorStore
from search.hybrid_search import HybridSearch
from shared.db import SessionLocal

query = "கோடைக்காலத்திற்கு இலகுவான வசதியான உடைகள்"

print("Loading models...")

embedding_model = BGEEmbeddingModel()
sparse_model = BM25SparseModel()
vector_store = QdrantVectorStore()

hybrid = HybridSearch(
    embedding_model=embedding_model,
    sparse_model=sparse_model,
    vector_store=vector_store,
    reranker=None,
)

db = SessionLocal()

results = hybrid.search(
    query,
    db=db,
    dense_top_k=50,
    sparse_top_k=50,
    fusion_top_k=50,
    final_top_k=20,
)

print()
print("=" * 100)
print("QUERY")
print("=" * 100)
print(query)

print()
print("=" * 100)
print("TOP 20 TAMIL RETRIEVAL")
print("=" * 100)

for i, result in enumerate(results, start=1):
    product = result["product"]

    print(
        f"{i:>2}. "
        f"id={product.id} "
        f"score={result['score']:.6f} "
        f"title={product.title[:150]}"
    )

db.close()
