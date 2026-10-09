"""Pass 0 — Dynamische Gruppenidentifikation.

Erkennt Gruppenidentifikatoren im Originaltext (rassisch, ethnisch, religiös etc.)
und gibt eine strukturierte Liste zurück. Das LLM identifiziert nur — das Ersetzen
erfolgt deterministisch durch den Anonymizer-Code, nicht durch das LLM.
"""

from __future__ import annotations

import json
import re
from typing import Any

from ..prompts import load_prompt
from .errors import AnalysisAbortedError, raise_if_gemini_quota_error


def detect_groups(text: str, adapter: Any) -> list[dict[str, str]]:
    """Identifiziert Gruppenidentifikatoren im Text via LLM.

    Returns:
        Liste von {"term": str, "type": str} — nur Identifikation, kein Ersetzen.

    Raises:
        AnalysisAbortedError: bei Fehler oder abgeschnittener/unbrauchbarer Antwort —
            ohne vollständiges Pass-0-Ergebnis wäre die Anonymisierung lückenhaft.
    """
    prompt = load_prompt("system", "pass0")
    try:
        raw = adapter.generate(system_prompt=prompt, input_data={"text": text})
    except Exception as exc:
        raise_if_gemini_quota_error(exc)
        raise AnalysisAbortedError("Pass 0", str(exc)) from exc

    cleaned = re.sub(r"<think>.*?</think>", "", raw.strip(), flags=re.DOTALL)
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        result = json.loads(cleaned)
    except Exception:
        # Abgeschnittene Liste nicht reparieren — siehe _extract_json in analyzer.py.
        if not cleaned.endswith("]"):
            raise AnalysisAbortedError("Pass 0", "Antwort abgeschnitten (endet nicht mit ']')")
        try:
            from json_repair import repair_json
            result = json.loads(repair_json(cleaned))
        except Exception as exc:
            raise AnalysisAbortedError("Pass 0", f"JSON nicht lesbar (auch nach Reparatur): {exc}") from exc

    if not isinstance(result, list):
        raise AnalysisAbortedError("Pass 0", f"Antwort ist keine Liste ({type(result).__name__})")

    return [
        {"term": str(item["term"]).lower(), "type": str(item["type"])}
        for item in result
        if isinstance(item, dict) and "term" in item and "type" in item
    ]
