from unittest.mock import Mock

from query_understanding.parser import ParsedQuery


def test_parsed_query_response_shape() -> None:
    """Verify the structured query can be represented by the API schema."""

    parsed = ParsedQuery(
        intent="outfit_recommendation",
        category=None,
        occasion="beach",
        season="summer",
        attributes=["comfortable"],
        language="en",
        normalized_query="comfortable summer beach outfit",
    )

    data = parsed.model_dump()

    assert data["intent"] == "outfit_recommendation"
    assert data["occasion"] == "beach"
    assert data["season"] == "summer"
    assert data["attributes"] == ["comfortable"]
    assert data["normalized_query"] == (
        "comfortable summer beach outfit"
    )