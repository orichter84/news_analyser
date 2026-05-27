"""
LLMConnector — abstract base class for all connector plugins.

Each connector wraps a specific LLM backend (Anthropic API, Claude CLI, Ollama, …)
behind a uniform interface. The pipeline only depends on this interface,
never on a concrete connector.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class LLMConnector(ABC):
    """Abstract connector interface for LLM backends."""

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
            input_data:    Structured input (will be YAML-serialised as user message)
            model:         Model identifier
            temperature:   Sampling temperature
            max_tokens:    Maximum tokens in the response

        Returns:
            Raw text response from the model
        """

    @property
    @abstractmethod
    def name(self) -> str:
        """Connector identifier (e.g. 'anthropic', 'cli', 'ollama')."""
