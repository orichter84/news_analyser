"""
Keyword-basierter Themenvorfilter für RSS-Feeds.

Klassifiziert Artikel anhand von Titel und Beschreibung — ohne LLM-Call.
Wird vor der Analyse ausgeführt um irrelevante Artikel auszuschließen.
"""

from __future__ import annotations

TOPIC_KEYWORDS: dict[str, list[str]] = {
    "Politik": [
        "bundestag", "bundesrat", "bundesregierung", "minister", "kanzler",
        "partei", "wahl", "koalition", "opposition", "parlament", "abgeordnete",
        "gesetz", "reform", "debatte", "abstimmung", "regierung", "spd", "cdu",
        "csu", "grüne", "fdp", "afd", "linke", "bsw", "demokratie", "politiker",
    ],
    "Außenpolitik": [
        "ukraine", "russland", "nato", "eu ", "europäisch", "außenminister",
        "diplomat", "sanktion", "krieg", "konflikt", "usa", "china", "israel",
        "gaza", "iran", "türkei", "putin", "trump", "biden", "macron",
        "vereinte nationen", "un-", "außenpolitik", "botschaft", "g7", "g20",
    ],
    "Wirtschaft": [
        "wirtschaft", "inflation", "euro", "börse", "dax", "unternehmen",
        "konzern", "aktie", "bank", "finanzen", "haushalt", "schulden",
        "arbeitslosigkeit", "tarif", "gewerkschaft", "streik", "industrie",
        "energiepreise", "rezession", "wachstum", "bruttoinlandsprodukt",
    ],
    "Gesellschaft": [
        "migration", "flüchtling", "asyl", "integration", "diskriminierung",
        "rassismus", "feminismus", "gleichstellung", "armut", "sozialhilfe",
        "bildung", "schule", "universität", "kriminalität", "gewalt",
        "demonstration", "protest", "zivilgesellschaft", "bürgerrecht",
    ],
    "Justiz": [
        "gericht", "urteil", "verurteil", "richter", "staatsanwalt", "klage",
        "prozess", "strafrecht", "verfassung", "bundesverfassungsgericht",
        "europäischer gerichtshof", "freispruch", "haft", "strafverfolgung",
    ],
    "Gesundheit": [
        "gesundheit", "krankenhaus", "impf", "pandemie", "virus", "krankheit",
        "medizin", "pharma", "pflege", "krankenkasse", "arzt", "therapie",
    ],
    "Klima": [
        "klima", "umwelt", "co2", "emissionen", "erneuerbar", "solar",
        "windenergie", "klimawandel", "erderwärmung", "naturkatastrophe",
        "überschwemmung", "dürre", "nachhaltigkeit", "klimaschutz",
    ],
    "Technologie": [
        "technologie", "tech", "digital", "software", "hardware", "internet",
        "künstliche intelligenz", "algorithmus", "datenschutz", "cybersicherheit",
        "atomkraft", "kernkraft", "kernenergie", "atomenergie", "reaktor",
        "windkraft", "windrad", "solaranlage", "photovoltaik", "energiewende",
        "strommix", "strompreis", "gasnetz", "wasserstoff", "kohleausstieg",
        "netzausbau", "elektromobilität", "verbrenner", "laufzeit",
        "abschalten", "kraftwerk", "ki ", "chatgpt", "plattform",
    ],
}

# Themen die standardmäßig analysiert werden
DEFAULT_ALLOWED_TOPICS = {
    "Politik", "Außenpolitik", "Wirtschaft", "Gesellschaft", "Justiz", "Technologie",
}


def classify_topic(title: str, summary: str = "") -> str | None:
    """Gibt das passendste Thema zurück oder None wenn kein Match."""
    text = (title + " " + summary).lower()
    scores: dict[str, int] = {}
    for topic, keywords in TOPIC_KEYWORDS.items():
        hits = sum(1 for kw in keywords if kw in text)
        if hits:
            scores[topic] = hits
    if not scores:
        return None
    return max(scores, key=lambda t: scores[t])


def is_relevant(title: str, summary: str, allowed_topics: set[str]) -> tuple[bool, str | None]:
    """
    Gibt (relevant, topic) zurück.
    relevant=True wenn das Thema in allowed_topics liegt oder allowed_topics leer ist.
    """
    if not allowed_topics:
        return True, classify_topic(title, summary)
    topic = classify_topic(title, summary)
    return (topic in allowed_topics, topic)
