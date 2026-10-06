from __future__ import annotations

from typing import Any

from qdrant_client.models import PointIdsList
from sqlalchemy import select

from embedding.bge_m3 import BGEEmbeddingModel
from shared.db import SessionLocal
from shared.models import Product
from sparse.bm25 import BM25SparseModel
from vector_store.qdrant import QdrantVectorStore


BATCH_SIZE = 50
MAX_PRODUCTS = 20_000


def normalize_text(value: Any) -> str:
    if value is None:
        return ""

    if isinstance(value, str):
        return value.strip()

    if isinstance(value, list):
        return " ".join(
            normalize_text(item)
            for item in value
            if item is not None
        ).strip()

    if isinstance(value, dict):
        return " ".join(
            f"{key} {normalize_text(item)}"
            for key, item in value.items()
            if item is not None
        ).strip()

    return str(value).strip()


def build_product_text(product: Product) -> str:
    parts = [
        product.title,
        product.description or "",
        product.main_category or "",
        product.store or "",
        normalize_text(product.features),
        normalize_text(product.categories),
        normalize_text(product.details),
    ]

    return " ".join(
        part.strip()
        for part in parts
        if part and part.strip()
    )


def get_existing_ids(
    vector_store: QdrantVectorStore,
    product_ids: list[int],
) -> set[int]:
    """Return product IDs already present in the hybrid collection."""

    if not product_ids:
        return set()

    result = vector_store.client.retrieve(
        collection_name=vector_store.HYBRID_COLLECTION_NAME,
        ids=product_ids,
        with_payload=False,
        with_vectors=False,
    )

    return {int(point.id) for point in result}


def main() -> None:
    print("=" * 70)
    print("Day 4 - Resume-Safe Hybrid Product Indexing")
    print("=" * 70)

    embedding_model = BGEEmbeddingModel()
    sparse_model = BM25SparseModel()

    vector_store = QdrantVectorStore()
    vector_store.create_hybrid_collection()

    existing_count = vector_store.count_hybrid_points()

    print(f"Existing hybrid points : {existing_count}")
    print(f"Target products        : {MAX_PRODUCTS}")
    print()

    with SessionLocal() as db:
        products = db.scalars(
            select(Product)
            .order_by(Product.id)
            .limit(MAX_PRODUCTS)
        ).all()

        total = len(products)

        print(f"Products available     : {total}")
        print()

        indexed_this_run = 0
        skipped_existing = 0

        for start in range(0, total, BATCH_SIZE):
            batch = products[start : start + BATCH_SIZE]

            product_ids = [product.id for product in batch]

            existing_ids = get_existing_ids(
                vector_store,
                product_ids,
            )

            hybrid_points = []

            for product in batch:
                if product.id in existing_ids:
                    skipped_existing += 1
                    continue

                product_text = build_product_text(product)

                if not product_text:
                    print(
                        f"Skipping product {product.id}: "
                        "empty searchable text"
                    )
                    continue

                dense_vector = embedding_model.embed(product_text)

                sparse_indices, sparse_values = sparse_model.embed(
                    product_text
                )

                hybrid_points.append(
                    {
                        "id": product.id,
                        "dense_vector": dense_vector,
                        "sparse_indices": sparse_indices,
                        "sparse_values": sparse_values,
                        "payload": {
                            "product_id": product.id,
                            "parent_asin": product.parent_asin,
                            "title": product.title,
                            "main_category": product.main_category,
                            "store": product.store,
                        },
                    }
                )

            if hybrid_points:
                vector_store.upsert_hybrid_points(
                    hybrid_points
                )

                indexed_this_run += len(hybrid_points)

            current_count = vector_store.count_hybrid_points()

            print(
                f"Processed {min(start + BATCH_SIZE, total)}/{total} "
                f"| added this run: {indexed_this_run} "
                f"| skipped existing: {skipped_existing} "
                f"| total in Qdrant: {current_count}"
            )

    final_count = vector_store.count_hybrid_points()

    print()
    print("=" * 70)
    print("Hybrid indexing complete")
    print("=" * 70)
    print(f"Final hybrid points    : {final_count}")
    print(f"Added this run         : {indexed_this_run}")
    print(f"Skipped existing       : {skipped_existing}")

    if final_count != total:
        raise RuntimeError(
            f"Hybrid index incomplete: expected {total}, "
            f"found {final_count}."
        )

    print()
    print("SUCCESS: Hybrid collection contains all products.")


if __name__ == "__main__":
    main()