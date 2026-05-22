"""LLM-based manipulation and framing analyser."""

import json
import re
from typing import Any

from .scraper import Article
from .config import LLMConfig
from .prompts import load_prompt
from .connectors import load_connector


def _extract_json(raw: str) -> dict[str, Any] | None:
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        print(f"[analyzer] JSON parse error: {exc}")
        return None


def analyze_article(article: Article) -> dict[str, Any] | None:
    cfg = LLMConfig.from_env()
    connector = load_connector(cfg.provider)
    system_prompt = load_prompt("system")

    input_data = {
        "url": article.url,
        "domain": article.domain,
        "fetched_at": article.fetched_at,
        "text": article.text,
    }

    try:
        raw = connector.generate(
            system_prompt=system_prompt,
            input_data=input_data,
            model=cfg.model,
            temperature=cfg.temperature,
            max_tokens=cfg.max_tokens,
        )
    except Exception as exc:
        print(f"[analyzer] Connector error: {exc}")
        return None

    return _extract_json(raw)
