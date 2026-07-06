"""Pass 0 — Dynamische Gruppenidentifikation.

Erkennt Gruppenidentifikatoren im Originaltext (rassisch, ethnisch, religiös etc.)
und gibt eine strukturierte Liste zurück. Das LLM identifiziert nur — das Ersetzen
erfolgt deterministisch durch den Anonymizer-Code, nicht durch das LLM.
"""

from __future__ import annotations

import json
import re
from typing import Any

import llm_adapter
from ..prompts import load_prompt


def detect_groups(text: str, adapter: Any) -> list[dict[str, str]]:
    """Identifiziert Gruppenidentifikatoren im Text via LLM.

    Returns:
        Liste von {"term": str, "type": str} — nur Identifikation, kein Ersetzen.
        Bei Fehler: leere Liste (Analyse läuft ohne Pass-0-Ergebnisse weiter).
    """
    prompt = load_prompt("system", "pass0")
    try:
        raw = adapter.generate(system_prompt=prompt, input_data={"text": text})
    except Exception as exc:
        print(f"[pass0] Fehler bei Gruppenidentifikation: {exc}")
        return []

    cleaned = re.sub(r"<think>.*?</think>", "", raw.strip(), flags=re.DOTALL)
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        result = json.loads(cleaned)
    except Exception:
        try:
            from json_repair import repair_json
            result = json.loads(repair_json(cleaned))
        except Exception as exc:
            print(f"[pass0] JSON-Fehler: {exc}")
            return []

    if not isinstance(result, list):
        return []

    return [
        {"term": str(item["term"]).lower(), "type": str(item["type"])}
        for item in result
        if isinstance(item, dict) and "term" in item and "type" in item
    ]
