from __future__ import annotations

from typing import Any

from shared.models import Product


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