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
