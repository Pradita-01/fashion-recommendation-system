from __future__ import annotations

import re
from typing import Any


STOPWORDS = {
    "a",
    "an",
    "and",
    "for",
    "from",
    "in",
    "into",
    "of",
    "on",
    "the",
    "to",
    "with",
    "my",
    "me",
    "i",
    "need",
    "want",
    "looking",
    "find",
    "show",
}


# ---------------------------------------------------------------------------
# Fashion-aware seasonal vocabulary
# ---------------------------------------------------------------------------
#
# These are deliberately conservative.
# We use them as ranking evidence, NOT as hard filters.
#
# This means a product containing a potentially conflicting term can still
# appear if its semantic relevance is strong enough.
# ---------------------------------------------------------------------------

SEASON_TERMS: dict[str, set[str]] = {
    "summer": {
        "summer",
        "beach",
        "breathable",
        "cool",
        "lightweight",
        "sundress",
        "sundresses",
        "tank",
        "sleeveless",
        "shorts",
    },
    "winter": {
        "winter",
        "sweater",
        "sweaters",
        "hoodie",
        "hoodies",
        "fleece",
        "thermal",
        "thermals",
        "parka",
        "parkas",
        "coat",
        "coats",
        "jacket",
        "jackets",
        "snow",
        "ski",
        "wool",
    },
    "spring": {
        "spring",
        "lightweight",
        "breathable",
        "cardigan",
        "floral",
    },
    "fall": {
        "fall",
        "autumn",
        "cardigan",
        "sweater",
        "jacket",
        "layer",
        "layers",
    },
}


# ---------------------------------------------------------------------------
# Attribute vocabulary
# ---------------------------------------------------------------------------

ATTRIBUTE_TERMS: dict[str, set[str]] = {
    "lightweight": {
        "lightweight",
        "light",
        "thin",
        "weightless",
    },
    "comfortable": {
        "comfortable",
        "comfort",
        "comfy",
        "soft",
        "relaxed",
    },
    "breathable": {
        "breathable",
        "ventilated",
        "airflow",
    },
    "casual": {
        "casual",
        "everyday",
        "relaxed",
    },
    "formal": {
        "formal",
        "dressy",
        "elegant",
        "business",
    },
}


class LightweightRanker:
    """
    Fast query-aware ranking layer applied after hybrid RRF retrieval.

    Ranking remains primarily driven by hybrid retrieval.

    Additional signals:
    - title lexical overlap
    - description lexical overlap
    - query season evidence
    - query attribute evidence
    - conflicting seasonal evidence

    This intentionally avoids an expensive cross-encoder on the live path.
    """

    SCORE_MULTIPLIER = 0.30

    # Small, controlled adjustments.
    SEASON_BOOST = 0.18
    ATTRIBUTE_BOOST = 0.10
    CONFLICT_PENALTY = 0.30

    def rank(
        self,
        query: str,
        results: list[dict[str, Any]],
        parsed_query: Any | None = None,
    ) -> list[dict[str, Any]]:
        if not results:
            return []

        query_tokens = self._meaningful_tokens(query)

        ranked_results: list[dict[str, Any]] = []

        for original_index, result in enumerate(results):
            product = result.get("product")

            lexical_score = self._lexical_score(
                query=query,
                query_tokens=query_tokens,
                product=product,
            )

            rrf_score = float(result.get("score", 0.0))

            # Existing lexical adjustment.
            adjusted_score = rrf_score * (
                1.0 + self.SCORE_MULTIPLIER * lexical_score
            )

            # Structured query-aware adjustment.
            if parsed_query is not None:
                adjusted_score *= self._structured_adjustment(
                    product=product,
                    parsed_query=parsed_query,
                )

            ranked_results.append(
                {
                    **result,
                    "score": adjusted_score,
                    "_original_index": original_index,
                }
            )

        ranked_results.sort(
            key=lambda item: (
                float(item["score"]),
                -int(item["_original_index"]),
            ),
            reverse=True,
        )

        for result in ranked_results:
            result.pop("_original_index", None)

        return ranked_results

    # -----------------------------------------------------------------------
    # Structured query ranking
    # -----------------------------------------------------------------------

    def _structured_adjustment(
        self,
        product: Any,
        parsed_query: Any,
    ) -> float:
        if product is None:
            return 1.0

        text = self._product_text(product)
        product_tokens = self._meaningful_tokens(text)

        if not product_tokens:
            return 1.0

        adjustment = 1.0

        # ---------------------------------------------------------------
        # Season
        # ---------------------------------------------------------------

        season = str(
            getattr(parsed_query, "season", None) or ""
        ).strip().casefold()

        if season:
            target_terms = SEASON_TERMS.get(
                season,
                {season},
            )

            target_matches = self._count_term_matches(
                target_terms,
                product_tokens,
            )

            if target_matches > 0:
                # One or more pieces of evidence for the requested season.
                adjustment += self.SEASON_BOOST

            # Strong conflict detection.
            conflicting_season = self._has_conflicting_season(
                season=season,
                product_tokens=product_tokens,
            )

            if conflicting_season:
                adjustment -= self.CONFLICT_PENALTY

        # ---------------------------------------------------------------
        # Attributes
        # ---------------------------------------------------------------

        attributes = getattr(
            parsed_query,
            "attributes",
            [],
        ) or []

        matched_attributes = 0

        for attribute in attributes:
            attribute_name = str(attribute).strip().casefold()

            terms = ATTRIBUTE_TERMS.get(
                attribute_name,
                {attribute_name},
            )

            if self._count_term_matches(
                terms,
                product_tokens,
            ) > 0:
                matched_attributes += 1

        if attributes:
            attribute_coverage = (
                matched_attributes / len(attributes)
            )

            adjustment += (
                self.ATTRIBUTE_BOOST
                * attribute_coverage
            )

        # Never allow this lightweight adjustment to zero-out a result.
        return max(0.55, adjustment)

    @staticmethod
    def _has_conflicting_season(
        season: str,
        product_tokens: set[str],
    ) -> bool:
        conflicts = {
            "summer": {"winter", "fall", "autumn"},
            "winter": {"summer"},
            "spring": {"winter"},
            "fall": {"summer"},
            "autumn": {"summer"},
        }

        conflicting_seasons = conflicts.get(
            season,
            set(),
        )

        for conflicting_season in conflicting_seasons:
            conflict_terms = SEASON_TERMS.get(
                conflicting_season,
                {conflicting_season},
            )

            if LightweightRanker._count_term_matches(
                conflict_terms,
                product_tokens,
            ) > 0:
                return True

        # Strong winter-specific clothing should also be penalized for
        # summer even when the word "winter" itself is absent.
        if season == "summer":
            cold_weather_terms = {
                "sweater",
                "sweaters",
                "hoodie",
                "hoodies",
                "fleece",
                "thermal",
                "thermals",
                "parka",
                "parkas",
                "snow",
                "ski",
                "wool",
            }

            if LightweightRanker._count_term_matches(
                cold_weather_terms,
                product_tokens,
            ) > 0:
                return True

        return False

    @staticmethod
    def _count_term_matches(
        terms: set[str],
        product_tokens: set[str],
    ) -> int:
        return sum(
            1
            for term in terms
            if any(
                LightweightRanker._tokens_match(
                    term,
                    product_token,
                )
                for product_token in product_tokens
            )
        )

    # -----------------------------------------------------------------------
    # Existing lexical ranking
    # -----------------------------------------------------------------------

    def _lexical_score(
        self,
        query: str,
        query_tokens: set[str],
        product: Any,
    ) -> float:
        if product is None or not query_tokens:
            return 0.0

        title = str(
            getattr(product, "title", "") or ""
        )

        description = str(
            getattr(product, "description", "") or ""
        )

        title_tokens = self._meaningful_tokens(title)
        description_tokens = self._meaningful_tokens(description)

        if not title_tokens:
            return 0.0

        title_matches = self._matching_token_count(
            query_tokens,
            title_tokens,
        )

        description_matches = self._matching_token_count(
            query_tokens,
            description_tokens,
        )

        title_coverage = (
            title_matches / len(query_tokens)
        )

        description_coverage = (
            description_matches / len(query_tokens)
            if description_tokens
            else 0.0
        )

        phrase_bonus = 0.0

        normalized_query = " ".join(
            self._normalize_token(token)
            for token in self._tokens(query)
        ).strip()

        normalized_title = " ".join(
            self._normalize_token(token)
            for token in self._tokens(title)
        ).strip()

        if (
            normalized_query
            and normalized_title
            and normalized_query in normalized_title
        ):
            phrase_bonus = 0.25

        score = (
            0.75 * title_coverage
            + 0.25 * description_coverage
            + phrase_bonus
        )

        return min(score, 1.0)

    @staticmethod
    def _matching_token_count(
        query_tokens: set[str],
        product_tokens: set[str],
    ) -> int:
        matches = 0

        for query_token in query_tokens:
            if any(
                LightweightRanker._tokens_match(
                    query_token,
                    product_token,
                )
                for product_token in product_tokens
            ):
                matches += 1

        return matches

    @staticmethod
    def _tokens_match(
        left: str,
        right: str,
    ) -> bool:
        if left == right:
            return True

        if len(left) >= 4 and len(right) >= 4:
            if left.endswith("s") and left[:-1] == right:
                return True

            if right.endswith("s") and right[:-1] == left:
                return True

            if left.endswith("es") and left[:-2] == right:
                return True

            if right.endswith("es") and right[:-2] == left:
                return True

        return False

    # -----------------------------------------------------------------------
    # Product text
    # -----------------------------------------------------------------------

    @staticmethod
    def _product_text(product: Any) -> str:
        title = str(
            getattr(product, "title", "") or ""
        )

        description = str(
            getattr(product, "description", "") or ""
        )

        return f"{title} {description}"

    # -----------------------------------------------------------------------
    # Tokenization
    # -----------------------------------------------------------------------

    @classmethod
    def _meaningful_tokens(
        cls,
        text: str,
    ) -> set[str]:
        return {
            cls._normalize_token(token)
            for token in cls._tokens(text)
            if cls._normalize_token(token)
            and cls._normalize_token(token) not in STOPWORDS
        }

    @staticmethod
    def _tokens(text: str) -> list[str]:
        return re.findall(
            r"\w+",
            text.casefold(),
            flags=re.UNICODE,
        )

    @staticmethod
    def _normalize_token(token: str) -> str:
        return token.strip().casefold()
