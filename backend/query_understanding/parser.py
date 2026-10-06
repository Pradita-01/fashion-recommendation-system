from __future__ import annotations

import json

from llm.client import LLMClient
from pydantic import BaseModel, Field


class ParsedQuery(BaseModel):
    """Structured representation of a user's fashion search query."""

    intent: str
    category: str | None = None
    occasion: str | None = None
    season: str | None = None
    attributes: list[str] = Field(default_factory=list)
    language: str
    normalized_query: str


class QueryParser:
    """Convert a natural-language fashion query into structured intent."""

    def __init__(self, llm_client: LLMClient) -> None:
        self.llm_client = llm_client

    def parse(self, query: str) -> ParsedQuery:
        """
        Parse a user's natural-language fashion query.

        Gemini is responsible for understanding the query.
        Pydantic is responsible for validating the structure.
        """

        cleaned_query = query.strip()

        if not cleaned_query:
            raise ValueError("Query cannot be empty.")

        prompt = self._build_prompt(cleaned_query)

        try:
            response = self.llm_client.generate(prompt)
        except Exception as exc:
            raise RuntimeError(
                "Gemini query understanding failed."
            ) from exc

        try:
            data = json.loads(response)
        except json.JSONDecodeError as exc:
            raise ValueError(
                "Gemini returned invalid JSON."
            ) from exc

        try:
            parsed = ParsedQuery.model_validate(data)
        except Exception as exc:
            raise ValueError(
                "Gemini returned an invalid ParsedQuery."
            ) from exc

        # Preserve the user's original intent if Gemini somehow
        # returns an empty normalized query.
        if not parsed.normalized_query.strip():
            parsed.normalized_query = cleaned_query

        return parsed

    @staticmethod
    def _build_prompt(query: str) -> str:
        """Build the structured query-understanding prompt."""

        return f"""
You are a fashion search query-understanding system.

Your task is to analyze the user's fashion search query
and return ONLY valid JSON.

Do not recommend products.

Do not invent preferences, constraints, brands,
categories, colors, materials, prices, occasions,
or other information that the user did not provide.

Only extract information explicitly stated or
strongly supported by the user's query.

Return exactly this JSON structure:

{{
  "intent": "string",
  "category": "string or null",
  "occasion": "string or null",
  "season": "string or null",
  "attributes": ["string"],
  "language": "string",
  "normalized_query": "string"
}}

Rules:

1. "intent" describes what the user is trying to accomplish.

2. "category" should contain an explicitly requested
   product category when present.

3. "occasion" should contain an explicitly stated
   use or occasion when present.

4. "season" should contain an explicitly stated season
   when present.

5. "attributes" should contain descriptive preferences
   explicitly expressed by the user.

6. "language" should be the ISO 639-1 language code
   when possible.

7. "normalized_query" should be a concise representation
   of the user's original shopping intent suitable for
   semantic retrieval.

8. Preserve all meaningful words from the user's original
   shopping intent.

9. Preserve normal word boundaries.

10. Do not concatenate separate words.

11. Use a normal single space between separate words.

12. Do not invent information.

13. If information is not present or cannot be supported,
    use null for nullable fields and [] for attributes.

14. Preserve the user's actual intent.

15. Return JSON only.

16. Do not wrap the JSON in markdown code fences.

17. Do not add explanations outside the JSON.

User query:

{query}
"""


def fallback_parsed_query(query: str) -> ParsedQuery:
    """
    Create a safe fallback when Gemini is unavailable.

    The original query is preserved so that the existing
    BGE-M3 semantic search can continue to operate.
    """

    cleaned_query = query.strip()

    if not cleaned_query:
        raise ValueError("Query cannot be empty.")

    return ParsedQuery(
        intent="product_search",
        category=None,
        occasion=None,
        season=None,
        attributes=[],
        language="unknown",
        normalized_query=cleaned_query,
    )