"""
Pre-signal computation for the Orwell-Index.

Counts politically loaded keywords (left/right) and returns a raw directional
signal that the LLM uses as one of two inputs alongside few-shot anchor examples.

The signal is intentionally naive — it cannot distinguish "pro" vs. "contra"
usage, which is why the LLM remains the final arbiter.
"""

from typing import TypedDict


LEFT_KEYWORDS: list[str] = [
    # Gesellschaft & Gerechtigkeit
    "soziale gerechtigkeit", "solidarität", "umverteilung", "soziale ungleichheit",
    "armutsbekämpfung", "gemeinwohl", "vergesellschaftung", "klassenkampf",
    "ausbeutung", "kapitalismuskritik", "konzernmacht", "rüstungskonzerne",
    # Identität & Rechte
    "diversität", "inklusion", "antirassismus", "feminismus", "diskriminierung",
    "marginalisierte", "privilegien", "patriarchat", "gleichstellung",
    "minderheitenschutz", "emanzipation", "queere", "lgbtq",
    # Migration & Weltoffenheit
    "weltoffenheit", "flüchtlingsschutz", "asylrecht", "willkommenskultur",
    "menschenrechte", "seenotrettung",
    # Klima & Umwelt
    "klimaschutz", "klimagerechtigkeit", "energiewende", "dekarbonisierung",
    "erneuerbare energien", "fossil",
    # Wirtschaft
    "progressive", "reiche zur kasse", "vermögenssteuer", "mindestlohn erhöhung",
    "waffenexporte", "rüstungsexporte",
]

RIGHT_KEYWORDS: list[str] = [
    # Nation & Identität
    "heimat", "leitkultur", "tradition", "nationale identität", "abendland",
    "deutsche werte", "patriotismus", "deutschtum", "völkisch",
    # Sicherheit & Ordnung
    "ordnung", "grenzschutz", "innere sicherheit", "law and order",
    "null toleranz", "null-toleranz", "recht und ordnung",
    # Migration (negativ geframt)
    "abschiebung", "remigration", "bevölkerungsaustausch", "überfremdung",
    "islamisierung", "asylmissbrauch", "wirtschaftsflüchtlinge",
    "kriminalitätszuwanderer", "masseneinwanderung",
    # Medien & Establishment
    "mainstream-medien", "lügenpresse", "staatsfunk", "meinungsdiktatur",
    "altparteien", "volksverrat", "systemmedien", "politkaste",
    # Ideologiekritik (rechts)
    "woke", "genderideologie", "genderwahn", "klimawahn", "ökodiktatur",
    "frühsexualisierung", "links-grün",
    # Wirtschaft (konservativ)
    "leistungsgesellschaft", "eigenverantwortung", "steuerverschwendung",
    "bürokratieabbau", "wirtschaftsfreiheit", "mittelstand stärken",
]


class KeywordSignal(TypedDict):
    raw_signal: float       # -1.0 (links) bis +1.0 (rechts)
    left_count: int
    right_count: int
    left_hits: list[str]    # gematchte Begriffe (max 10 als Stichprobe)
    right_hits: list[str]


def compute_keyword_signal(text: str) -> KeywordSignal:
    """Return a directional keyword signal for the given article text.

    raw_signal = (right - left) / (right + left)  ∈ [-1.0, +1.0]
    Returns 0.0 if no political keywords are found.
    """
    text_lower = text.lower()

    left_hits = [kw for kw in LEFT_KEYWORDS if kw in text_lower]
    right_hits = [kw for kw in RIGHT_KEYWORDS if kw in text_lower]

    left_count = len(left_hits)
    right_count = len(right_hits)
    total = left_count + right_count

    raw_signal = round((right_count - left_count) / total, 3) if total > 0 else 0.0

    return KeywordSignal(
        raw_signal=raw_signal,
        left_count=left_count,
        right_count=right_count,
        left_hits=left_hits[:10],
        right_hits=right_hits[:10],
    )
