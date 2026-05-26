"""
Pre-signal computation for the Orwell-Index (extremism).

Counts rhetorically extreme keywords from both ends of the political spectrum
and returns a signal for overall extremism intensity — direction-neutral.

The signal is passed to Pass 1 (anonymised) as a weak prior (~20-30% weight).
The LLM remains the final arbiter.
"""

from typing import TypedDict


# Extreme Rhetorik — linkes Spektrum
EXTREME_LEFT: list[str] = [
    # Kampf & Mobilisierung
    "klassenkampf", "revolution", "widerstand", "aufstand", "mobilisierung",
    "blockade", "sabotage", "systemsturz", "enteignung",
    # Feindbilder
    "kapitalisten", "konzernherrschaft", "ausbeutung", "faschisten",
    "unterdrücker", "herrschende klasse", "bourgeoisie",
    # Apokalyptische Sprache
    "kapitalismus zerstört", "system überwinden", "alles steht auf dem spiel",
    "kein kompromiss", "kampf ums überleben",
    # Totalitärer Anspruch
    "vergesellschaftung", "diktatur des proletariats", "klassenjustiz",
]

# Extreme Rhetorik — rechtes Spektrum
EXTREME_RIGHT: list[str] = [
    # Kampf & Mobilisierung
    "volksverrat", "remigration", "bevölkerungsaustausch", "endkampf",
    "widerstand", "reconquista", "abendland verteidigen",
    # Feindbilder
    "lügenpresse", "systemmedien", "globalisten", "überfremdung",
    "islamisierung", "bevölkerungsaustausch", "politkaste", "altparteien",
    # Apokalyptische Sprache
    "deutschland wird abgeschafft", "großer austausch", "volkstod",
    "existenzielle bedrohung", "letzte chance",
    # Totalitärer Anspruch
    "völkisch", "rassenrein", "blut und boden", "lebensraum",
    "führerprinzip",
]

# Allgemeine Extremismus-Indikatoren (richtungsunabhängig)
EXTREME_GENERAL: list[str] = [
    "menschenverachtend", "vernichten", "ausrotten", "säuberung",
    "todfeind", "parasiten", "untermenschen", "verräter",
    "kollaborateur", "feinde des volkes",
]


class KeywordSignal(TypedDict):
    extremism_score: float    # 0.0 (keine Treffer) bis 1.0 (viele Treffer)
    left_count: int
    right_count: int
    general_count: int
    left_hits: list[str]
    right_hits: list[str]
    general_hits: list[str]


def compute_keyword_signal(text: str) -> KeywordSignal:
    """Return an extremism keyword signal for the given article text.

    extremism_score = total_hits / (total_hits + dampening)
    Asymptotically approaches 1.0, never reaches it.
    Returns 0.0 if no extreme keywords are found.
    """
    text_lower = text.lower()

    left_hits    = [kw for kw in EXTREME_LEFT    if kw in text_lower]
    right_hits   = [kw for kw in EXTREME_RIGHT   if kw in text_lower]
    general_hits = [kw for kw in EXTREME_GENERAL if kw in text_lower]

    total = len(left_hits) + len(right_hits) + len(general_hits)
    # Dampening=5: score bei 1 Treffer=0.17, bei 5=0.5, bei 15=0.75
    extremism_score = round(total / (total + 5), 3) if total > 0 else 0.0

    return KeywordSignal(
        extremism_score=extremism_score,
        left_count=len(left_hits),
        right_count=len(right_hits),
        general_count=len(general_hits),
        left_hits=left_hits[:10],
        right_hits=right_hits[:10],
        general_hits=general_hits[:10],
    )
