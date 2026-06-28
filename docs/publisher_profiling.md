# Publisher Profiling — Konzept & Umsetzung

Drei aufeinander aufbauende Analysen zur automatischen Charakterisierung von Medien-Herausgebern.  
Datenbasis und Schema: [reference.md](reference.md) | Auswertungsübersicht: [auswertungen.md](auswertungen.md)

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

## Feature 1 — Politische Richtung eines Herausgebers

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
- Neuer Backend-Endpoint `GET /profile/{domain}/stroemung`
- Aggregation der `politische_stroemung`-Metadaten aus ChromaDB
- Frontend: Balkendiagramm oder Radar-Chart pro Domain

### Aufwand
| Schritt | Aufwand |
|---|---|
| Aggregations-Endpoint | 1–2 Tage |
| Frontend-Visualisierung | 1–2 Tage |
| **Gesamt** | **⭐ 2–4 Tage** |

---

## Feature 2 — Abhängigkeitsprofil (Regierungsfreundlich, US-freundlich etc.)

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

### Schlüssel-Entitäten (konfigurierbar)
| Dimension | Entitäten |
|---|---|
| Regierungsfreundlich | Bundesregierung, Olaf Scholz, SPD, Koalition |
| Regierungskritisch | Opposition, AfD, CDU (je nach Kontext) |
| US-freundlich | USA, NATO, Biden, Trump, Washington |
| EU-freundlich | EU, Europäische Kommission, Brüssel, Ursula von der Leyen |
| Russland-freundlich | Russland, Putin, Kreml, Moskau |
| Chinafreundlich | China, Xi Jinping, Peking, KPCh |

### Umsetzung
- Entitäten-Liste als Konfigurationsdatei (YAML)
- Neuer Endpoint `GET /profile/{domain}/abhaengigkeit`
- Score: `(positiv - negativ) / gesamt` pro Dimension, normiert auf -1 bis +1
- Frontend: Heatmap oder Spinnen-Diagramm

### Aufwand
| Schritt | Aufwand |
|---|---|
| Schlüssel-Entitäten definieren + Konfig | 1 Tag |
| Aggregations-Endpoint | 1–2 Tage |
| Frontend-Visualisierung | 2–3 Tage |
| **Gesamt** | **⭐ ~1 Woche** |

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

| # | Feature | Aufwand | Datengrundlage |
|---|---|---|---|
| 1 | Politische Richtung | ⭐ 2–4 Tage | sofort verfügbar |
| 2 | Abhängigkeitsprofil | ⭐ ~1 Woche | sofort verfügbar |
| 3 | Paradigmenwechsel | ⭐⭐ 1–2 Wochen | nach 3–4 Wochen Feed |

Features 1 und 2 sind unabhängig voneinander und können parallel entwickelt werden.  
Feature 3 baut konzeptionell auf beiden auf und benötigt historische Daten.
