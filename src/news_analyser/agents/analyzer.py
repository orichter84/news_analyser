"""LLM-based manipulation and framing analyser — two-pass architecture.

Pass 1 (anonymised text): Orwell-Index (extremism), Bernays Score, Techniques
Pass 2 (original text):   Politische Strömung (labels), DK-Index
"""

import json
import os
import re
from typing import Any

from ..scraper import Article
from ..prompts import load_prompt
import llm_adapter
from ..keywords import compute_keyword_signal
from ..anonymizer import anonymize
from ..repositories.anchor_store import get_similar_anchors, add_anchor, format_anchors_for_prompt
from ..repositories.technique_store import normalize_technique
from ..repositories.role_store import normalize_role, format_roles_for_prompt


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
    provider = os.environ.get("LLM_PROVIDER", "openai")
    adapter  = llm_adapter.get_instance(provider)

    kw      = compute_keyword_signal(article.text)
    anon    = anonymize(article.text)
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
        "text": anon["text"],
    }

    # Dynamische Anker in Prompt einbetten wenn vorhanden
    pass1_prompt = load_prompt("system", "pass1")
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

    result1 = _extract_json(raw1)
    if result1 is None:
        return None

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

    result2 = _extract_json(raw2)
    if result2 is None:
        return None

    # Rollen aus Pass 2 normalisieren
    for t in result2.get("manipulation_targets", []):
        if isinstance(t.get("rolle"), str):
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
    }

    # Artikel als Anker für zukünftige Analysen speichern
    add_anchor(
        text=anon["text"],
        orwell_index=orwell,
        politische_stroemung=stroemung,
        domain=article.domain,
        source_url=article.url,
    )

    return result
