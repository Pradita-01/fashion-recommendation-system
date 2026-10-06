from embedding.bge_m3 import BGEEmbeddingModel
from vector_store.qdrant import QdrantVectorStore


embedding_model = BGEEmbeddingModel()
vector_store = QdrantVectorStore()


queries = [
    (
        "TAMIL",
        "கோடைக்காலத்திற்கு இலகுவான வசதியான உடைகள்",
    ),
    (
        "ENGLISH",
        "lightweight comfortable clothes for summer",
    ),
]


for label, query in queries:

    print()
    print("=" * 100)
    print(label)
    print("QUERY:", query)
    print("=" * 100)

    # BGE-M3 implementation uses embed(), not embed_query()
    vector = embedding_model.embed(query)

    results = vector_store.search_dense(
        query_vector=vector,
        limit=10,
    )

    for i, result in enumerate(results, 1):

        print(
            f"{i:>2}. "
            f"id={result.id} "
            f"score={result.score:.6f} "
            f"title={result.payload.get('title', '')[:150]}"
        )
