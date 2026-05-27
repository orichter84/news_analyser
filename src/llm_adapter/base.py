"""
LLMAdapter — abstract base class for all adapter plugins.

Each adapter wraps a specific LLM backend (Anthropic API, Claude CLI, LM Studio, …)
behind a uniform interface. The pipeline only depends on this interface,
never on a concrete adapter.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class LLMAdapter(ABC):
    """Abstract adapter interface for LLM backends."""

    @abstractmethod
    def generate(
        self,
        system_prompt: str,
        input_data: Dict[str, Any],
        model: str,
        temperature: float,
        max_tokens: int,
    ) -> str:
        """Call the LLM and return the raw text response.

        Args:
            system_prompt: Agent system prompt
            input_data:    Structured input (will be JSON-serialised as user message)
            model:         Model identifier
            temperature:   Sampling temperature
            max_tokens:    Maximum tokens in the response

        Returns:
            Raw text response from the model
        """

    @property
    @abstractmethod
    def name(self) -> str:
        """Adapter identifier (e.g. 'anthropic', 'cli', 'lm_studio')."""
