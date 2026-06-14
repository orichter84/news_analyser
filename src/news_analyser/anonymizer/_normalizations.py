from __future__ import annotations

# ---------------------------------------------------------------------------
# Static text normalizations — (original, normalized) pairs.
# Applied case-insensitively in the order listed; longer entries first to
# prevent partial matches on shorter prefixes.
# ---------------------------------------------------------------------------

IDEOLOGICAL_TERMS: list[tuple[str, str]] = [
    # Left spectrum
    ("antifaschistische", "extremistische"),
    ("antifaschistisch",  "extremistisch"),
    ("antifaschisten",    "aktivisten"),
    ("antifaschist",      "aktivist"),
    ("antifa",            "extremisten"),
    ("linksextremistisch","extremistisch"),
    ("linksextremisten",  "extremisten"),
    ("linksextremismus",  "extremismus"),
    ("linksradikal",      "radikal"),
    ("linksradikale",     "radikale"),
    ("kommunistisch",     "ideologisch"),
    ("kommunisten",       "ideologen"),
    # Right spectrum
    ("rechtsextremistisch","extremistisch"),
    ("rechtsextremisten",  "extremisten"),
    ("rechtsextremismus",  "extremismus"),
    ("rechtsradikal",      "radikal"),
    ("rechtsradikale",     "radikale"),
    ("rechtsradikalen",    "radikalen"),
    ("neonazis",           "extremisten"),
    ("neonazi",            "extremist"),
    ("faschismus",         "extremismus"),
    ("faschistisch",       "extremistisch"),
    ("faschisten",         "extremisten"),
    ("faschistischen",     "extremistischen"),
    ("nationalsozialismus","extremismus"),
    ("nationalsozialistisch","extremistisch"),
    ("nationalsozialisten", "extremisten"),
    # Political movements / identities
    ("queere",             "politische"),
    ("queer",              "politisch"),
    ("antirassistische",   "aktivistische"),
    ("antirassistisch",    "aktivistisch"),
    ("islamistisch",       "extremistisch"),
    ("islamisten",         "extremisten"),
    # Historical regimes (used as comparisons)
    ("nsdap",              "extremistische partei"),
    ("dritten reich",      "historisches regime"),
    ("drittes reich",      "historisches regime"),
    ("ddr",                "historisches regime"),
    ("sed",                "regierungspartei"),
]

# ---------------------------------------------------------------------------
# Gendered kinship terms — require word boundaries to avoid matching inside
# compound nouns (e.g. "Kaufmann", "Frauenhaus").
# Longer/plural forms first to prevent partial matches.
# ---------------------------------------------------------------------------

GENDERED_KINSHIP_TERMS: list[tuple[str, str]] = [
    ("herren",     "Erwachsene"),
    ("damen",      "Erwachsene"),
    ("herr",       "Erwachsener"),
    ("dame",       "Erwachsene"),
    ("töchter",    "Kinder"),
    ("söhne",      "Kinder"),
    ("sohnes",     "Kindes"),
    ("sohns",      "Kindes"),
    ("tochter",    "Kind"),
    ("sohn",       "Kind"),
    ("männer",     "Erwachsene"),
    ("mannes",     "Erwachsenen"),
    ("manns",      "Erwachsenen"),
    ("frauen",     "Erwachsene"),
    ("mann",       "Erwachsener"),
    ("frau",       "Erwachsene"),
    ("schwestern", "Geschwister"),
    ("brüder",     "Geschwister"),
    ("bruders",    "Geschwisterkindes"),
    ("schwester",  "Geschwister"),
    ("bruder",     "Geschwister"),
    ("mütter",     "Elternteile"),
    ("väter",      "Elternteile"),
    ("vaters",     "Elternteils"),
    ("mutter",     "Elternteil"),
    ("vater",      "Elternteil"),
    ("enkelinnen", "Enkelkinder"),
    ("enkelin",    "Enkelkind"),
    ("enkels",     "Enkelkindes"),
    ("enkel",      "Enkelkinder"),
    ("nichten",    "Geschwisterkinder"),
    ("neffen",     "Geschwisterkinder"),
    ("nichte",     "Geschwisterkind"),
    ("neffe",      "Geschwisterkind"),
    ("onkels",     "Verwandten"),
    ("tanten",     "Verwandte"),
    ("onkel",      "Verwandte"),
    ("tante",      "Verwandte"),
]

# Words that spaCy incorrectly tags as named entities.
_ENTITY_BLOCKLIST: frozenset[str] = frozenset({
    "faschismus", "kommunismus", "nationalismus", "extremismus",
    "massenabschiebungen", "abschiebungen", "terror", "ice-terror",
    "demokratie", "diktatur", "partei", "bündnis", "netzwerk",
})
