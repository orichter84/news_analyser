"""
AnthropicConnector — calls the Anthropic Messages API directly.
Requires ANTHROPIC_API_KEY environment variable.
"""

import os
from typing import Any, Dict

import yaml

try:
    import anthropic as _anthropic
except ImportError:
    _anthropic = None

from .base import LLMConnector


class AnthropicConnector(LLMConnector):
    """Connector for the Anthropic Messages API."""

    def __init__(self) -> None:
        if _anthropic is None:
            raise ImportError("anthropic package is not installed. Run: pip install anthropic")
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "ANTHROPIC_API_KEY not set. Export it before starting the server."
            )
        self._client = _anthropic.Anthropic(api_key=api_key)

    @property
    def name(self) -> str:
        return "anthropic"

    def generate(
        self,
        system_prompt: str,
        input_data: Dict[str, Any],
        model: str,
        temperature: float,
        max_tokens: int,
    ) -> str:
        user_content = yaml.safe_dump(input_data, sort_keys=False, allow_unicode=True)
        response = self._client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": user_content}],
        )
        return response.content[0].text
