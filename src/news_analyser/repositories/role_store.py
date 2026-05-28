"""
role_store — Verwaltet Rollen-Definitionen für Manipulation-Targets.

Zweck:
  1. Prompt-Injection  — format_roles_for_prompt() erzeugt den Rollen-Block für pass2.md
  2. Normalisierung    — normalize_role() mappt LLM-Freitext auf kanonische Namen
  3. Knowledge Base    — get_all_roles() liefert alle Rollen für die API

Normalisierung (kein ChromaDB — die Liste ist kurz und besteht aus Einzelwörtern):
  1. Exakter Treffer
  2. Groß-/Kleinschreibung ignorieren
  3. difflib.get_close_matches (Levenshtein-ähnlich, Schwellwert 0.75)
  4. Fallback: Original-Name unverändert
"""

import difflib
import json
from pathlib import Path
from typing import Any

_DATA_FILE = Path(__file__).parent.parent / "data" / "roles.json"
_FUZZY_CUTOFF = 0.75


def _load_roles() -> list[dict[str, Any]]:
    return json.loads(_DATA_FILE.read_text(encoding="utf-8"))


_ROLES: list[dict[str, Any]] = _load_roles()
_CANONICAL_NAMES: list[str] = [r["name"] for r in _ROLES]


def normalize_role(name: str) -> str:
    """Mappt einen LLM-generierten Rollennamen auf den kanonischen Namen.

    Gibt den Original-Namen zurück wenn keine ausreichend gute Übereinstimmung
    gefunden wird.
    """
    if not name:
        return name

    # 1. Exakter Treffer
    if name in _CANONICAL_NAMES:
        return name

    # 2. Groß-/Kleinschreibung ignorieren
    lower = name.lower()
    for canonical in _CANONICAL_NAMES:
        if canonical.lower() == lower:
            return canonical

    # 3. Fuzzy-Match (difflib — kein externes Paket nötig)
    matches = difflib.get_close_matches(name, _CANONICAL_NAMES, n=1, cutoff=_FUZZY_CUTOFF)
    if matches:
        return matches[0]

    return name


def format_roles_for_prompt() -> str:
    """Erzeugt den formatierten Rollen-Block für die Prompt-Injection ({{ROLES}})."""
    lines = []
    for role in _ROLES:
        line = f"  - `{role['name']}` — {role['prompt_en']}"
        if role.get("dk_signal"):
            line += " *(correlates with elevated Dunning-Kruger-Index)*"
        lines.append(line)
    return "\n".join(lines)


def get_all_roles() -> list[dict[str, Any]]:
    """Gibt alle Rollen-Definitionen zurück (für die Knowledge-Base-API)."""
    return _ROLES


def get_role(role_id: str) -> dict[str, Any] | None:
    """Gibt eine einzelne Rolle per ID zurück."""
    for role in _ROLES:
        if role["id"] == role_id:
            return role
    return None
