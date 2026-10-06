from __future__ import annotations

from pathlib import Path

from search_api.services.parse_schema import ParsedQuery
from shared.cache import RedisCache
from shared.llm.gemini_client import GeminiClient


PROMPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "prompts"
    / "parse_query.md"
)


class QueryParser:
    """
    Gemini-powered fashion query parser with Redis caching.

    Failure policy:
    - Redis failure must not break parsing.
    - Gemini failure must be handled by the caller.
    """

    def __init__(
        self,
        gemini_client: GeminiClient | None = None,
        cache: RedisCache | None = None,
    ) -> None:

        self.gemini = gemini_client or GeminiClient()
        self.cache = cache or RedisCache()

        self.prompt_template = PROMPT_PATH.read_text(
            encoding="utf-8"
        )

    def parse(
        self,
        query: str,
    ) -> ParsedQuery:

        query = query.strip()

        if not query:
            raise ValueError(
                "Query cannot be empty."
            )

        # ---------------------------------------------------------------
        # Redis cache
        # ---------------------------------------------------------------

        try:
            cached = self.cache.get_json(query)

            if cached is not None:
                return ParsedQuery.model_validate(cached)

        except Exception:
            # Cache is an optimization.
            # A cache failure must never break search.
            pass

        # ---------------------------------------------------------------
        # Gemini
        # ---------------------------------------------------------------

        prompt = self.prompt_template.replace(
            "{{USER_QUERY}}",
            query,
        )

        parsed = self.gemini.generate_structured(
            prompt=prompt,
            response_schema=ParsedQuery,
        )

        # ---------------------------------------------------------------
        # Defensive normalization
        # ---------------------------------------------------------------

        parsed.normalized_query = (
            parsed.normalized_query.strip()
            or query
        )

        parsed.attributes = [
            str(attribute).strip()
            for attribute in parsed.attributes
            if str(attribute).strip()
        ]

        # ---------------------------------------------------------------
        # Cache
        # ---------------------------------------------------------------

        try:
            self.cache.set_json(
                query,
                parsed.model_dump(),
            )
        except Exception:
            # Again, cache failure must not break search.
            pass

        return parsed
