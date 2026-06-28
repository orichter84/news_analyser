# Auswertungsmöglichkeiten & Deep Learning

Übersicht möglicher Analysen auf Basis der gesammelten Artikeldaten.  
Für das Datenschema siehe [reference.md](reference.md). Für die Architektur siehe [analyse_architektur.md](analyse_architektur.md).

---

## Verfügbare Datenbasis

Pro Artikel werden gespeichert:

| Typ | Felder |
|---|---|
| **Numerisch** | `orwell_index`, `bernays_score`, `dunning_kruger_index` |
| **Kategorisch** | `domain`, `themenbereich`, `politische_stroemung`, `intended_sentiment` |
| **Textuell** | `main_narrative`, `target_direction`, `technique_names`, Rohartikel |
| **Strukturiert** | `detected_techniques` (mit Zitaten), `manipulation_targets` |
| **Vektoren** | Sentence-Transformer-Embeddings (ChromaDB, Cosine-Similarity) |
| **Metadaten** | `author`, `published_at`, `word_count`, `domain` |

---

## Auswertungen

### Niedrig — Umsetzung in Tagen, kein Training nötig

| Name | Beschreibung | Aufwand |
|---|---|---|
| **Manipulations-Fingerprint** | Charakteristisches Profil pro Domain aus Orwell/Bernays/DK-Index und häufigsten Techniken. Macht sichtbar, dass z.B. Spiegel eher Emotionalisierung nutzt, Welt eher Framing. | ⭐ 1–2 Tage |
| **Technik-Kookkurrenz** | Welche Manipulationstechniken treten zusammen auf? Assoziationsanalyse über alle Artikel — erkennt typische "Pakete" von Techniken. | ⭐ 1–2 Tage |
| **Trend-Analyse** | Zeitliche Entwicklung von Orwell/Bernays/DK pro Domain. Erkennt z.B. ob ein Medium nach bestimmten Ereignissen manipulativer wird. | ⭐ 1–2 Tage |
| **Anomalie-Erkennung** | Artikel die für ihre Domain statistisch auffällig sind (z.B. ungewöhnlich hoher Orwell-Index bei normalerweise neutraler Quelle). Funktioniert bereits mit wenig Daten. | ⭐ 2–3 Tage |
| **Themen-Clustering** | Unsupervised Clustering der ChromaDB-Embeddings (k-Means / HDBSCAN). Zeigt semantisch verwandte Themen unabhängig von der LLM-Klassifikation. | ⭐ 1–2 Tage |

---

### Mittel — Wochen, wenig bis kein gelabeltes Training nötig

| Name | Beschreibung | Aufwand |
|---|---|---|
| **Cross-Domain-Narrativ-Vergleich** | Wie berichten verschiedene Quellen über dasselbe Ereignis? Ähnlichste Artikel per Embedding-Suche, dann Vergleich von Scores und Techniken. | ⭐⭐ 1 Woche |
| **Semantische Drift-Erkennung** | Erkennt ob ein Thema über Zeit zunehmend einseitig geframt wird — z.B. "Ukraine" im Zeitverlauf per Embedding-Verschiebung. | ⭐⭐ 1–2 Wochen |
| **Politische Strömungs-Klassifikation** | Einfacher Klassifikator (SVM / Logistic Regression) auf Embeddings + Scores, der `politische_stroemung` vorhersagt. LLM-Labels dienen als Trainingsdaten. Benötigt ~200+ Artikel. | ⭐⭐ 1–2 Wochen |
| **Manipulations-Intensitäts-Vorhersage** | Regressionsmodell das aus Texteigenschaften (Satzlänge, Adjektivdichte, Passivkonstruktionen via spaCy) den Orwell-Index vorhersagt — ohne LLM. | ⭐⭐ 1–2 Wochen |

---

### Hoch — Monate, braucht viele Daten

| Name | Beschreibung | Aufwand |
|---|---|---|
| **Fine-tuning eines BERT-Modells** | Deutsches BERT (z.B. `deepset/gbert-base`) auf den gesammelten Artikeln fine-tunen, um Manipulationstechniken direkt zu klassifizieren — ohne LLM. Benötigt 1.000+ gelabelte Artikel. | ⭐⭐⭐ 2–3 Monate |
| **Schwache Supervision (Snorkel)** | LLM-Scores als "noisy labels" nutzen um ein kleines Modell zu trainieren, das später ohne LLM auskommt. Sinnvoll wenn Inferenzkosten gesenkt werden sollen. | ⭐⭐⭐ 2–3 Monate |
| **Narrative-Graph** | Wissensgraph der zeigt wie Narrative zwischen Domains und Zeit fließen — welche Quelle übernimmt Framing von welcher? Erfordert NLP-Pipeline und Graphdatenbank. | ⭐⭐⭐⭐ 3–6 Monate |

---

## Datenmenge als Voraussetzung

| Auswertungstyp | Mindestanzahl Artikel |
|---|---|
| Statistik, Clustering, Anomalie | ab ~50 |
| Einfache Klassifikatoren | ab ~200 |
| Fine-tuning Sprachmodelle | ab ~1.000–5.000 |

Bei stündlichem Feed-Betrieb (~5–15 neue Artikel/Stunde) sind die Schwellenwerte für einfache Klassifikatoren in wenigen Wochen erreichbar.

---

## Empfehlung für den Einstieg

**Manipulations-Fingerprint** und **Trend-Analyse** sind sofort umsetzbar, liefern direkt Erkenntnisse und bilden die Grundlage für spätere ML-Modelle. Als nächster Schritt bietet sich das **Themen-Clustering** auf den vorhandenen ChromaDB-Embeddings an, da die Infrastruktur dafür bereits vollständig vorhanden ist.
