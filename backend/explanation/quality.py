from __future__ import annotations


class ExplanationQuality:
    """
    Lightweight quality gate for grounded product explanations.

    This does not decide whether a product is relevant.
    Retrieval and reranking already make that decision.

    This only decides whether an explanation is safe enough
    to expose to the user.
    """

    @staticmethod
    def validate(explanation: str | None) -> bool:
        if explanation is None:
            return False

        cleaned = explanation.strip()

        if not cleaned:
            return False

        # Avoid exposing obvious LLM uncertainty/meta commentary.
        blocked_phrases = (
            "i don't know",
            "i cannot determine",
            "i can't determine",
            "not enough information",
            "as an ai",
        )

        lowered = cleaned.lower()

        if any(
            phrase in lowered
            for phrase in blocked_phrases
        ):
            return False

        return True