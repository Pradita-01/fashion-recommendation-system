from __future__ import annotations

from pydantic import BaseModel, Field


class ParsedQuery(BaseModel):
    """
    Structured interpretation of a user's natural-language fashion query.

    Gemini is responsible only for understanding the query.
    It must never select products or invent catalogue items.
    """

    intent: str = Field(
        default="search",
        description="The user's intent, normally 'search'.",
    )

    category: str | None = Field(
        default=None,
        description="Fashion product category if explicitly or clearly requested.",
    )

    occasion: str | None = Field(
        default=None,
        description="Occasion such as wedding, beach, casual, party, work, etc.",
    )

    season: str | None = Field(
        default=None,
        description="Season such as summer, winter, spring, or fall.",
    )

    attributes: list[str] = Field(
        default_factory=list,
        description="Descriptive preferences such as lightweight, comfortable, elegant, cotton.",
    )

    language: str = Field(
        default="en",
        description="ISO-style language code detected from the original query.",
    )

    normalized_query: str = Field(
        ...,
        description=(
            "A concise English semantic search query preserving the user's "
            "actual shopping intent and constraints."
        ),
    )
