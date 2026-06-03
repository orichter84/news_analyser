"""
Anonymizer — ersetzt Gruppenidentifikatoren durch neutrale Platzhalter.

Zwei Schichten:
  1. spaCy de_core_news_md  → erkennt Personen (PER) und Organisationen (ORG)
  2. Kuratierte Liste       → ideologische Deskriptoren die spaCy nicht kennt

Gibt anonymisierten Text + Mapping zurück (für Nachvollziehbarkeit).
"""

from __future__ import annotations
import os
import re
from functools import lru_cache
from typing import TypedDict

import spacy


# ---------------------------------------------------------------------------
# Ideologische Deskriptoren — spaCy erkennt diese nicht als Named Entities
# Reihenfolge: längere Ausdrücke zuerst (verhindert Partial-Matches)
# ---------------------------------------------------------------------------

IDEOLOGICAL_TERMS: list[tuple[str, str]] = [
    # Linkes Spektrum
    ("antifaschistische", "extremistische"),
    ("antifaschistisch",  "extremistisch"),
    ("antifaschisten",    "aktivisten"),
    ("antifaschist",      "aktivist"),
    ("antifa",            "gruppe-a"),
    ("linksextremistisch","extremistisch"),
    ("linksextremisten",  "extremisten"),
    ("linksextremismus",  "extremismus"),
    ("linksradikal",      "radikal"),
    ("linksradikale",     "radikale"),
    ("kommunistisch",     "ideologisch"),
    ("kommunisten",       "ideologen"),
    # Rechtes Spektrum
    ("rechtsextremistisch","extremistisch"),
    ("rechtsextremisten",  "extremisten"),
    ("rechtsextremismus",  "extremismus"),
    ("rechtsradikal",      "radikal"),
    ("rechtsradikale",     "radikale"),
    ("rechtsradikalen",    "radikalen"),
    ("neonazi",            "extremist"),
    ("neonazis",           "extremisten"),
    ("faschismus",         "extremismus"),
    ("faschistisch",       "extremistisch"),
    ("faschisten",         "extremisten"),
    ("faschistischen",     "extremistischen"),
    ("nationalsozialismus","extremismus"),
    ("nationalsozialistisch","extremistisch"),
    ("nationalsozialisten", "extremisten"),
    # Politische Bewegungen / Identitäten
    ("queere",             "politische"),
    ("queer",              "politisch"),
    ("antirassistische",   "aktivistische"),
    ("antirassistisch",    "aktivistisch"),
    ("islamistisch",       "extremistisch"),
    ("islamisten",         "extremisten"),
    # Historische Regime (als Vergleich)
    ("nsdap",              "regime-d"),
    ("dritten reich",      "regime-d"),
    ("drittes reich",      "regime-d"),
    ("ddr",                "regime-e"),
    ("sed",                "partei-e"),
]


class AnonymizationResult(TypedDict):
    text: str
    mapping: dict[str, str]  # Platzhalter → Original


# Wörter die spaCy fälschlicherweise als Entities taggt
_ENTITY_BLOCKLIST: set[str] = {
    "faschismus", "kommunismus", "nationalismus", "extremismus",
    "massenabschiebungen", "abschiebungen", "terror", "ice-terror",
    "demokratie", "diktatur", "partei", "bündnis", "netzwerk",
}


@lru_cache(maxsize=1)
def _load_nlp() -> spacy.language.Language:
    return spacy.load(os.environ.get("SPACY_MODEL", "de_core_news_md"))


def anonymize(text: str) -> AnonymizationResult:
    """Anonymisiert Gruppenidentifikatoren im Text.

    Returns:
        text:    Anonymisierter Text
        mapping: {Platzhalter: Original} für Nachvollziehbarkeit
    """
    # Deduplizierungs-Dicts: surface form → Platzhalter
    seen_per: dict[str, str] = {}
    seen_org: dict[str, str] = {}
    seen_geo: dict[str, str] = {}
    person_counter = 0
    org_counter = 0
    geo_counter = 0

    # --- Schicht 1: spaCy NER ---
    nlp = _load_nlp()
    doc = nlp(text)

    replacements: list[tuple[int, int, str]] = []
    for ent in doc.ents:
        surface = ent.text.strip()
        surface_lower = surface.lower()

        # Blocklist und Mindestlänge (< 3 Zeichen überspringen)
        if surface_lower in _ENTITY_BLOCKLIST or len(surface) < 3:
            continue

        if ent.label_ == "PER":
            # Deduplizierung: Nachname allein → gleicher Platzhalter wie vollständiger Name
            key = _last_token(surface_lower)
            if key not in seen_per:
                person_counter += 1
                seen_per[key] = f"Person-{_num_to_letter(person_counter)}"
            placeholder = seen_per[key]
            replacements.append((ent.start_char, ent.end_char, placeholder))

        elif ent.label_ == "ORG":
            # Normalisierung: Punktuation entfernen, dann prüfen ob Kurzform bekannt
            norm = surface_lower.rstrip(".,;:!?")
            key = next((k for k in seen_org if norm.startswith(k) or k.startswith(norm)), norm)
            if key not in seen_org:
                org_counter += 1
                seen_org[key] = f"Org-{_num_to_letter(org_counter)}"
            placeholder = seen_org[key]
            replacements.append((ent.start_char, ent.end_char, placeholder))

        elif ent.label_ in ("LOC", "GPE"):
            key = surface_lower.rstrip(".,;:!?")
            if key not in seen_geo:
                geo_counter += 1
                seen_geo[key] = f"Geo-{_num_to_letter(geo_counter)}"
            placeholder = seen_geo[key]
            replacements.append((ent.start_char, ent.end_char, placeholder))

    # Mapping aufbauen (Platzhalter → repräsentatives Original)
    mapping: dict[str, str] = {}
    for surface, ph in {**{v: k for k, v in seen_per.items()},
                        **{v: k for k, v in seen_org.items()},
                        **{v: k for k, v in seen_geo.items()}}.items():
        mapping[surface] = ph

    # Replacements von hinten nach vorne anwenden (Indizes bleiben stabil)
    result = text
    for start, end, placeholder in sorted(replacements, key=lambda x: x[0], reverse=True):
        result = result[:start] + placeholder + result[end:]

    # --- Schicht 2: Ideologische Deskriptoren ---
    for original, replacement in IDEOLOGICAL_TERMS:
        pattern = re.compile(re.escape(original), re.IGNORECASE)
        if pattern.search(result):
            mapping[replacement] = original
            result = pattern.sub(replacement, result)

    return AnonymizationResult(text=result, mapping=mapping)


def _last_token(text: str) -> str:
    """Gibt das letzte Wort zurück — für Nachnamen-Deduplizierung."""
    return text.split()[-1] if text.split() else text


def _num_to_letter(n: int) -> str:
    """1→A, 2→B, … 26→Z, 27→AA, …"""
    result = ""
    while n > 0:
        n, remainder = divmod(n - 1, 26)
        result = chr(65 + remainder) + result
    return result
