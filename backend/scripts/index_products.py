from __future__ import annotations

from sqlalchemy import select

from embedding.bge_m3 import BGEEmbeddingModel
from shared.db import SessionLocal
from shared.models import Product
from vector_store.qdrant import QdrantVectorStore


BATCH_SIZE = 50
MAX_PRODUCTS = 20_000


def build_product_text(product: Product) -> str:
    parts: list[str] = []

    if product.title:
        parts.append(f"Title: {product.title}")

    if product.description:
        parts.append(f"Description: {product.description}")

    if product.main_category:
        parts.append(f"Category: {product.main_category}")

    if product.store:
        parts.append(f"Store: {product.store}")

    if product.features:
        features = " ".join(str(feature) for feature in product.features)
        if features:
            parts.append(f"Features: {features}")

    if product.categories:
        categories = " > ".join(
            str(category) for category in product.categories
        )
        if categories:
            parts.append(f"Categories: {categories}")

    if product.details:
        details = " ".join(
            f"{key}: {value}"
            for key, value in product.details.items()
        )
        if details:
            parts.append(f"Details: {details}")

    return "\n".join(parts)


def main() -> None:
    vector_store = QdrantVectorStore()
    vector_store.create_collection()

    embedding_model = BGEEmbeddingModel()

    with SessionLocal() as db:
        products = db.scalars(
            select(Product)
            .order_by(Product.id)
            .limit(MAX_PRODUCTS)
        ).all()

    print(f"Products selected: {len(products)}")

    points = []

    for index, product in enumerate(products, start=1):
        text = build_product_text(product)

        vector = embedding_model.embed(text)

        points.append(
            {
                "id": product.id,
                "vector": vector,
                "payload": {
                    "product_id": product.id,
                    "parent_asin": product.parent_asin,
                    "title": product.title,
                    "main_category": product.main_category,
                    "store": product.store,
                },
            }
        )

        if len(points) >= BATCH_SIZE:
            vector_store.upsert_points(points)
            print(f"Indexed {index}/{len(products)} products")
            points = []

    if points:
        vector_store.upsert_points(points)
        print(f"Indexed {len(products)}/{len(products)} products")

    print("Indexing complete.")


if __name__ == "__main__":
    main()