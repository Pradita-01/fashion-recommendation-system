from llm.gemini import GeminiClient


def test_gemini_generate() -> None:
    client = GeminiClient()

    response = client.generate(
        "In one short sentence, describe a comfortable beach outfit."
    )

    assert response.strip()