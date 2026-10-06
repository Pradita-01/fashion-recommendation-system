from __future__ import annotations

import os
import time

from google import genai

from llm.client import LLMClient


class GeminiClient(LLMClient):
    MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
    

    MAX_RETRIES = 2
    RETRY_DELAY_SECONDS = 2

    def __init__(self) -> None:
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY environment variable is not set."
            )

        self.client = genai.Client(api_key=api_key)

    def generate(self, prompt: str) -> str:
        """Generate a plain-text response from Gemini."""

        last_exception: Exception | None = None

        for attempt in range(self.MAX_RETRIES + 1):
            try:
                response = self.client.models.generate_content(
                    model=self.MODEL_NAME,
                    contents=prompt,
                )

                if response.text is None:
                    raise RuntimeError(
                        "Gemini returned an empty response."
                    )

                return response.text

            except Exception as exc:
                last_exception = exc

                if attempt >= self.MAX_RETRIES:
                    break

                time.sleep(self.RETRY_DELAY_SECONDS)

        raise RuntimeError(
            "Gemini request failed after retries."
        ) from last_exception