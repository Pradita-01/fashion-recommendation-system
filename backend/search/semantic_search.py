from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from embedding.bge_m3 import BGEEmbeddingModel
from shared.models import Product
from vector_store.qdrant import QdrantVectorStore


class SemanticSearch:
    """Dense semantic search over the fashion catalogue."""

    def __init__(
        self,
        embedding_model: BGEEmbeddingModel,
        vector_store: QdrantVectorStore,
    ) -> None:
        self.embedding_model = embedding_model
        self.vector_store = vector_store

    def search(
        self,
        query: str,
        db: Session,
        top_k: int = 10,
    ) -> list[dict]:
        query_vector = self.embedding_model.embed(query)

        results = self.vector_store.client.query_points(
            collection_name=self.vector_store.COLLECTION_NAME,
            query=query_vector,
            limit=top_k,
            with_payload=True,
        ).points

        product_ids = [
            int(result.payload["product_id"])
            for result in results
            if result.payload and "product_id" in result.payload
        ]

        if not product_ids:
            return []

        products = db.scalars(
            select(Product).where(Product.id.in_(product_ids))
        ).all()

        products_by_id = {
            product.id: product
            for product in products
        }

        output = []

        for result in results:
            if not result.payload:
                continue

            product_id = result.payload.get("product_id")

            if product_id is None:
                continue

            product = products_by_id.get(int(product_id))

            if product is None:
                continue

            output.append(
                {
                    "product": product,
                    "score": result.score,
                }
            )

        return output