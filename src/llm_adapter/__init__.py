"""
llm_adapter — LLM backend abstraction layer.

Provides a uniform interface (LLMAdapter) over multiple LLM backends.
Each adapter implements initialize(config) and generate(system_prompt, input_data).

Quickstart:
    import llm_adapter

    adapter = llm_adapter.get_instance("openai")
    response = adapter.generate(system_prompt, input_data)

Custom adapter (external project):
    llm_adapter.register_adapter("gunther", GuntherAdapter, {"api_key_env": "GUNTHER_KEY"})

Advanced (isolated manager, e.g. for tests):
    manager = llm_adapter.AdapterManager()
    manager.register_adapter("gunther", GuntherAdapter, {"api_key_env": "GUNTHER_KEY"})

Built-in backends:
    openai       — OpenAI Chat Completions API (OPENAI_API_KEY)
    anthropic    — Anthropic Messages API (ANTHROPIC_API_KEY)
    cli          — Claude Code CLI via subprocess (no API key required)
    copilot      — GitHub Copilot via OpenAI-compatible API (GITHUB_TOKEN)
    lm_studio    — LM Studio local server (no API key required)
    m365_copilot — Microsoft 365 Copilot via Graph API (M365_COPILOT_ACCESS_TOKEN)

Adapter lifecycle:
    1. register_adapter(name, cls, config={})  — stores class + config dict
    2. get_instance(name)                      — creates cls(), calls initialize(config)
    3. adapter.generate(system_prompt, data)   — clean, config-free interface

Two-phase initialization (inside initialize):
    Step 1 — non-security values: config dict → ENV var → hardcoded default
    Step 2 — security-critical:   ENV[config["api_key_env"]] → API key value
"""

from .base import LLMAdapter
from .anthropic_adapter import AnthropicAdapter
from .cli_adapter import CLIAdapter
from .openai_adapter import OpenAIAdapter
from .m365_copilot_adapter import M365CopilotAdapter


class AdapterManager:
    """Registry for LLM adapters.

    Stores (class, config-dict) pairs.  get_instance() creates a fresh
    instance and calls initialize(config) — no shared state between calls.

    Can be used as an isolated instance (e.g. in tests) or via the global
    module-level API.
    """

    def __init__(self) -> None:
        self._registry: dict[str, tuple[type[LLMAdapter], dict]] = {}

    def register_adapter(
        self,
        name: str,
        cls: type[LLMAdapter],
        config: dict | None = None,
    ) -> None:
        """Register an adapter class under *name*.

        Args:
            name:   Provider name used in get_instance() (e.g. "openai", "gunther").
            cls:    Adapter class — must subclass LLMAdapter.
            config: Non-security configuration dict passed to adapter.initialize().
                    Security-critical values (API keys) must NOT be placed here;
                    put only the ENV var *name* (e.g. ``"api_key_env": "MY_KEY"``).
        """
        self._registry[name] = (cls, config or {})

    def get_instance(self, name: str) -> LLMAdapter:
        """Create and initialise a fresh adapter instance.

        Raises:
            ValueError: *name* is not registered.
            EnvironmentError: A required ENV var is missing (raised by initialize).
        """
        entry = self._registry.get(name)
        if entry is None:
            available = ", ".join(self._registry.keys())
            raise ValueError(f"Unknown adapter '{name}'. Available: {available}")
        cls, config = entry
        adapter = cls()
        adapter.initialize(config)
        return adapter


# ---------------------------------------------------------------------------
# Global manager — pre-loaded with built-in adapters
# ---------------------------------------------------------------------------

_global_manager = AdapterManager()

# Structural / adapter-specific config only.
# model, temperature, max_tokens are read by each adapter from:
#   1. this config dict (if present)
#   2. LLM_MODEL / OPENAI_MODEL / LLM_TEMPERATURE / LLM_MAX_TOKENS env vars
#   3. the adapter's hardcoded _DEFAULTS

_global_manager.register_adapter("anthropic", AnthropicAdapter, {
    "api_key_env": "ANTHROPIC_API_KEY",
})

_global_manager.register_adapter("cli", CLIAdapter)

_global_manager.register_adapter("openai", OpenAIAdapter, {
    "api_key_env": "OPENAI_API_KEY",
})

_global_manager.register_adapter("copilot", OpenAIAdapter, {
    "api_key_env":  "GITHUB_TOKEN",
    "base_url":     "https://api.githubcopilot.com",
    "adapter_name": "copilot",
})

_global_manager.register_adapter("lm_studio", OpenAIAdapter, {
    "api_key_env":     "LM_STUDIO_API_KEY",
    "api_key_default": "lm-studio",        # LM Studio accepts any non-empty key
    "base_url":        "http://localhost:1234/v1",
    "adapter_name":    "lm_studio",
    "use_system_role": False,              # LM Studio merges system+user
})

_global_manager.register_adapter("m365_copilot", M365CopilotAdapter, {
    "api_key_env": "M365_COPILOT_ACCESS_TOKEN",
})

# ---------------------------------------------------------------------------
# Module-level API — delegates to the global manager
# ---------------------------------------------------------------------------

register_adapter = _global_manager.register_adapter
get_instance     = _global_manager.get_instance


__all__ = [
    # Core class
    "LLMAdapter",
    "AdapterManager",
    # Built-in adapters
    "AnthropicAdapter",
    "CLIAdapter",
    "OpenAIAdapter",
    "M365CopilotAdapter",
    # Module-level API (global manager)
    "register_adapter",
    "get_instance",
]
