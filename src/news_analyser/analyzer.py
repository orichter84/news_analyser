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
    except json.JSONDecodeError:
        try:
            from json_repair import repair_json
            return json.loads(repair_json(cleaned))
        except Exception as exc:
            print(f"[analyzer] JSON parse error (auch nach Reparatur): {exc}")
            return None


def analyze_article(article: Article) -> dict[str, Any] | None:
    cfg = LLMConfig.from_env()
    connector = load_connector(cfg.provider)
    system_prompt = load_prompt("system")

    input_data = {
        "url": article.url,
        "domain": article.domain,
        "title": article.title or "",
        "author": article.author or "",
        "published_at": article.published_at or article.fetched_at,
        "word_count": article.word_count,
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

    result = _extract_json(raw)
    if result is not None:
        result.setdefault("title", article.title or "")
        result.setdefault("author", article.author or "")
        result.setdefault("published_at", article.published_at or article.fetched_at)
        result.setdefault("word_count", article.word_count)
    return result
