"""
AnthropicAdapter — calls the Anthropic Messages API directly.

Config keys (passed to initialize):
    model       — model name (default: "claude-opus-4-5")
    temperature — sampling temperature (default: 0.2)
    max_tokens  — maximum output tokens (default: 2048)
    api_key_env — name of the ENV var that holds the API key
                  (default: "ANTHROPIC_API_KEY")

ENV fallbacks for non-security values (if not in config dict):
    LLM_MODEL        — provider-agnostic model name (preferred)
    OPENAI_MODEL     — legacy alias (backward compat)
    LLM_TEMPERATURE  — sampling temperature
    LLM_MAX_TOKENS   — max output tokens
"""

import json
import os
from typing import Any, Dict

try:
    import anthropic as _anthropic
except ImportError:
    _anthropic = None

from .base import LLMAdapter


class AnthropicAdapter(LLMAdapter):
    """Adapter for the Anthropic Messages API."""

    _DEFAULTS: dict = {
        "model":       "claude-opus-4-5",
        "temperature": 0.2,
        "max_tokens":  2048,
        "api_key_env": "ANTHROPIC_API_KEY",
    }

    @property
    def name(self) -> str:
        return "anthropic"

    @property
    def model(self) -> str:
        return self._model

    def initialize(self, config: dict) -> None:
        if _anthropic is None:
            raise ImportError(
                "anthropic package ist nicht installiert. Ausführen: pip install anthropic"
            )

        # ---- Schritt 1: Nicht-sicherheitskritische Konfiguration ----
        # Reihenfolge: Konfigurationsliste → Umgebungsvariable → Standardwert

        model = config.get("model")
        if not model:
            model = os.environ.get("LLM_MODEL") or os.environ.get("OPENAI_MODEL")
        self._model: str = model or self._DEFAULTS["model"]

        temp_raw = config.get("temperature")
        if temp_raw is None:
            temp_raw = os.environ.get("LLM_TEMPERATURE")
        self._temperature: float = (
            float(temp_raw) if temp_raw is not None else self._DEFAULTS["temperature"]
        )

        tokens_raw = config.get("max_tokens")
        if tokens_raw is None:
            tokens_raw = os.environ.get("LLM_MAX_TOKENS")
        self._max_tokens: int = (
            int(tokens_raw) if tokens_raw is not None else self._DEFAULTS["max_tokens"]
        )

        api_key_env: str = config.get("api_key_env", self._DEFAULTS["api_key_env"])

        # ---- Schritt 2: Sicherheitskritische Werte aus ENV ----
        api_key = os.environ.get(api_key_env)
        if not api_key:
            raise EnvironmentError(
                f"Umgebungsvariable '{api_key_env}' ist nicht gesetzt oder leer."
            )
        self._client = _anthropic.Anthropic(api_key=api_key)

    def generate(
        self,
        system_prompt: str,
        input_data: Dict[str, Any],
    ) -> str:
        user_content = json.dumps(input_data, ensure_ascii=False, indent=2)
        response = self._client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            temperature=self._temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": user_content}],
        )
        text_block = next((b for b in response.content if b.type == "text"), None)
        if text_block is None:
            raise RuntimeError("Anthropic response enthielt keinen Text-Block.")
        return text_block.text
