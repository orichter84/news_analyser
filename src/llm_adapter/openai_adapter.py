"""
OpenAIAdapter — calls the OpenAI Chat Completions API.
Requires OPENAI_API_KEY environment variable.

Also serves as base for OpenAI-compatible endpoints (LM Studio, GitHub Copilot).
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
    """Adapter for the OpenAI Chat Completions API."""

    def __init__(
        self,
        api_key_env: str = "OPENAI_API_KEY",
        api_key_default: str | None = None,
        base_url: str | None = None,
        adapter_name: str = "openai",
        use_system_role: bool = True,
    ) -> None:
        if _openai is None:
            raise ImportError("openai package is not installed. Run: pip install openai")
        api_key = os.environ.get(api_key_env) or api_key_default
        if not api_key:
            raise EnvironmentError(
                f"{api_key_env} not set. Export it before starting the server."
            )
        self._adapter_name = adapter_name
        self._use_system_role = use_system_role
        self._client = _openai.OpenAI(api_key=api_key, base_url=base_url)

    @property
    def name(self) -> str:
        return self._adapter_name

    def generate(
        self,
        system_prompt: str,
        input_data: Dict[str, Any],
        model: str,
        temperature: float,
        max_tokens: int,
    ) -> str:
        user_content = json.dumps(input_data, ensure_ascii=False, indent=2)
        messages: List[Any] = (
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ]
            if self._use_system_role
            else [
                {"role": "user", "content": f"{system_prompt}\n\n{user_content}"},
            ]
        )
        response = self._client.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=messages,
        )
        return response.choices[0].message.content.strip()
