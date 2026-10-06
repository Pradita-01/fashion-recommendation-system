import json
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from sqlalchemy import select

# Allow imports from backend/
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from shared.db import SessionLocal  # noqa: E402
from shared.models import CatalogVersion, Product  # noqa: E402


DATA_FILE = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "raw"
    / "meta_Amazon_Fashion.jsonl"
)

CATALOG_VERSION = "amazon-fashion-day1-v1"
MAX_PRODUCTS = 20_000
BATCH_SIZE = 500


def normalize_text(value: Any) -> str | None:
    """Convert strings/lists into clean text."""
    if value is None:
        return None

    if isinstance(value, str):
        value = value.strip()
        return value or None

    if isinstance(value, list):
        parts = []

        for item in value:
            if isinstance(item, str):
                text = item.strip()
                if text:
                    parts.append(text)
            elif isinstance(item, dict):
                parts.append(json.dumps(item, ensure_ascii=False))

        return "\n".join(parts) or None

    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)

    return str(value).strip() or None


def normalize_list(value: Any) -> list | None:
    """Ensure JSON/list-like source fields are stored as JSON arrays."""
    if value is None:
        return None

    if isinstance(value, list):
        return value

    return [value]


def normalize_dict(value: Any) -> dict | None:
    """Ensure dictionary-like source fields remain dictionaries."""
    if value is None:
        return None

    if isinstance(value, dict):
        return value

    return None


def parse_price(value: Any) -> Decimal | None:
    """Parse Amazon price values into Decimal."""
    if value is None:
        return None

    if isinstance(value, (int, float, Decimal)):
        try:
            return Decimal(str(value))
        except InvalidOperation:
            return None

    if isinstance(value, str):
        cleaned = (
            value.strip()
            .replace("$", "")
            .replace("£", "")
            .replace("€", "")
            .replace(",", "")
        )

        if not cleaned:
            return None

        try:
            return Decimal(cleaned)
        except InvalidOperation:
            return None

    return None


def extract_image_url(images: Any) -> str | None:
    """Extract the first usable image URL from the Amazon image structure."""
    if not isinstance(images, list):
        return None

    for image in images:
        if isinstance(image, str):
            image = image.strip()
            if image:
                return image

        elif isinstance(image, dict):
            for key in ("large", "hi_res", "thumb", "url"):
                value = image.get(key)

                if isinstance(value, str) and value.strip():
                    return value.strip()

    return None


def normalize_product(record: dict[str, Any]) -> dict[str, Any] | None:
    """Convert one Amazon metadata record into our Product schema."""

    parent_asin = record.get("parent_asin")

    if not isinstance(parent_asin, str) or not parent_asin.strip():
        return None

    parent_asin = parent_asin.strip()

    title = normalize_text(record.get("title"))

    if not title:
        return None

    description = normalize_text(record.get("description"))

    main_category = normalize_text(record.get("main_category"))

    store = normalize_text(record.get("store"))

    average_rating = record.get("average_rating")
    if average_rating is not None:
        try:
            average_rating = Decimal(str(average_rating))
        except (InvalidOperation, ValueError, TypeError):
            average_rating = None

    rating_number = record.get("rating_number")
    if rating_number is not None:
        try:
            rating_number = int(rating_number)
        except (ValueError, TypeError):
            rating_number = None

    return {
        "parent_asin": parent_asin,
        "title": title,
        "description": description,
        "main_category": main_category,
        "store": store,
        "price": parse_price(record.get("price")),
        "average_rating": average_rating,
        "rating_number": rating_number,
        "features": normalize_list(record.get("features")),
        "categories": normalize_list(record.get("categories")),
        "details": normalize_dict(record.get("details")),
        "image_url": extract_image_url(record.get("images")),
    }


def get_or_create_catalog_version(session) -> CatalogVersion:
    """Create or reuse the Day 1 catalogue version."""

    catalog_version = session.scalar(
        select(CatalogVersion).where(
            CatalogVersion.version == CATALOG_VERSION
        )
    )

    if catalog_version is None:
        catalog_version = CatalogVersion(
            version=CATALOG_VERSION,
        )
        session.add(catalog_version)
        session.flush()

    return catalog_version


def load_products() -> None:
    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"Catalogue file not found: {DATA_FILE}"
        )

    print(f"Catalogue file: {DATA_FILE}")
    print(f"Target products: {MAX_PRODUCTS:,}")
    print(f"Batch size: {BATCH_SIZE}")

    session = SessionLocal()

    try:
        catalog_version = get_or_create_catalog_version(session)

        # Avoid duplicate parent_asins in this run.
        seen_parent_asins: set[str] = set()

        # Also account for products already present in the database.
        existing_asins = set(
            session.scalars(
                select(Product.parent_asin)
                .where(
                    Product.catalog_version_id == catalog_version.id
                )
            ).all()
        )

        seen_parent_asins.update(existing_asins)

        batch: list[Product] = []

        processed = 0
        loaded = len(existing_asins)
        skipped = 0
        malformed = 0

        with DATA_FILE.open(
            "r",
            encoding="utf-8",
            errors="replace",
        ) as file:

            for line_number, line in enumerate(file, start=1):

                if loaded >= MAX_PRODUCTS:
                    break

                processed += 1

                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    malformed += 1
                    continue

                if not isinstance(record, dict):
                    skipped += 1
                    continue

                product_data = normalize_product(record)

                if product_data is None:
                    skipped += 1
                    continue

                parent_asin = product_data["parent_asin"]

                if parent_asin in seen_parent_asins:
                    skipped += 1
                    continue

                seen_parent_asins.add(parent_asin)

                batch.append(
                    Product(
                        **product_data,
                        catalog_version_id=catalog_version.id,
                    )
                )

                loaded += 1

                if len(batch) >= BATCH_SIZE:
                    session.add_all(batch)
                    session.commit()

                    print(
                        f"Loaded {loaded:,}/{MAX_PRODUCTS:,} "
                        f"products | processed={processed:,} "
                        f"skipped={skipped:,} "
                        f"malformed={malformed:,}"
                    )

                    batch.clear()

        if batch:
            session.add_all(batch)
            session.commit()

        print()
        print("========================================")
        print("Catalogue ingestion complete")
        print("========================================")
        print(f"Processed records : {processed:,}")
        print(f"Loaded products   : {loaded:,}")
        print(f"Skipped records   : {skipped:,}")
        print(f"Malformed JSON    : {malformed:,}")
        print(f"Catalog version   : {CATALOG_VERSION}")
        print("========================================")

    except Exception:
        session.rollback()
        raise

    finally:
        session.close()


if __name__ == "__main__":
    load_products()