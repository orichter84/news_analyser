"""LLM-based manipulation and framing analyser — three-pass architecture.

Pass 0 (original text):   Gruppenidentifikation (dynamische Anonymisierungsliste)
Pass 1 (anonymised text): Orwell-Index (extremism), Bernays Score, Techniques
Pass 2 (original text):   Politische Strömung (labels), DK-Index
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from ..scraper import Article

_DEBUG_DIR = Path(__file__).resolve().parents[3] / "data" / "debug_last_run"


def _write_debug(filename: str, content: str) -> None:
    try:
        _DEBUG_DIR.mkdir(parents=True, exist_ok=True)
        (_DEBUG_DIR / filename).write_text(content, encoding="utf-8")
    except Exception:
        pass
from ..prompts import load_prompt
import llm_adapter
from ..keywords import compute_keyword_signal
from ..anonymizer import anonymize
from .group_detector import detect_groups
from ..repositories.anchor_store import get_similar_anchors, add_anchor, format_anchors_for_prompt
from ..repositories.technique_store import normalize_technique, format_techniques_for_prompt
from ..repositories.role_store import normalize_role, format_roles_for_prompt


def _extract_json(raw: str) -> dict[str, Any] | None:
    # Strip Qwen-style thinking tokens before any other processing
    cleaned = re.sub(r"<think>.*?</think>", "", raw.strip(), flags=re.DOTALL)
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        try:
            from json_repair import repair_json
            parsed = json.loads(repair_json(cleaned))
        except Exception as exc:
            print(f"[analyzer] JSON parse error (auch nach Reparatur): {exc}")
            return None
    # Manche Modelle wrappen das Ergebnis in ein Array — erstes Element nehmen
    if isinstance(parsed, list):
        parsed = parsed[0] if parsed else None
    return parsed if isinstance(parsed, dict) else None


def _validate_quote_grounding(
    techniques: list[dict[str, Any]], source_text: str
) -> list[dict[str, Any]]:
    """Drops technique instances whose quote can't be verified against the source text.

    Catches two hallucination patterns observed with local models: fabricated quotes that
    never appear in the text, and inflated occurrence counts (the same quote reported as a
    "2nd/3rd/4th instance" more often than it actually occurs in the text).
    """
    quote_counts: dict[str, int] = {}
    validated = []
    dropped = 0
    for t in techniques:
        quote = (t.get("quote") or "").strip()
        if not quote:
            dropped += 1
            continue
        occurrences = source_text.count(quote)
        if occurrences == 0:
            dropped += 1
            continue
        quote_counts[quote] = quote_counts.get(quote, 0) + 1
        if quote_counts[quote] > occurrences:
            dropped += 1
            continue
        validated.append(t)
    if dropped:
        print(f"[analyzer] Grounding-Check: {dropped} nicht belegte Technik-Instanz(en) entfernt.")
    return validated


_QUOTE_PATTERNS = [
    re.compile(r"„.*?“", re.DOTALL),  # „..."
    re.compile(r"».*?«", re.DOTALL),
    re.compile(r'".*?"', re.DOTALL),
]


def _strip_quoted_material(text: str) -> str:
    """Removes direct quoted speech („...", »...«, "...") before Pass 1.

    Pass 1 must not use quoted third-party speech as evidence for detected_techniques
    (every model tested so far violated that rule at least once when asked to self-exclude
    it). Stripping it mechanically is more reliable than relying on the model's compliance.
    Quote-selection bias (one-sided quoting, missing rebuttals) is judged in Pass 2 instead,
    which operates on the full, unstripped original text.
    """
    stripped = text
    for pattern in _QUOTE_PATTERNS:
        stripped = pattern.sub("[…]", stripped)
    return stripped


def analyze_article(article: Article, skip_anonymize: bool = False) -> dict[str, Any] | None:
    provider = os.environ.get("LLM_PROVIDER", "openai")
    adapter  = llm_adapter.get_instance(provider)

    kw = compute_keyword_signal(article.text)

    if skip_anonymize:
        anon = {"text": article.text, "mapping": {}}
    else:
        group_terms = detect_groups(article.text, adapter)
        anon        = anonymize(article.text, group_terms=group_terms)
        _write_debug("01_detected_terms.json", json.dumps(group_terms, ensure_ascii=False, indent=2))
        _write_debug("03_anonymization_mapping.json", json.dumps(anon["mapping"], ensure_ascii=False, indent=2))

    _write_debug("00_original_text.txt", article.text)
    _write_debug("02_anonymized_text.txt", anon["text"])

    anchors = get_similar_anchors(anon["text"])

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
    pass1_text = _strip_quoted_material(anon["text"])
    _write_debug("02b_pass1_input_quotes_stripped.txt", pass1_text)

    pass1_input = {
        **base_meta,
        "keyword_signal": {
            "extremism_score": kw["extremism_score"],
            "left_count":      kw["left_count"],
            "right_count":     kw["right_count"],
            "general_count":   kw["general_count"],
            "left_hits":       kw["left_hits"],
            "right_hits":      kw["right_hits"],
            "general_hits":    kw["general_hits"],
        },
        "text": pass1_text,
    }

    # Dynamische Anker in Prompt einbetten wenn vorhanden
    pass1_prompt = load_prompt("system", "pass1", context={"TECHNIQUES": format_techniques_for_prompt()})
    anchor_section = format_anchors_for_prompt(anchors)
    if anchor_section:
        pass1_prompt = pass1_prompt + "\n\n" + anchor_section

    try:
        raw1 = adapter.generate(
            system_prompt=pass1_prompt,
            input_data=pass1_input,
        )
    except Exception as exc:
        print(f"[analyzer] Pass 1 error: {exc}")
        return None

    _write_debug("04_pass1_raw_response.txt", raw1)
    result1 = _extract_json(raw1)
    if result1 is None:
        return None

    result1["detected_techniques"] = _validate_quote_grounding(
        result1.get("detected_techniques", []), pass1_text
    )

    # Techniken auf kanonische Namen normalisieren
    for t in result1.get("detected_techniques", []):
        if isinstance(t.get("technique"), str):
            t["technique"] = normalize_technique(t["technique"])

    # Rollen auf kanonische Namen normalisieren (Pass 1 hat keine Rollen)
    for t in result1.get("manipulation_targets", []):
        if isinstance(t.get("rolle"), str):
            t["rolle"] = normalize_role(t["rolle"])

    # ------------------------------------------------------------------
    # Pass 2 — Originaltext → Politische Strömung, DK-Index
    # ------------------------------------------------------------------
    pass2_input = {
        **base_meta,
        "text": article.text,
    }

    pass2_prompt = load_prompt("system", "pass2", context={"ROLES": format_roles_for_prompt()})

    try:
        raw2 = adapter.generate(
            system_prompt=pass2_prompt,
            input_data=pass2_input,
        )
    except Exception as exc:
        print(f"[analyzer] Pass 2 error: {exc}")
        return None

    _write_debug("05_pass2_raw_response.txt", raw2)
    result2 = _extract_json(raw2)
    if result2 is None:
        return None

    # Rollen aus Pass 2 normalisieren
    for t in result2.get("manipulation_targets", []):
        if isinstance(t, dict) and isinstance(t.get("rolle"), str):
            t["rolle"] = normalize_role(t["rolle"])

    # ------------------------------------------------------------------
    # Ergebnisse zusammenführen
    # ------------------------------------------------------------------
    stroemung            = result2.get("politische_stroemung", ["neutral"])
    orwell               = result1.get("framing_target", {}).get("orwell_index", 0.0)
    themenbereich        = result2.get("themenbereich", "Sonstiges")
    manipulation_targets = result2.get("manipulation_targets", [])

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
        "politische_stroemung":  stroemung,
        "themenbereich":         themenbereich,
        "manipulation_targets":  manipulation_targets,
        "llm_provider":          adapter.name,
        "llm_model":             adapter.model,
    }

    _write_debug("06_final_result.json", json.dumps(result, ensure_ascii=False, indent=2))

    # Artikel als Anker für zukünftige Analysen speichern
    add_anchor(
        text=anon["text"],
        orwell_index=orwell,
        politische_stroemung=stroemung,
        domain=article.domain,
        source_url=article.url,
    )

    return result
