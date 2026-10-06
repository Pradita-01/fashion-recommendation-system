import pytest

from llm.gemini import GeminiClient
from query_understanding.parser import ParsedQuery, QueryParser


@pytest.mark.integration
def test_real_gemini_query_parser() -> None:
    """Verify the complete parser against the real Gemini API."""

    client = GeminiClient()
    parser = QueryParser(client)

    parsed = parser.parse(
        "I need a comfortable beach outfit this summer."
    )

    assert isinstance(parsed, ParsedQuery)
    assert parsed.intent
    assert parsed.language == "en"
    assert parsed.normalized_query