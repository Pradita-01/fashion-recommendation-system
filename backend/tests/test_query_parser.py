from query_understanding.parser import (
    ParsedQuery,
    QueryParser,
    fallback_parsed_query,
)


class MockLLMClient:
    """Deterministic fake LLM used for unit testing."""

    def __init__(self, response: str) -> None:
        self.response = response

    def generate(self, prompt: str) -> str:
        return self.response


class FailingLLMClient:
    """Fake LLM that simulates Gemini being unavailable."""

    def generate(self, prompt: str) -> str:
        raise RuntimeError("Simulated Gemini failure")


def test_parsed_query_valid() -> None:
    """Verify that ParsedQuery accepts valid structured data."""

    parsed = ParsedQuery(
        intent="outfit_recommendation",
        category=None,
        occasion="beach",
        season="summer",
        attributes=["comfortable"],
        language="en",
        normalized_query="comfortable summer beach outfit",
    )

    assert parsed.intent == "outfit_recommendation"
    assert parsed.category is None
    assert parsed.occasion == "beach"
    assert parsed.season == "summer"
    assert "comfortable" in parsed.attributes
    assert parsed.language == "en"
    assert parsed.normalized_query == (
        "comfortable summer beach outfit"
    )


def test_query_parser_with_mock_llm() -> None:
    """Verify parsing without depending on the real Gemini API."""

    mock_response = """
    {
        "intent": "outfit_recommendation",
        "category": "outfit",
        "occasion": "beach",
        "season": "summer",
        "attributes": ["comfortable"],
        "language": "en",
        "normalized_query": "comfortable beach outfit for summer"
    }
    """

    parser = QueryParser(
        MockLLMClient(mock_response)
    )

    parsed = parser.parse(
        "I need a comfortable beach outfit this summer."
    )

    assert isinstance(parsed, ParsedQuery)
    assert parsed.intent == "outfit_recommendation"
    assert parsed.category == "outfit"
    assert parsed.occasion == "beach"
    assert parsed.season == "summer"
    assert parsed.attributes == ["comfortable"]
    assert parsed.language == "en"
    assert parsed.normalized_query == (
        "comfortable beach outfit for summer"
    )


def test_query_parser_rejects_invalid_json() -> None:
    """Verify that malformed LLM output is rejected."""

    parser = QueryParser(
        MockLLMClient("this is not valid JSON")
    )

    try:
        parser.parse("beach outfit")
    except ValueError as exc:
        assert str(exc) == "Gemini returned invalid JSON."
    else:
        raise AssertionError(
            "Expected ValueError for invalid JSON."
        )


def test_query_parser_handles_invalid_llm_response() -> None:
    """Verify that invalid structured output is rejected."""

    mock_response = """
    {
        "intent": "search",
        "category": null,
        "occasion": null,
        "season": null,
        "attributes": [],
        "language": "en"
    }
    """

    parser = QueryParser(
        MockLLMClient(mock_response)
    )

    try:
        parser.parse("beach outfit")
    except ValueError as exc:
        assert str(exc) == (
            "Gemini returned an invalid ParsedQuery."
        )
    else:
        raise AssertionError(
            "Expected ValueError for invalid ParsedQuery."
        )


def test_fallback_parsed_query() -> None:
    """Verify that the fallback preserves the original query."""

    query = "comfortable beach outfit for summer"

    parsed = fallback_parsed_query(query)

    assert parsed.intent == "product_search"
    assert parsed.category is None
    assert parsed.occasion is None
    assert parsed.season is None
    assert parsed.attributes == []
    assert parsed.language == "unknown"
    assert parsed.normalized_query == query


def test_fallback_rejects_empty_query() -> None:
    """Verify that an empty query cannot enter the fallback."""

    try:
        fallback_parsed_query("   ")
    except ValueError as exc:
        assert str(exc) == "Query cannot be empty."
    else:
        raise AssertionError(
            "Expected ValueError for empty query."
        )


def test_query_parser_handles_llm_failure() -> None:
    """Verify that LLM failures are surfaced to the caller."""

    parser = QueryParser(FailingLLMClient())

    try:
        parser.parse("comfortable beach outfit")
    except RuntimeError as exc:
        assert str(exc) == "Gemini query understanding failed."
    else:
        raise AssertionError(
            "Expected RuntimeError for LLM failure."
        )