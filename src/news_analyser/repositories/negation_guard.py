"""
Shared negation/critical-prefix guard for embedding-based normalize_* functions.

Sentence-transformer embeddings don't reliably separate a term from its negation
for short German compounds — e.g. "islamkritisch" (critical of Islam) lands at
cosine distance ~0.09 from "islamistisch" (Islamist), and "antifeministisch" at
~0.18 from "feministisch": well inside a typical match threshold despite being
near-opposite stances. First found and fixed in stroemung_store.normalize_stroemung
(ADR 0009); technique_store.normalize_technique had the same latent bug
(e.g. "anti-Appeal to Fear" -> "Appeal to Fear"), confirmed via
notebooks/normalization_check.ipynb and fixed the same way.

Any label built from one of these markers is a critical/oppositional stance on
the root concept, not a spelling variant of it, so it must skip semantic
matching entirely rather than risk being collapsed onto the concept it opposes.
"""

from __future__ import annotations

NEGATION_MARKERS = ["anti", "kritisch", "gegner", "feindlich", "skeptisch", "ablehnend"]


def is_oppositional(text: str) -> bool:
    lower = text.lower()
    return any(marker in lower for marker in NEGATION_MARKERS)
