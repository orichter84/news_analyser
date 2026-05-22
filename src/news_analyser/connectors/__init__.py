"""
Connector plugin registry.

Usage:
    from .connectors import load_connector
    connector = load_connector("openai")
"""

from functools import partial

from .base import LLMConnector
from .anthropic_connector import AnthropicConnector
from .cli_connector import CLIConnector
from .openai_connector import OpenAIConnector
from .M365CopilotConnector import M365CopilotConnector

_REGISTRY = {
    "anthropic": AnthropicConnector,
    "cli": CLIConnector,
    "openai": OpenAIConnector,
    "copilot": partial(
        OpenAIConnector,
        api_key_env="GITHUB_TOKEN",
        base_url="https://api.githubcopilot.com",
        connector_name="copilot",
    ),
    "lm_studio": partial(
        OpenAIConnector,
        api_key_env="LM_STUDIO_API_KEY",
        api_key_default="lm-studio",
        base_url="http://localhost:1234/v1",
        connector_name="lm_studio",
        use_system_role=False,
    ),
    "m365_copilot": M365CopilotConnector,
}


def load_connector(name: str) -> LLMConnector:
    """Instantiate a connector by name.

    Raises:
        ValueError: If connector name is unknown
    """
    cls = _REGISTRY.get(name)
    if cls is None:
        available = ", ".join(_REGISTRY.keys())
        raise ValueError(f"Unknown connector '{name}'. Available: {available}")
    return cls()


__all__ = [
    "LLMConnector",
    "AnthropicConnector",
    "CLIConnector",
    "OpenAIConnector",
    "M365CopilotConnector",
    "load_connector",
]
