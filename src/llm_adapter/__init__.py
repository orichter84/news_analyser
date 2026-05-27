"""
llm_adapter — LLM backend abstraction layer.

Provides a uniform interface (LLMAdapter) over multiple LLM backends.
New adapters only need to implement LLMAdapter.generate() and LLMAdapter.name.

Usage:
    from llm_adapter import load_adapter
    adapter = load_adapter("openai")
    response = adapter.generate(system_prompt, input_data, model, temperature, max_tokens)

Supported backends:
    openai      — OpenAI Chat Completions API (OPENAI_API_KEY)
    anthropic   — Anthropic Messages API (ANTHROPIC_API_KEY)
    cli         — Claude Code CLI via subprocess
    copilot     — GitHub Copilot via OpenAI-compatible API (GITHUB_TOKEN)
    lm_studio   — LM Studio local server (kein API-Key erforderlich)
    m365_copilot — Microsoft 365 Copilot via Graph API (M365_COPILOT_ACCESS_TOKEN)
"""

from functools import partial

from .base import LLMAdapter
from .anthropic_adapter import AnthropicAdapter
from .cli_adapter import CLIAdapter
from .openai_adapter import OpenAIAdapter
from .m365_copilot_adapter import M365CopilotAdapter

_REGISTRY = {
    "anthropic": AnthropicAdapter,
    "cli": CLIAdapter,
    "openai": OpenAIAdapter,
    "copilot": partial(
        OpenAIAdapter,
        api_key_env="GITHUB_TOKEN",
        base_url="https://api.githubcopilot.com",
        adapter_name="copilot",
    ),
    "lm_studio": partial(
        OpenAIAdapter,
        api_key_env="LM_STUDIO_API_KEY",
        api_key_default="lm-studio",
        base_url="http://localhost:1234/v1",
        adapter_name="lm_studio",
        use_system_role=False,
    ),
    "m365_copilot": M365CopilotAdapter,
}


def load_adapter(name: str) -> LLMAdapter:
    """Instantiate an adapter by name.

    Raises:
        ValueError: If adapter name is unknown.
    """
    cls = _REGISTRY.get(name)
    if cls is None:
        available = ", ".join(_REGISTRY.keys())
        raise ValueError(f"Unknown adapter '{name}'. Available: {available}")
    return cls()


__all__ = [
    "LLMAdapter",
    "AnthropicAdapter",
    "CLIAdapter",
    "OpenAIAdapter",
    "M365CopilotAdapter",
    "load_adapter",
]
