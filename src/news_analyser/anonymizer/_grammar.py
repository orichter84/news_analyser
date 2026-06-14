from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Article agreement correction for neuter nouns introduced by kinship
# term replacement (e.g. Sohn→Kind, Vater→Elternteil).
#
# Masculine and feminine article forms that precede a neuter noun are wrong
# and must be replaced with the neuter form.
# Longer alternatives first so the alternation matches greedily.
# ---------------------------------------------------------------------------

_MASC_TO_NEUT: dict[str, str] = {
    "welchen":  "welches",
    "welche":   "welches",
    "unseren":  "unser",
    "unsere":   "unser",
    "diesen":   "dieses",
    "diese":    "dieses",
    "meinen":   "mein",
    "meine":    "mein",
    "seinen":   "sein",
    "seine":    "sein",
    "ihren":    "ihr",
    "ihre":     "ihr",
    "keinen":   "kein",
    "keine":    "kein",
    "deinen":   "dein",
    "deine":    "dein",
    "euren":    "euer",
    "eure":     "euer",
    "einer":    "einem",
    "einen":    "ein",
    "eine":     "ein",
    "den":      "das",
    "die":      "das",
    "der":      "das",
}

_NEUTER_NOUNS: frozenset[str] = frozenset({
    "kind",
    "kindes",
    "geschwister",
    "geschwisterkindes",
    "elternteil",
    "elternteils",
    "enkelkind",
    "enkelkindes",
    "geschwisterkind",
})

# Pre-compiled: one pattern per neuter noun.
_art_alts = "|".join(re.escape(a) for a in _MASC_TO_NEUT)
ARTICLE_FIX_PATTERNS: list[re.Pattern[str]] = [
    re.compile(rf"\b({_art_alts})\s+({re.escape(noun)})\b", re.IGNORECASE)
    for noun in _NEUTER_NOUNS
]

# "einen Erwachsener" → "einen Erwachsenen" (accusative weak declension)
ERWACHSENER_ACC: re.Pattern[str] = re.compile(
    r"\b(einen)\s+Erwachsener\b", re.IGNORECASE
)


# ---------------------------------------------------------------------------
# Pronoun replacement in sentences containing Person-X placeholders.
# Masculine pronouns → feminine/neutral so the placeholder stays ungendered.
# Ordered longest-first to prevent partial matches (e.g. "seinen" before "sein").
# ---------------------------------------------------------------------------

_PRONOUN_MAP: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bseines\b", re.IGNORECASE), "ihres"),
    (re.compile(r"\bseinen\b", re.IGNORECASE), "ihren"),
    (re.compile(r"\bseinem\b", re.IGNORECASE), "ihrem"),
    (re.compile(r"\bseiner\b", re.IGNORECASE), "ihrer"),
    (re.compile(r"\bseine\b",  re.IGNORECASE), "ihre"),
    (re.compile(r"\bsein\b",   re.IGNORECASE), "ihr"),
    (re.compile(r"\bihn\b",    re.IGNORECASE), "sie"),
    (re.compile(r"\bihm\b",    re.IGNORECASE), "ihr"),
    (re.compile(r"\ber\b",     re.IGNORECASE), "sie"),
]

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")
_PERSON_PLACEHOLDER = re.compile(r"\bPerson-[A-Z]+\b")


def fix_pronouns(text: str) -> str:
    """Replace masculine pronouns throughout the text if any Person-X placeholder exists.

    Pronouns frequently refer across sentence boundaries, so a global replacement
    is more reliable than per-sentence matching.
    """
    if not _PERSON_PLACEHOLDER.search(text):
        return text
    for pattern, replacement in _PRONOUN_MAP:
        text = pattern.sub(
            lambda m, r=replacement: _match_case(m.group(0), r), text
        )
    return text


def _match_case(original: str, replacement: str) -> str:
    if original[0].isupper():
        return replacement[0].upper() + replacement[1:]
    return replacement


def fix_article_agreement(text: str) -> str:
    """Replace wrong article forms before neuter kinship-replacement nouns."""
    for pattern in ARTICLE_FIX_PATTERNS:
        text = pattern.sub(_replace_article, text)
    text = ERWACHSENER_ACC.sub(r"\1 Erwachsenen", text)
    return text


def _replace_article(m: re.Match[str]) -> str:
    article = m.group(1)
    noun = m.group(2)
    correct = _MASC_TO_NEUT[article.lower()]
    if article[0].isupper():
        correct = correct[0].upper() + correct[1:]
    return f"{correct} {noun}"
