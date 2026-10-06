from embedding.bge_m3 import BGEEmbeddingModel
from sparse.bm25 import BM25SparseModel
from vector_store.qdrant import QdrantVectorStore
from shared.db import SessionLocal

query = "கோடைக்காலத்திற்கு இலகுவான வசதியான உடைகள்"

print("Loading models...")
embedding_model = BGEEmbeddingModel()
sparse_model = BM25SparseModel()
vector_store = QdrantVectorStore()

db = SessionLocal()

# ---------------------------------------------------------
# DENSE
# ---------------------------------------------------------

print()
print("=" * 100)
print("DENSE BGE-M3 TOP 20")
print("=" * 100)

query_vector = embedding_model.embed_query(query)

dense_results = vector_store.search_dense(
    query_vector=query_vector,
    limit=20,
)

for i, result in enumerate(dense_results, start=1):
    print(
        f"{i:>2}. "
        f"id={result.id} "
        f"score={result.score:.6f} "
        f"payload={result.payload}"
    )

# ---------------------------------------------------------
# SPARSE
# ---------------------------------------------------------

print()
print("=" * 100)
print("SPARSE BM25 TOP 20")
print("=" * 100)

sparse_output = sparse_model.encode_query(query)

sparse_results = vector_store.search_sparse(
    indices=sparse_output.indices,
    values=sparse_output.values,
    limit=20,
)

for i, result in enumerate(sparse_results, start=1):
    print(
        f"{i:>2}. "
        f"id={result.id} "
        f"score={result.score:.6f} "
        f"payload={result.payload}"
    )

db.close()
