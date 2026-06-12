from __future__ import annotations

import os
import re

import spacy

from ._normalizations import IDEOLOGICAL_TERMS, _ENTITY_BLOCKLIST
from ._result import AnonymizationResult
from .strategy import AnonymizationStrategy


class SpacyStrategy(AnonymizationStrategy):
    """Anonymization pipeline using spaCy NER and curated normalizations."""

    def __init__(self, model: str | None = None) -> None:
        self._model_name = model or os.environ.get("SPACY_MODEL", "de_core_news_md")
        self._nlp: spacy.language.Language | None = None

    # ------------------------------------------------------------------
    # Pipeline steps
    # ------------------------------------------------------------------

    def normalize(self, text: str) -> tuple[str, dict[str, str]]:
        mapping: dict[str, str] = {}
        for original, replacement in IDEOLOGICAL_TERMS:
            pattern = re.compile(re.escape(original), re.IGNORECASE)
            if pattern.search(text):
                mapping[replacement] = original
                text = pattern.sub(
                    lambda m, r=replacement: _match_case(m.group(0), r), text
                )
        return text, mapping

    def ner(self, text: str) -> tuple[str, dict[str, str]]:
        seen_per: dict[str, str] = {}
        seen_org: dict[str, str] = {}
        seen_geo: dict[str, str] = {}
        person_counter = 0
        org_counter = 0
        geo_counter = 0

        doc = self._load_nlp()(text)
        replacements: list[tuple[int, int, str]] = []

        for ent in doc.ents:
            surface = ent.text.strip()
            surface_lower = surface.lower()

            if surface_lower in _ENTITY_BLOCKLIST or len(surface) < 3:
                continue

            if ent.label_ == "PER":
                key = _last_token(surface_lower)
                if key not in seen_per:
                    person_counter += 1
                    seen_per[key] = f"Person-{_num_to_letter(person_counter)}"
                replacements.append((ent.start_char, ent.end_char, seen_per[key]))

            elif ent.label_ == "ORG":
                norm = surface_lower.rstrip(".,;:!?")
                key = next(
                    (k for k in seen_org if norm.startswith(k) or k.startswith(norm)),
                    norm,
                )
                if key not in seen_org:
                    org_counter += 1
                    seen_org[key] = f"Org-{_num_to_letter(org_counter)}"
                replacements.append((ent.start_char, ent.end_char, seen_org[key]))

            elif ent.label_ in ("LOC", "GPE"):
                key = surface_lower.rstrip(".,;:!?")
                if key not in seen_geo:
                    geo_counter += 1
                    seen_geo[key] = f"Geo-{_num_to_letter(geo_counter)}"
                replacements.append((ent.start_char, ent.end_char, seen_geo[key]))

        mapping: dict[str, str] = {
            ph: surface
            for surface, ph in {
                **{v: k for k, v in seen_per.items()},
                **{v: k for k, v in seen_org.items()},
                **{v: k for k, v in seen_geo.items()},
            }.items()
        }

        for start, end, placeholder in sorted(replacements, key=lambda x: x[0], reverse=True):
            text = text[:start] + placeholder + text[end:]

        return text, mapping

    def replace_groups(
        self,
        text: str,
        group_terms: list[dict[str, str]] | None = None,
    ) -> tuple[str, dict[str, str]]:
        mapping: dict[str, str] = {}
        group_counter = 0
        if group_terms:
            for item in group_terms:
                term = item.get("term", "").strip()
                if not term:
                    continue
                pattern = re.compile(re.escape(term), re.IGNORECASE)
                if pattern.search(text):
                    group_counter += 1
                    placeholder = f"Gruppe-{_num_to_letter(group_counter)}"
                    mapping[placeholder] = term
                    text = pattern.sub(placeholder, text)
        return text, mapping

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load_nlp(self) -> spacy.language.Language:
        if self._nlp is None:
            self._nlp = spacy.load(self._model_name)
        return self._nlp


def _match_case(original: str, replacement: str) -> str:
    """Preserve capitalisation: if original starts uppercase, capitalise replacement."""
    if original and original[0].isupper():
        return replacement[0].upper() + replacement[1:]
    return replacement


def _last_token(text: str) -> str:
    """Return the last whitespace-separated token (used for surname deduplication)."""
    parts = text.split()
    return parts[-1] if parts else text


def _num_to_letter(n: int) -> str:
    """Map 1→A, 2→B, …, 26→Z, 27→AA, …"""
    result = ""
    while n > 0:
        n, remainder = divmod(n - 1, 26)
        result = chr(65 + remainder) + result
    return result
