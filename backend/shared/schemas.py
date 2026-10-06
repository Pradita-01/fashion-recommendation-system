from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


# ---------------------------------------------------------------------------
# Product
# ---------------------------------------------------------------------------

class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    parent_asin: str
    title: str
    description: str | None
    main_category: str | None
    store: str | None
    price: Decimal | None
    average_rating: Decimal | None
    rating_number: int | None
    features: list | None
    categories: list | None
    details: dict | None
    image_url: str | None
    catalog_version_id: int
    created_at: datetime


# ---------------------------------------------------------------------------
# Product list
# ---------------------------------------------------------------------------

class ProductListResponse(BaseModel):
    items: list[ProductResponse]
    total: int


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

class SearchResult(BaseModel):
    product: ProductResponse
    score: float


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]
    page: int
    page_size: int
    total: int
    has_next: bool


# ---------------------------------------------------------------------------
# Day 3 / Gemini schemas
#
# These can remain because Gemini/query-understanding is still part of
# the project and may be used later for evaluation or an advanced mode.
# ---------------------------------------------------------------------------

class ParsedQueryResponse(BaseModel):
    intent: str
    category: str | None
    occasion: str | None
    season: str | None
    attributes: list[str]
    language: str
    normalized_query: str