"""LLM-based manipulation and framing analyser — three-pass architecture.

Pass 0 (original text):   Gruppenidentifikation (dynamische Anonymisierungsliste)
Pass 1 (anonymised text): Orwell-Index (extremism), Bernays Score, Techniques
Pass 2 (original text):   Politische Strömung (labels), DK-Index
"""

from __future__ import annotations

import datetime
import json
import logging
import os
import re
from pathlib import Path
from typing import Any

from ..scraper import Article

logger = logging.getLogger(__name__)

_DEBUG_DIR = Path(__file__).resolve().parents[3] / "data" / "debug_last_run"
_DEBUG_RUNS_DIR = Path(__file__).resolve().parents[3] / "data" / "debug_runs"


def _new_debug_run_id(domain: str) -> str:
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%f")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", domain).strip("-") or "unknown"
    return f"{ts}_{slug}"


def _write_debug(filename: str, content: str, run_id: str | None = None) -> None:
    """Writes to debug_last_run/ (always the latest run, fixed paths some
    notebooks depend on) and, when run_id is given, additionally archives an
    untouched copy under debug_runs/<run_id>/ so repeated runs of the same
    article can be diffed instead of overwriting each other.
    """
    try:
        _DEBUG_DIR.mkdir(parents=True, exist_ok=True)
        (_DEBUG_DIR / filename).write_text(content, encoding="utf-8")
        if run_id:
            run_dir = _DEBUG_RUNS_DIR / run_id
            run_dir.mkdir(parents=True, exist_ok=True)
            (run_dir / filename).write_text(content, encoding="utf-8")
    except Exception:
        pass
from ..prompts import load_prompt
import llm_adapter
from ..keywords import compute_keyword_signal
from ..anonymizer import anonymize
from .group_detector import detect_groups
from .errors import raise_if_gemini_quota_error
from ..repositories.anchor_store import get_similar_anchors, add_anchor, format_anchors_for_prompt
from ..repositories.technique_store import normalize_technique, format_techniques_for_prompt
from ..repositories.role_store import normalize_role, format_roles_for_prompt
from ..repositories.stroemung_store import normalize_stroemung


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
            logger.error("JSON parse error (auch nach Reparatur): %s", exc)
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
        logger.info("Grounding-Check: %d nicht belegte Technik-Instanz(en) entfernt.", dropped)
    return validated


def _dedupe_techniques(techniques: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Merges technique instances that became identical after canonical normalization.

    Two different free-text labels the model used for the same passage (e.g.
    "Emotional Appeal" and "Gefühlsbetonte Sprache") can both normalize to the
    same canonical technique; kept separately, the same quote would count
    twice towards the Bernays Score.
    """
    seen: set[tuple[str, str]] = set()
    deduped = []
    dropped = 0
    for t in techniques:
        key = (t.get("technique", ""), (t.get("quote") or "").strip())
        if key in seen:
            dropped += 1
            continue
        seen.add(key)
        deduped.append(t)
    if dropped:
        logger.info(
            "Dedup-Check: %d Technik-Instanz(en) nach Normalisierung als Duplikat entfernt.",
            dropped,
        )
    return deduped


def _validate_manipulation_target_grounding(
    targets: list[dict[str, Any]], source_text: str
) -> list[dict[str, Any]]:
    """Strips `rolle`/`direction` that lack a verifiable supporting quote.

    An unevidenced classification is not a valid data point (see the "General
    grounding requirement" in pass2.md) — it would otherwise silently skew
    downstream aggregations (publisher profiles, Cato-pattern) that read
    `rolle`/`direction` directly. Drops the whole entity if neither survives,
    since at that point nothing about it is a verified claim — consistent
    with "only list entities where manipulation techniques are clearly
    directed at them".
    """
    validated = []
    dropped_fields = 0
    dropped_entities = 0
    for t in targets:
        if not isinstance(t, dict):
            continue
        rolle_quote = (t.get("rolle_quote") or "").strip()
        direction_quote = (t.get("direction_quote") or "").strip()
        rolle_grounded = bool(rolle_quote) and rolle_quote in source_text
        direction_grounded = bool(direction_quote) and direction_quote in source_text

        if t.get("rolle") is not None and not rolle_grounded:
            t["rolle"] = None
            t["rolle_quote"] = None
            dropped_fields += 1
        if t.get("direction") is not None and not direction_grounded:
            t["direction"] = None
            t["direction_quote"] = None
            dropped_fields += 1

        if t.get("rolle") is None and t.get("direction") is None:
            dropped_entities += 1
            continue
        validated.append(t)

    if dropped_fields or dropped_entities:
        logger.info(
            "Grounding-Check (manipulation_targets): %d Feld(er) entfernt, %d Entität(en) komplett entfernt.",
            dropped_fields, dropped_entities,
        )
    return validated


def _validate_stroemung_grounding(
    stroemung: list[Any], source_text: str
) -> list[Any]:
    """Drops a politische_stroemung label that isn't backed by a verifiable quote.

    `neutral` is exempt (the prompt explicitly allows `quote: null` there — it's
    not a claim that needs evidence). Every other label is only as good as its
    quote: pass2.md now requires one ("strictly enforced"), so a label that
    arrives without one, or with one that doesn't actually occur in the article,
    is an unevidenced claim, not a valid data point — the same reasoning
    `_validate_manipulation_target_grounding` applies to rolle/direction, just
    without a second field to fall back on here. Confirmed empirically: four
    repeated runs of the same article produced four different stroemung label
    sets, none of which the previous (quote-preserving) version of this
    function could have caught.
    """
    validated = []
    dropped = 0
    for item in stroemung:
        if not isinstance(item, dict):
            validated.append(item)
            continue
        if item.get("label") == "neutral":
            validated.append(item)
            continue
        quote = (item.get("quote") or "").strip()
        if not quote or quote not in source_text:
            dropped += 1
            continue
        validated.append(item)
    if dropped:
        logger.info(
            "Grounding-Check (politische_stroemung): %d Label ohne belegtes Zitat entfernt.",
            dropped,
        )
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
    debug_run_id = _new_debug_run_id(article.domain)

    kw = compute_keyword_signal(article.text)

    if skip_anonymize:
        anon = {"text": article.text, "mapping": {}}
    else:
        group_terms = detect_groups(article.text, adapter)
        anon        = anonymize(article.text, group_terms=group_terms)
        _write_debug("01_detected_terms.json", json.dumps(group_terms, ensure_ascii=False, indent=2), debug_run_id)
        _write_debug("03_anonymization_mapping.json", json.dumps(anon["mapping"], ensure_ascii=False, indent=2), debug_run_id)

    _write_debug("00_original_text.txt", article.text, debug_run_id)
    _write_debug("02_anonymized_text.txt", anon["text"], debug_run_id)

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
    pass1_word_count = len(pass1_text.split())
    _write_debug("02b_pass1_input_quotes_stripped.txt", pass1_text, debug_run_id)

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
        raise_if_gemini_quota_error(exc)
        logger.error("Pass 1 error: %s", exc)
        return None

    _write_debug("04_pass1_raw_response.txt", raw1, debug_run_id)
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

    result1["detected_techniques"] = _dedupe_techniques(
        result1.get("detected_techniques", [])
    )

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
        raise_if_gemini_quota_error(exc)
        logger.error("Pass 2 error: %s", exc)
        return None

    _write_debug("05_pass2_raw_response.txt", raw2, debug_run_id)
    result2 = _extract_json(raw2)
    if result2 is None:
        return None

    # Rollen aus Pass 2 normalisieren
    for t in result2.get("manipulation_targets", []):
        if isinstance(t, dict) and isinstance(t.get("rolle"), str):
            t["rolle"] = normalize_role(t["rolle"])

    result2["manipulation_targets"] = _validate_manipulation_target_grounding(
        result2.get("manipulation_targets", []), article.text
    )

    # Freie Strömungs-Labels auf die kanonische Taxonomie normalisieren
    for item in result2.get("politische_stroemung", []):
        if isinstance(item, dict) and isinstance(item.get("label"), str):
            item["label"] = normalize_stroemung(item["label"])

    result2["politische_stroemung"] = _validate_stroemung_grounding(
        result2.get("politische_stroemung", ["neutral"]), article.text
    )

    # ------------------------------------------------------------------
    # Ergebnisse zusammenführen
    # ------------------------------------------------------------------
    stroemung            = result2.get("politische_stroemung", ["neutral"])
    themenbereich        = result2.get("themenbereich", "Sonstiges")
    manipulation_targets = result2.get("manipulation_targets", [])

    # orwell_index ist das Maximum aus zwei unabhängigen Signalen:
    # - orwell_index_structural: Pass 1, eigene Stimme des Autors (zitat-bereinigt)
    # - quote_amplification_index: Pass 2, Verstärkung extremer Rhetorik durch Zitatauswahl
    # Ein Artikel kann also allein durch seine Zitatauswahl als extrem gelten,
    # selbst wenn der Autor selbst sachlich und neutral formuliert.
    orwell_structural   = float(result1.get("framing_target", {}).get("orwell_index", 0.0))
    quote_amplification = float(result2.get("quote_amplification_index", 0.0))
    orwell              = max(orwell_structural, quote_amplification)

    result = {
        **base_meta,
        "source_url":          result1.get("source_url", article.url),
        "timestamp":           result1.get("timestamp", base_meta["published_at"]),
        "pass1_word_count":    pass1_word_count,
        "detected_techniques": result1.get("detected_techniques", []),
        "framing_target": {
            **result1.get("framing_target", {}),
            "orwell_index":                    orwell,
            "orwell_index_structural":         orwell_structural,
            "quote_amplification_index":       quote_amplification,
            "quote_amplification_explanation": result2.get("quote_amplification_explanation", ""),
            "dunning_kruger_index":        result2.get("dunning_kruger_index", 0.0),
            "dunning_kruger_explanation":  result2.get("dunning_kruger_explanation", ""),
            "target_direction":          result2.get("target_direction", ""),
        },
        "politische_stroemung":  stroemung,
        "themenbereich":         themenbereich,
        "manipulation_targets":  manipulation_targets,
        "llm_provider":          adapter.name,
        "llm_model":             adapter.model,
    }

    _write_debug("06_final_result.json", json.dumps(result, ensure_ascii=False, indent=2), debug_run_id)

    # Artikel als Anker für zukünftige Analysen speichern
    add_anchor(
        text=anon["text"],
        orwell_index=orwell,
        politische_stroemung=stroemung,
        domain=article.domain,
        source_url=article.url,
    )

    return result
