# Publisher Profiling — Konzept & Umsetzung

Drei aufeinander aufbauende Analysen zur automatischen Charakterisierung von Medien-Herausgebern.  
Datenbasis und Schema: [reference.md](reference.md) | Auswertungsübersicht: [auswertungen.md](auswertungen.md)

**Status:** Feature 1 und 2 sind implementiert (seit `536e16f`, 2026-06-28) — beide teilen sich einen gemeinsamen Endpoint statt der ursprünglich getrennt geplanten Routen. Feature 3 ist weiterhin offen.

---

## Vorhandene Datenbasis

Alle drei Features nutzen ausschließlich bereits gespeicherte Felder — **keine Prompt-Änderungen nötig**.

| Feld | Inhalt | Relevant für |
|---|---|---|
| `politische_stroemung` | LLM-Label pro Artikel (links, konservativ, liberal …) | Feature 1 |
| `manipulation_targets[].entity` | Name der Entität (Bundesregierung, USA, Putin …) | Feature 2 |
| `manipulation_targets[].direction` | positiv \| negativ \| neutral | Feature 2 |
| `manipulation_targets[].rolle` | Held \| Feind \| Sündenbock \| Versager … | Feature 2 |
| `domain` | Herausgeber-Domain | alle |
| `published_at` | Erscheinungsdatum | Feature 3 |

---

## Feature 1 — Politische Richtung eines Herausgebers ✅ Implementiert

### Idee
Aggregation der pro-Artikel vorhandenen `politische_stroemung`-Labels auf Domain-Ebene ergibt ein politisches Profil des Mediums.

### Beispiel
```
spiegel.de (42 Artikel):
  links:        67 %
  liberal:      50 %
  sozialdemokratisch: 31 %
  neutral:      17 %
  konservativ:   5 %
```

### Umsetzung
- Endpoint `GET /stats/publisher` (`backend/routers/stats.py`), liefert pro Domain ein `stroemung`-Feld mit Häufigkeiten je Label
- Aggregation in `publisher_profiles()` (`src/news_analyser/stats.py:372`)
- Frontend: `stats-publisher.component` — Balkendiagramm pro Domain in der Detailansicht ("Politische Strömung")

---

## Feature 2 — Abhängigkeitsprofil (Regierungsfreundlich, US-freundlich etc.) ✅ Implementiert

### Idee
`manipulation_targets` enthält bereits für jeden Artikel, wie jede Entität dargestellt wird (`direction`, `rolle`). Aggregiert man dies über alle Artikel einer Domain für definierte Schlüssel-Entitäten, ergibt sich ein Abhängigkeitsprofil — **ohne Prompt-Änderung**.

### Beispiel
```
welt.de, Entität "USA" (31 Artikel):
  positiv: 28×  negativ: 3×  neutral: 5×
  häufigste Rolle: Autorität
  → us_freundlich: 0.82

spiegel.de, Entität "Bundesregierung" (54 Artikel):
  positiv: 12×  negativ: 34×  neutral: 8×
  häufigste Rolle: Versager
  → regierungskritisch: 0.71
```

### Schlüssel-Entitäten
Zwei Gruppen, hartkodiert in `_DEPENDENCY_ENTITIES` (`src/news_analyser/stats.py:254`) — keine YAML-Konfiguration, da bisher kein Bedarf für Laufzeit-Anpassung bestand:

| Dimension | Entitäten (Auszug) |
|---|---|
| Regierungsfreundlich | Bundesregierung, Olaf Scholz, Ampel, Koalition, Bundesminister |
| US-freundlich | USA, NATO, Washington, Biden, Trump, Pentagon |
| EU-freundlich | EU, Europäische Union, Brüssel, von der Leyen, Europäische Kommission |
| Russland-freundlich | Russland, Putin, Kreml, Moskau |
| China-freundlich | China, Xi Jinping, Peking, KPCh |
| SPD / CDU-CSU / Grüne / FDP / AfD / BSW / Linke | je Partei: Kurzform, führende Politiker:innen |

Die Parteiprofile (SPD…Linke) gehen über den ursprünglichen Vorschlag hinaus und wurden zusätzlich zu den geopolitischen Dimensionen umgesetzt.

### Umsetzung
- Gemeinsamer Endpoint mit Feature 1: `GET /stats/publisher`, Feld `abhaengigkeit` pro Domain
- Score: `(positiv - negativ) / gesamt` pro Dimension, normiert auf -1 bis +1 — exakt wie ursprünglich vorgeschlagen
- Frontend: `stats-publisher.component` — Kartenraster mit horizontalem Score-Balken je Dimension, getrennt nach "Geopolitisches Profil" und "Parteiprofil" (kein Heatmap/Spinnen-Diagramm)

---

## Feature 3 — Erkennen von Paradigmenwechseln

### Idee
Die Profile aus Feature 1 und 2 werden als Zeitreihe betrachtet. Signifikante Sprünge in diesen Zeitreihen markieren Paradigmenwechsel — z.B. ein Medium das zuvor regierungskritisch war und plötzlich regierungsfreundlich berichtet.

### Beispiel
```
spiegel.de — Dimension "regierungsfreundlich", monatlich:
  Jan: -0.62   (stark kritisch)
  Feb: -0.58
  Mär: -0.21   ← Wechsel erkannt
  Apr: +0.14   (zunehmend freundlich)
  Mai: +0.31
```

### Mögliche Ursachen (manuell zu interpretieren)
- Redaktionelle Neuausrichtung / Chefredakteurswechsel
- Eigentümerwechsel
- Reaktion auf politisches Ereignis (Wahl, Krise, Krieg)

### Technische Umsetzung
- Zeitreihe: monatliche Aggregation der Profile
- Change-Point-Detection: Python-Bibliothek `ruptures` (PELT-Algorithmus)
- Ausgabe: Zeitpunkte + betroffene Dimension + Stärke des Wechsels
- Frontend: Zeitstrahl mit markierten Wechselpunkten

### Aufwand
| Schritt | Aufwand |
|---|---|
| Zeitreihen-Aggregation per Domain/Monat | 2–3 Tage |
| Change-Point-Detection (`ruptures`) | 1–2 Tage |
| Frontend-Zeitstrahl | 3–5 Tage |
| **Gesamt** | **⭐⭐ 1–2 Wochen** |

> **Voraussetzung:** Mindestens 3–4 Wochen Feed-Betrieb mit ausreichend Artikeln pro Domain.

---

## Gesamtübersicht & empfohlene Reihenfolge

| # | Feature | Status | Datengrundlage |
|---|---|---|---|
| 1 | Politische Richtung | ✅ Implementiert (`GET /stats/publisher`) | sofort verfügbar |
| 2 | Abhängigkeitsprofil | ✅ Implementiert (`GET /stats/publisher`) | sofort verfügbar |
| 3 | Paradigmenwechsel | offen — ⭐⭐ geschätzt 1–2 Wochen | nach 3–4 Wochen Feed |

Feature 3 baut konzeptionell auf den Profilen aus 1 und 2 auf und benötigt historische Daten (Zeitreihe je Domain/Monat).
