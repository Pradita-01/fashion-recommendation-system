from embedding.bge_m3 import BGEEmbeddingModel
from vector_store.qdrant import QdrantVectorStore

query = "கோடைக்காலத்திற்கு இலகுவான வசதியான உடைகள்"

print("Loading models...")

embedding_model = BGEEmbeddingModel()
vector_store = QdrantVectorStore()

print()
print("=" * 100)
print("DENSE BGE-M3 TOP 20")
print("=" * 100)

query_vector = embedding_model.embed(query)

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
