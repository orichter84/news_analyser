"""LLM-based manipulation and framing analyser — two-pass architecture.

Pass 1 (anonymised text): Orwell-Index (extremism), Bernays Score, Techniques
Pass 2 (original text):   Politische Strömung (labels), DK-Index
"""

import json
import re
from typing import Any

from .scraper import Article
from .config import LLMConfig
from .prompts import load_prompt
from .connectors import load_connector
from .keywords import compute_keyword_signal
from .anonymizer import anonymize


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

    kw = compute_keyword_signal(article.text)
    anon = anonymize(article.text)

    base_meta = {
        "url": article.url,
        "domain": article.domain,
        "title": article.title or "",
        "author": article.author or "",
        "published_at": article.published_at or article.fetched_at,
        "word_count": article.word_count,
    }

    # ------------------------------------------------------------------
    # Pass 1 — anonymisierter Text → Orwell-Index (Extremismus), Techniken
    # ------------------------------------------------------------------
    pass1_input = {
        **base_meta,
        "keyword_signal": {
            "raw_signal": kw["raw_signal"],
            "left_count": kw["left_count"],
            "right_count": kw["right_count"],
            "left_hits": kw["left_hits"],
            "right_hits": kw["right_hits"],
        },
        "text": anon["text"],
    }

    try:
        raw1 = connector.generate(
            system_prompt=load_prompt("system", "pass1"),
            input_data=pass1_input,
            model=cfg.model,
            temperature=cfg.temperature,
            max_tokens=cfg.max_tokens,
        )
    except Exception as exc:
        print(f"[analyzer] Pass 1 Connector error: {exc}")
        return None

    result1 = _extract_json(raw1)
    if result1 is None:
        return None

    # ------------------------------------------------------------------
    # Pass 2 — Originaltext → Politische Strömung, DK-Index
    # ------------------------------------------------------------------
    pass2_input = {
        **base_meta,
        "text": article.text,
    }

    try:
        raw2 = connector.generate(
            system_prompt=load_prompt("system", "pass2"),
            input_data=pass2_input,
            model=cfg.model,
            temperature=cfg.temperature,
            max_tokens=cfg.max_tokens,
        )
    except Exception as exc:
        print(f"[analyzer] Pass 2 Connector error: {exc}")
        return None

    result2 = _extract_json(raw2)
    if result2 is None:
        return None

    # ------------------------------------------------------------------
    # Ergebnisse zusammenführen
    # ------------------------------------------------------------------
    result = {
        **base_meta,
        "source_url":          result1.get("source_url", article.url),
        "timestamp":           result1.get("timestamp", base_meta["published_at"]),
        "detected_techniques": result1.get("detected_techniques", []),
        "framing_target": {
            **result1.get("framing_target", {}),
            "dunning_kruger_index": result2.get("dunning_kruger_index", 0.0),
            "target_direction":     result2.get("target_direction", ""),
        },
        "politische_stroemung": result2.get("politische_stroemung", ["neutral"]),
    }

    return result
