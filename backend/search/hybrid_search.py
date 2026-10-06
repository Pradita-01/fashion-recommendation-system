from __future__ import annotations

from collections import defaultdict

from qdrant_client.models import SparseVector
from sqlalchemy import select
from sqlalchemy.orm import Session

from embedding.bge_m3 import BGEEmbeddingModel
from reranking.bge_reranker import BGEReranker
from reranking.product_text import build_product_text
from shared.models import Product
from sparse.bm25 import BM25SparseModel
from vector_store.qdrant import QdrantVectorStore


class HybridSearch:
    """
    Hybrid retrieval pipeline:

    1. BGE-M3 dense retrieval
    2. BM25 sparse retrieval
    3. Reciprocal Rank Fusion (RRF)
    4. Dedicated multilingual cross-encoder reranking
    """

    RRF_K = 60

    def __init__(
        self,
        embedding_model: BGEEmbeddingModel,
        sparse_model: BM25SparseModel,
        vector_store: QdrantVectorStore,
        reranker: BGEReranker | None = None,
    ) -> None:
        self.embedding_model = embedding_model
        self.sparse_model = sparse_model
        self.vector_store = vector_store
        self.reranker = reranker

    def search(
        self,
        query: str,
        db: Session,
        dense_top_k: int = 50,
        sparse_top_k: int = 50,
        fusion_top_k: int = 50,
        final_top_k: int = 10,
    ) -> list[dict]:

        if not query.strip():
            raise ValueError("Query cannot be empty.")

        dense_vector = self.embedding_model.embed(query)

        sparse_indices, sparse_values = self.sparse_model.embed(query)

        dense_results = self._dense_search(
            dense_vector=dense_vector,
            top_k=dense_top_k,
        )

        sparse_results = self._sparse_search(
            sparse_indices=sparse_indices,
            sparse_values=sparse_values,
            top_k=sparse_top_k,
        )

        fused_results = self._rrf_fusion(
            dense_results=dense_results,
            sparse_results=sparse_results,
            top_k=fusion_top_k,
        )

        if not fused_results:
            return []

        product_ids = [
            result["product_id"]
            for result in fused_results
        ]

        products = db.scalars(
            select(Product).where(Product.id.in_(product_ids))
        ).all()

        products_by_id = {
            product.id: product
            for product in products
        }

        candidates: list[dict] = []

        for result in fused_results:
            product_id = result["product_id"]

            product = products_by_id.get(product_id)

            if product is None:
                continue

            candidates.append(
                {
                    "product": product,
                    "product_id": product.id,
                    "text": build_product_text(product),
                    "score": result["score"],
                    "rrf_score": result["score"],
                    "dense_rank": result.get("dense_rank"),
                    "sparse_rank": result.get("sparse_rank"),
                }
            )

        if not candidates:
            return []

        # ---------------------------------------------------------
        # Dedicated reranking
        # ---------------------------------------------------------

        if self.reranker is not None:
            reranked = self.reranker.rerank(
                query=query,
                documents=[
                    {
                        "product_id": candidate["product_id"],
                        "text": candidate["text"],
                        "product": candidate["product"],
                        "rrf_score": candidate["rrf_score"],
                        "dense_rank": candidate["dense_rank"],
                        "sparse_rank": candidate["sparse_rank"],
                    }
                    for candidate in candidates
                ],
                top_k=final_top_k,
            )

            output: list[dict] = []

            for result in reranked:
                output.append(
                    {
                        "product": result["product"],
                        "score": result["rerank_score"],
                        "rerank_score": result["rerank_score"],
                        "rrf_score": result["rrf_score"],
                        "dense_rank": result["dense_rank"],
                        "sparse_rank": result["sparse_rank"],
                    }
                )

            return output

        # ---------------------------------------------------------
        # Graceful degradation:
        # no reranker → return RRF results
        # ---------------------------------------------------------

        return candidates[:final_top_k]

    def _dense_search(
        self,
        dense_vector: list[float],
        top_k: int,
    ) -> list[dict]:

        results = self.vector_store.client.query_points(
            collection_name=self.vector_store.HYBRID_COLLECTION_NAME,
            query=dense_vector,
            using="dense",
            limit=top_k,
            with_payload=True,
        ).points

        output: list[dict] = []

        for rank, result in enumerate(results, start=1):

            if not result.payload:
                continue

            product_id = result.payload.get("product_id")

            if product_id is None:
                continue

            output.append(
                {
                    "product_id": int(product_id),
                    "rank": rank,
                    "score": float(result.score),
                }
            )

        return output

    def _sparse_search(
        self,
        sparse_indices: list[int],
        sparse_values: list[float],
        top_k: int,
    ) -> list[dict]:

        sparse_vector = SparseVector(
            indices=sparse_indices,
            values=sparse_values,
        )

        results = self.vector_store.client.query_points(
            collection_name=self.vector_store.HYBRID_COLLECTION_NAME,
            query=sparse_vector,
            using="sparse",
            limit=top_k,
            with_payload=True,
        ).points

        output: list[dict] = []

        for rank, result in enumerate(results, start=1):

            if not result.payload:
                continue

            product_id = result.payload.get("product_id")

            if product_id is None:
                continue

            output.append(
                {
                    "product_id": int(product_id),
                    "rank": rank,
                    "score": float(result.score),
                }
            )

        return output

    def _rrf_fusion(
        self,
        dense_results: list[dict],
        sparse_results: list[dict],
        top_k: int,
    ) -> list[dict]:

        fused: dict[int, dict] = defaultdict(
            lambda: {
                "score": 0.0,
                "dense_rank": None,
                "sparse_rank": None,
            }
        )

        for result in dense_results:

            product_id = result["product_id"]
            rank = result["rank"]

            fused[product_id]["score"] += (
                1.0 / (self.RRF_K + rank)
            )

            fused[product_id]["dense_rank"] = rank

        for result in sparse_results:

            product_id = result["product_id"]
            rank = result["rank"]

            fused[product_id]["score"] += (
                1.0 / (self.RRF_K + rank)
            )

            fused[product_id]["sparse_rank"] = rank

        ranked = sorted(
            fused.items(),
            key=lambda item: item[1]["score"],
            reverse=True,
        )

        output: list[dict] = []

        for product_id, data in ranked[:top_k]:

            output.append(
                {
                    "product_id": product_id,
                    "score": data["score"],
                    "dense_rank": data["dense_rank"],
                    "sparse_rank": data["sparse_rank"],
                }
            )

        return output