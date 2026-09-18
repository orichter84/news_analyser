"""news_analyser package — loads .env on first import."""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / ".env")

import llm_adapter

# Gemini via OpenAI-compatible endpoint — nutzt OPENAI_API_KEY.
# Überschreibbar via GEMINI_MODEL (providerspezifisch statt LLM_MODEL/OPENAI_MODEL,
# die auch andere Provider mitbeeinflussen würden — siehe Kommentar bei "cli" unten).
llm_adapter.register_adapter("gemini", llm_adapter.OpenAIAdapter, {
    "api_key_env":  "OPENAI_API_KEY",
    "base_url":     "https://generativelanguage.googleapis.com/v1beta/openai/",
    "adapter_name": "gemini",
    "model":        os.environ.get("GEMINI_MODEL", "gemini-2.5-flash"),
    "max_tokens":   8192,
})

# Mistral via OpenAI-kompatiblen Endpoint — nutzt MISTRAL_API_KEY.
# Welche Modelle verfügbar sind, hängt vom Subscription-Tier ab (GET /v1/models
# mit dem eigenen Key prüfen); mistral-large-latest ist z.B. auf dem
# kostenfreien Tier nicht freigeschaltet, mistral-medium-latest/-small-latest schon.
# Überschreibbar via MISTRAL_MODEL (providerspezifisch, siehe Kommentar bei "cli" unten).
llm_adapter.register_adapter("mistral", llm_adapter.OpenAIAdapter, {
    "api_key_env":  "MISTRAL_API_KEY",
    "base_url":     "https://api.mistral.ai/v1",
    "adapter_name": "mistral",
    "model":        os.environ.get("MISTRAL_MODEL", "mistral-medium-latest"),
    "max_tokens":   8192,
})

# Claude Code CLI als Subprocess — kein API-Key nötig, CLI authentifiziert sich
# eigenständig. Modell hier fest im Projekt verankert statt über das
# providerübergreifende LLM_MODEL/OPENAI_MODEL aus .env, damit ein für
# copilot_cli gesetztes Modell nicht versehentlich hier landet (siehe
# docs/environments/local.md, Option A/G). Überschreibbar via CLAUDE_CLI_MODEL.
llm_adapter.register_adapter("cli", llm_adapter.CLIAdapter, {
    "model": os.environ.get("CLAUDE_CLI_MODEL", "claude-opus-4-5"),
})

# GitHub Copilot CLI (`@github/copilot`) als Subprocess — Auth über `copilot`/
# `/login` oder headless via COPILOT_GITHUB_TOKEN/GH_TOKEN/GITHUB_TOKEN.
# Eigene Adapter-Klasse (kein Drop-in über CLAUDE_CLI_PATH), siehe
# copilot_cli_adapter.py für Details zu Tool-Sperre und Session-Cleanup.
# Modell ebenfalls fest im Projekt verankert statt über LLM_MODEL/OPENAI_MODEL
# aus .env (siehe Kommentar bei "cli" oben) — überschreibbar via COPILOT_MODEL.
from .copilot_cli_adapter import CopilotCliAdapter
llm_adapter.register_adapter("copilot_cli", CopilotCliAdapter, {
    "model": os.environ.get("COPILOT_MODEL", "gemini-3.8-flash"),
})
