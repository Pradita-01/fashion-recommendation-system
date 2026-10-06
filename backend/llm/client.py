from __future__ import annotations

from abc import ABC, abstractmethod


class LLMClient(ABC):
    """Abstract interface for LLM-backed query understanding."""

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Generate a text response from the LLM."""
        raise NotImplementedError