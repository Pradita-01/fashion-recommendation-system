from __future__ import annotations

import logging
import os
import random
import time
from typing import Any

from google import genai

from llm.client import LLMClient
from search_api.services.parse_schema import ParsedQuery


logger = logging.getLogger(__name__)


class GeminiClient(LLMClient):
    """
    Gemini client for the Fashion Search query parser.

    Responsibilities:
    - Call Gemini with structured output.
    - Return ParsedQuery, as expected by QueryParser.
    - Retry transient 503/500 errors.
    - Skip exhausted daily quotas.
    - Fall back to alternate Gemini models.
    """

    PRIMARY_MODEL = os.getenv(
        "GEMINI_MODEL",
        "gemini-3.5-flash",
    )

    FALLBACK_MODELS = [
        "gemini-3.5-flash-lite",
        "gemini-3.1-flash-lite",
    ]

    MAX_RETRIES_PER_MODEL = 2
    INITIAL_RETRY_DELAY_SECONDS = 2
    MAX_RETRY_DELAY_SECONDS = 16

    def __init__(self) -> None:
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY environment variable is not set."
            )

        self.client = genai.Client(api_key=api_key)

    @property
    def models(self) -> list[str]:
        """Primary model followed by unique fallback models."""

        models: list[str] = []

        for model in [
            self.PRIMARY_MODEL,
            *self.FALLBACK_MODELS,
        ]:
            if model not in models:
                models.append(model)

        return models

    def generate(self, prompt: str) -> str:
        """
        Generate plain text.

        Kept for compatibility with the LLMClient interface.
        """

        response = self._call_gemini(
            prompt=prompt,
            structured=False,
        )

        if response.text is None:
            raise RuntimeError(
                "Gemini returned an empty response."
            )

        return response.text

    def generate_structured(
        self,
        prompt: str,
        response_schema: dict[str, Any] | None = None,
    ) -> ParsedQuery:
        """
        Generate a structured ParsedQuery.

        IMPORTANT:
        QueryParser expects a ParsedQuery object, not a dict.
        """

        response = self._call_gemini(
            prompt=prompt,
            structured=True,
            response_schema=response_schema,
        )

        if response.text is None:
            raise RuntimeError(
                "Gemini returned an empty structured response."
            )

        parsed = ParsedQuery.model_validate_json(
            response.text
        )

        logger.info(
            "Gemini parsed query: language=%s normalized_query=%s",
            parsed.language,
            parsed.normalized_query,
        )

        return parsed

    def _call_gemini(
        self,
        prompt: str,
        structured: bool,
        response_schema: dict[str, Any] | None = None,
    ):
        """
        Call Gemini using model failover.
        """

        errors: list[str] = []

        for model in self.models:
            logger.info(
                "Trying Gemini model: %s",
                model,
            )

            for attempt in range(
                self.MAX_RETRIES_PER_MODEL + 1
            ):
                try:
                    config = None

                    if structured:
                        config = {
                            "response_mime_type": "application/json",
                        }

                        if response_schema:
                            config["response_schema"] = response_schema

                    response = (
                        self.client.models.generate_content(
                            model=model,
                            contents=prompt,
                            config=config,
                        )
                    )

                    logger.info(
                        "Gemini request succeeded using model: %s",
                        model,
                    )

                    return response

                except Exception as exc:
                    error_text = str(exc)

                    errors.append(
                        f"{model}: {error_text}"
                    )

                    # Daily quota:
                    # do NOT waste retries.
                    if self._is_daily_quota_error(
                        error_text
                    ):
                        logger.warning(
                            "Daily quota exhausted for %s. "
                            "Moving to next Gemini model.",
                            model,
                        )
                        break

                    # Temporary service/capacity errors:
                    # retry with exponential backoff.
                    if self._is_retryable_error(
                        error_text
                    ):
                        if attempt < self.MAX_RETRIES_PER_MODEL:
                            delay = min(
                                self.INITIAL_RETRY_DELAY_SECONDS
                                * (2 ** attempt),
                                self.MAX_RETRY_DELAY_SECONDS,
                            )

                            delay += random.uniform(
                                0,
                                0.5,
                            )

                            logger.warning(
                                "Gemini %s failed. "
                                "Retrying in %.1f seconds.",
                                model,
                                delay,
                            )

                            time.sleep(delay)
                            continue

                    logger.warning(
                        "Gemini model %s failed: %s",
                        model,
                        error_text,
                    )

                    break

        raise RuntimeError(
            "All configured Gemini models failed. "
            + " | ".join(errors)
        )

    @staticmethod
    def _is_retryable_error(
        error_text: str,
    ) -> bool:
        """Return True for transient API failures."""

        markers = (
            "429",
            "RESOURCE_EXHAUSTED",
            "500",
            "INTERNAL",
            "503",
            "UNAVAILABLE",
            "504",
            "DEADLINE_EXCEEDED",
            "deadline exceeded",
        )

        error_lower = error_text.lower()

        return any(
            marker.lower() in error_lower
            for marker in markers
        )

    @staticmethod
    def _is_daily_quota_error(
        error_text: str,
    ) -> bool:
        """
        Detect daily free-tier quota exhaustion.

        Daily quota should not be retried repeatedly.
        """

        markers = (
            "GenerateRequestsPerDay",
            "PerDayPerProject",
            "FreeTier",
            "per day",
        )

        error_lower = error_text.lower()

        return any(
            marker.lower() in error_lower
            for marker in markers
        )