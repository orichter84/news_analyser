"""
LLMAdapter — abstract base class for all adapter plugins.

Each adapter wraps a specific LLM backend (Anthropic API, Claude CLI, LM Studio, …)
behind a uniform interface. The pipeline only depends on this interface,
never on a concrete adapter.

Lifecycle:
    1. adapter = SomeAdapter()           # no-arg constructor
    2. adapter.initialize(config)        # two-phase init:
                                         #   step 1 — non-security values from config dict
                                         #   step 2 — security-critical values from ENV
    3. result = adapter.generate(...)    # clean, config-free call

Why two phases?
    The adapter declares its own config keys (via _DEFAULTS).
    The caller passes a generic dict — no need to know constructor signatures.
    Security-critical values (API keys) never travel through the dict; they are
    always read directly from the environment using the key name from step 1.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class LLMAdapter(ABC):
    """Abstract adapter interface for LLM backends."""

    @abstractmethod
    def initialize(self, config: dict) -> None:
        """Two-phase initialisation.

        Step 1 — non-security-critical values:
            Read from *config* dict first; fall back to environment variables;
            fall back to hardcoded defaults (documented in the concrete adapter's
            ``_DEFAULTS`` class attribute).

        Step 2 — security-critical values:
            Read the actual secret (API key, token, …) from the environment
            using the variable *name* supplied in step 1.

        Args:
            config: Adapter-specific key/value pairs.  Unknown keys are ignored.
                    See the concrete adapter's ``_DEFAULTS`` for supported keys.

        Raises:
            EnvironmentError: A required environment variable is not set.
            ImportError:      An optional backend library is not installed.
        """

    @abstractmethod
    def generate(
        self,
        system_prompt: str,
        input_data: Dict[str, Any],
    ) -> str:
        """Call the LLM and return the raw text response.

        Args:
            system_prompt: Agent system prompt (role / task description).
            input_data:    Structured input — JSON-serialised as the user message.

        Returns:
            Raw text response from the model.
        """

    @property
    @abstractmethod
    def name(self) -> str:
        """Adapter identifier (e.g. 'anthropic', 'cli', 'lm_studio')."""
