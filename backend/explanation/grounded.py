from __future__ import annotations

import json

from llm.client import LLMClient
from shared.models import Product


class GroundedExplanation:
    """
    Generates a grounded explanation for an already-selected product.

    Gemini explains the match.
    Gemini does not select or rank products.
    """

    def __init__(self, llm_client: LLMClient) -> None:
        self.llm_client = llm_client

    def explain(
        self,
        query: str,
        product: Product,
    ) -> str:
        if not query.strip():
            raise ValueError("Query cannot be empty.")

        prompt = self._build_prompt(
            query=query,
            product=product,
        )

        response = self.llm_client.generate(prompt)

        try:
            data = json.loads(response)
        except json.JSONDecodeError as exc:
            raise ValueError(
                "Gemini returned invalid explanation JSON."
            ) from exc

        explanation = data.get("explanation")

        if not isinstance(explanation, str):
            raise ValueError(
                "Gemini explanation is missing or invalid."
            )

        explanation = explanation.strip()

        if not explanation:
            raise ValueError(
                "Gemini returned an empty explanation."
            )

        return explanation

    @staticmethod
    def _build_prompt(
        query: str,
        product: Product,
    ) -> str:
        return f"""
You are a grounded fashion search explanation system.

Your task is to explain why an already-selected product may match
the user's search query.

IMPORTANT RULES:
- You are NOT selecting the product.
- You are NOT ranking the product.
- Do NOT invent product properties.
- Do NOT invent materials, colors, sizes, occasions,
  quality claims, or features.
- Use ONLY facts explicitly provided in the product data.
- If a useful property is not present in the product data,
  do not mention it.
- Keep the explanation concise and useful.
- Return JSON only.

User query:
{query}

Product catalogue facts:

Title:
{product.title}

Description:
{product.description or "Not available"}

Category:
{product.main_category or "Not available"}

Store:
{product.store or "Not available"}

Features:
{product.features or "Not available"}

Categories:
{product.categories or "Not available"}

Details:
{product.details or "Not available"}

Return exactly:

{{
  "explanation": "A concise explanation grounded only in the product facts."
}}
"""