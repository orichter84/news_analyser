"""
OpenAIAdapter — calls the OpenAI Chat Completions API.

Also serves as base for OpenAI-compatible endpoints (LM Studio, GitHub Copilot).

Config keys (passed to initialize):
    model           — model name (default: "gpt-4o")
    temperature     — sampling temperature (default: 0.2)
    max_tokens      — maximum output tokens (default: 2048)
    api_key_env     — ENV var name for the API key (default: "OPENAI_API_KEY")
    api_key_default — fallback key value when ENV var is absent (default: None)
    base_url        — custom endpoint URL, e.g. for LM Studio (default: None)
    adapter_name    — reported name (default: "openai")
    use_system_role — whether to use a separate system message (default: True)
                      Set False for backends that fold system+user into one message.

ENV fallbacks for non-security values (if not in config dict):
    LLM_MODEL        — provider-agnostic model name (preferred)
    OPENAI_MODEL     — legacy alias (backward compat)
    LLM_TEMPERATURE  — sampling temperature
    LLM_MAX_TOKENS   — max output tokens
"""

import json
import os
from typing import Any, Dict, List

try:
    import openai as _openai
except ImportError:
    _openai = None

from .base import LLMAdapter


class OpenAIAdapter(LLMAdapter):
    """Adapter for the OpenAI Chat Completions API and compatible endpoints."""

    _DEFAULTS: dict = {
        "model":           "gpt-4o",
        "temperature":     0.2,
        "max_tokens":      2048,
        "api_key_env":     "OPENAI_API_KEY",
        "api_key_default": None,
        "base_url":        None,
        "adapter_name":    "openai",
        "use_system_role": True,
    }

    @property
    def name(self) -> str:
        return self._adapter_name

    def initialize(self, config: dict) -> None:
        if _openai is None:
            raise ImportError(
                "openai package ist nicht installiert. Ausführen: pip install openai"
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

        self._adapter_name: str   = config.get("adapter_name",    self._DEFAULTS["adapter_name"])
        self._use_system_role: bool = config.get("use_system_role", self._DEFAULTS["use_system_role"])
        base_url: str | None      = config.get("base_url",        self._DEFAULTS["base_url"])

        api_key_env: str          = config.get("api_key_env",     self._DEFAULTS["api_key_env"])
        api_key_default: str | None = config.get("api_key_default", self._DEFAULTS["api_key_default"])

        # ---- Schritt 2: Sicherheitskritische Werte aus ENV ----
        api_key = os.environ.get(api_key_env) if api_key_env else None
        if not api_key:
            api_key = api_key_default
        if not api_key:
            raise EnvironmentError(
                f"Umgebungsvariable '{api_key_env}' ist nicht gesetzt "
                "und kein Standardwert (api_key_default) konfiguriert."
            )

        client_kwargs: dict = {"api_key": api_key}
        if base_url:
            client_kwargs["base_url"] = base_url
        self._client = _openai.OpenAI(**client_kwargs)

    def generate(
        self,
        system_prompt: str,
        input_data: Dict[str, Any],
    ) -> str:
        user_content = json.dumps(input_data, ensure_ascii=False, indent=2)
        messages: List[Any] = (
            [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_content},
            ]
            if self._use_system_role
            else [
                {"role": "user", "content": f"{system_prompt}\n\n{user_content}"},
            ]
        )
        response = self._client.chat.completions.create(
            model=self._model,
            max_tokens=self._max_tokens,
            temperature=self._temperature,
            messages=messages,
        )
        return response.choices[0].message.content.strip()
