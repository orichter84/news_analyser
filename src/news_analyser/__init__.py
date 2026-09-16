"""news_analyser package — loads .env on first import."""

from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / ".env")

import llm_adapter

# Gemini via OpenAI-compatible endpoint — nutzt OPENAI_API_KEY
llm_adapter.register_adapter("gemini", llm_adapter.OpenAIAdapter, {
    "api_key_env":  "OPENAI_API_KEY",
    "base_url":     "https://generativelanguage.googleapis.com/v1beta/openai/",
    "adapter_name": "gemini",
    "model":        "gemini-2.5-flash",
    "max_tokens":   8192,
})

# Mistral via OpenAI-kompatiblen Endpoint — nutzt MISTRAL_API_KEY
# Modell überschreibbar via LLM_MODEL/OPENAI_MODEL — welche Modelle verfügbar
# sind, hängt vom Subscription-Tier ab (GET /v1/models mit dem eigenen Key
# prüfen); mistral-large-latest ist z.B. auf dem kostenfreien Tier nicht
# freigeschaltet, mistral-medium-latest/mistral-small-latest schon.
llm_adapter.register_adapter("mistral", llm_adapter.OpenAIAdapter, {
    "api_key_env":  "MISTRAL_API_KEY",
    "base_url":     "https://api.mistral.ai/v1",
    "adapter_name": "mistral",
    "model":        "mistral-medium-latest",
    "max_tokens":   8192,
})
