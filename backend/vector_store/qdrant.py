from __future__ import annotations
import os

from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    PointStruct,
    ScoredPoint,
    SparseVector,
    SparseVectorParams,
    VectorParams,
)


class QdrantVectorStore:
    DENSE_COLLECTION_NAME = "fashion_products"
    COLLECTION_NAME = DENSE_COLLECTION_NAME
    HYBRID_COLLECTION_NAME = "fashion_products_hybrid"

    VECTOR_SIZE = 1024

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 6333,
    ) -> None:
        host = os.getenv("QDRANT_HOST", host)
        port = int(os.getenv("QDRANT_PORT", str(port)))
        self.client = QdrantClient(
            host=host,
            port=port,
        )

    # ------------------------------------------------------------------
    # Collection creation
    # ------------------------------------------------------------------

    def create_collection(self) -> None:
        collections = self.client.get_collections()

        existing_names = {
            collection.name
            for collection in collections.collections
        }

        if self.DENSE_COLLECTION_NAME not in existing_names:
            self.client.create_collection(
                collection_name=self.DENSE_COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=self.VECTOR_SIZE,
                    distance=Distance.COSINE,
                ),
            )

    def create_hybrid_collection(self) -> None:
        collections = self.client.get_collections()

        existing_names = {
            collection.name
            for collection in collections.collections
        }

        if self.HYBRID_COLLECTION_NAME in existing_names:
            return

        self.client.create_collection(
            collection_name=self.HYBRID_COLLECTION_NAME,
            vectors_config={
                "dense": VectorParams(
                    size=self.VECTOR_SIZE,
                    distance=Distance.COSINE,
                ),
            },
            sparse_vectors_config={
                "sparse": SparseVectorParams(
                    modifier="idf",
                ),
            },
        )

    # ------------------------------------------------------------------
    # Collection checks
    # ------------------------------------------------------------------

    def collection_exists(self) -> bool:
        collections = self.client.get_collections()

        return any(
            collection.name == self.DENSE_COLLECTION_NAME
            for collection in collections.collections
        )

    def hybrid_collection_exists(self) -> bool:
        collections = self.client.get_collections()

        return any(
            collection.name == self.HYBRID_COLLECTION_NAME
            for collection in collections.collections
        )

    # ------------------------------------------------------------------
    # Dense indexing
    # ------------------------------------------------------------------

    def upsert_points(
        self,
        points: list[dict[str, Any]],
    ) -> None:
        qdrant_points = [
            PointStruct(
                id=point["id"],
                vector=point["vector"],
                payload=point["payload"],
            )
            for point in points
        ]

        self.client.upsert(
            collection_name=self.DENSE_COLLECTION_NAME,
            points=qdrant_points,
        )

    # ------------------------------------------------------------------
    # Hybrid indexing
    # ------------------------------------------------------------------

    def upsert_hybrid_points(
        self,
        points: list[dict[str, Any]],
    ) -> None:
        qdrant_points = [
            PointStruct(
                id=point["id"],
                vector={
                    "dense": point["dense_vector"],
                    "sparse": {
                        "indices": point["sparse_indices"],
                        "values": point["sparse_values"],
                    },
                },
                payload=point["payload"],
            )
            for point in points
        ]

        self.client.upsert(
            collection_name=self.HYBRID_COLLECTION_NAME,
            points=qdrant_points,
        )

    # ------------------------------------------------------------------
    # Dense retrieval
    # ------------------------------------------------------------------

    def search_dense(
        self,
        query_vector: list[float],
        limit: int = 50,
    ) -> list[ScoredPoint]:
        response = self.client.query_points(
            collection_name=self.DENSE_COLLECTION_NAME,
            query=query_vector,
            limit=limit,
            with_payload=True,
        )

        return list(response.points)

    # ------------------------------------------------------------------
    # Sparse retrieval
    # ------------------------------------------------------------------

    def search_sparse(
        self,
        indices: list[int],
        values: list[float],
        limit: int = 50,
    ) -> list[ScoredPoint]:
        sparse_vector = SparseVector(
            indices=indices,
            values=values,
        )

        response = self.client.query_points(
            collection_name=self.HYBRID_COLLECTION_NAME,
            query=sparse_vector,
            using="sparse",
            limit=limit,
            with_payload=True,
        )

        return list(response.points)

    # ------------------------------------------------------------------
    # Hybrid dense retrieval
    # ------------------------------------------------------------------

    def search_hybrid_dense(
        self,
        query_vector: list[float],
        limit: int = 50,
    ) -> list[ScoredPoint]:
        response = self.client.query_points(
            collection_name=self.HYBRID_COLLECTION_NAME,
            query=query_vector,
            using="dense",
            limit=limit,
            with_payload=True,
        )

        return list(response.points)

    # ------------------------------------------------------------------
    # Counts
    # ------------------------------------------------------------------

    def count_dense_points(self) -> int:
        result = self.client.count(
            collection_name=self.DENSE_COLLECTION_NAME,
            exact=True,
        )

        return result.count

    def count_hybrid_points(self) -> int:
        result = self.client.count(
            collection_name=self.HYBRID_COLLECTION_NAME,
            exact=True,
        )

        return result.count