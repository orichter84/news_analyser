# Test 1 — Ergebnisse: Klasse 1 (Satzebene NN-Suche)

Methodik: verifizierte Technik-Zitate aus der Pipeline-DB als NN-Referenzmenge, neue Testsätze
per Nearest-Neighbor dagegen abgefragt. Siehe [klasse1_nn_validation.ipynb](klasse1_nn_validation.ipynb).

**Status:** noch nicht durchgeführt.

---

## Setup

- Embedding-Modell:
- Größe der Referenzmenge (Anzahl Technik-Zitate, Anzahl Techniken):
- Anzahl / Herkunft der Testsätze:

## Beobachtungen

### Sätze aus der Trainingsmenge

| satz | erwartet | rang | gefunden_technik | distanz | zitat_match |
|---|---|---|---|---|---|
| Trump: Waffenruhe mit Iran vorbei, „die sind k... | Framing | 1 | Framing | 0.135 | Person-A: Waffenruhe mit Iran vorbei, „die sin... |
| Trump: Waffenruhe mit Iran vorbei, „die sind k... | Framing | 2 | Framing | 0.375 | Ärger wegen Irankrieg |
| Trump: Waffenruhe mit Iran vorbei, „die sind k... | Framing | 3 | Omission | 0.596 | Die USA greifen Angaben aus Teheran zufolge na... |
| Trump schimpfte über die Mullahs: „Die sind kr... | Loaded Language | 1 | Framing | 0.507 | über den im Vorfeld flüsternd allerlei Unfreun... |
| Trump schimpfte über die Mullahs: „Die sind kr... | Loaded Language | 2 | Loaded Language | 0.517 | kranke Leute |
| Trump schimpfte über die Mullahs: „Die sind kr... | Loaded Language | 3 | Framing | 0.527 | Person-A: Waffenruhe mit Iran vorbei, „die sin... |
| Die USA greifen Angaben aus Teheran zufolge na... | Omission | 1 | Omission | 0.095 | Die USA greifen Angaben aus Teheran zufolge na... |
| Die USA greifen Angaben aus Teheran zufolge na... | Omission | 2 | Framing | 0.518 | Ärger wegen Irankrieg |
| Die USA greifen Angaben aus Teheran zufolge na... | Omission | 3 | Loaded Language | 0.673 | angreifskriegs |
| Nahe der Hafenstadt Buschehr seien mindestens ... | — | 1 | Omission | 0.477 | Die USA greifen Angaben aus Teheran zufolge na... |
| Nahe der Hafenstadt Buschehr seien mindestens ... | — | 2 | Loaded Language | 0.544 | angreifskriegs |
| Nahe der Hafenstadt Buschehr seien mindestens ... | — | 3 | Framing | 0.590 | Ärger wegen Irankrieg |
| Der Iran müsse aber jetzt wirklich verstehen, ... | — | 1 | Framing | 0.431 | Ärger wegen Irankrieg |
| Der Iran müsse aber jetzt wirklich verstehen, ... | — | 2 | Framing | 0.456 | Person-A: Waffenruhe mit Iran vorbei, „die sin... |
| Der Iran müsse aber jetzt wirklich verstehen, ... | — | 3 | Framing | 0.541 | Hinter vorgehaltener Hand wird in der Partei a... |

### Unbekannte Sätze

| satz | erwartet | rang | gefunden_technik | distanz | zitat_match |
|---|---|---|---|---|---|
| Person-D Vorgänger, der im April abgewählte Pe... | Framing | 1 | Framing | 0.435 | Person-Q sei sehr fleißig gewesen und in Satzu... |
| Person-D Vorgänger, der im April abgewählte Pe... | Framing | 2 | Loaded Language | 0.516 | Der Kanzler auf Person-B Abschussliste |
| Person-D Vorgänger, der im April abgewählte Pe... | Framing | 3 | Loaded Language | 0.516 | Der Kanzler auf Person-B Abschussliste |
| Die Nachrichtensendungen des staatlichen Ferns... | Loaded Language | 1 | Loaded Language | 0.556 | Anstelle des Lügenpresse-Vorwurfs |
| Die Nachrichtensendungen des staatlichen Ferns... | Loaded Language | 2 | Loaded Language | 0.568 | Verzicht auf die sogenannte 'Friedensdividende' |
| Die Nachrichtensendungen des staatlichen Ferns... | Loaded Language | 3 | Framing | 0.571 | Diese Verschränkung zwischen dem Familienimper... |

## Distanz-Schwellenwert

**Befund: kein tragfähiger globaler Schwellenwert.**

In der Trainingsmenge (Sätze, die nahezu wortgleich mit ihrer eigenen Referenz sind) liegen
korrekte Treffer bei 0.095–0.135, klar getrennt vom Rest (≥ 0.375). Das hätte für einen
Schwellenwert von < 0.2 gesprochen.

Bei den unbekannten Sätzen (Stufe 2) liegen die korrekten Top-1-Treffer aber bei 0.435 und 0.556
— **im selben Band wie die Negativbeispiele aus Stufe 1** (0.431–0.541, Sätze ohne erwartete
Technik). Ein einzelner globaler Abstand kann "richtiger, aber entfernter Treffer auf neuem Text"
und "korrekt kein Treffer" damit nicht auseinanderhalten:

| Fall | Distanzbereich |
|---|---|
| Korrekter Treffer, Text ≈ Referenz (Stufe 1) | 0.095–0.135 |
| Korrekter Top-1-Treffer, unbekannter Text (Stufe 2) | 0.435–0.556 |
| Kein Treffer erwartet (Negativbeispiele, Stufe 1) | 0.431–0.541 |

Erkennung scheint eher über den **Rang** zu funktionieren (Top-1-Match war in beiden Stufe-2-Fällen
korrekt) als über einen **absoluten Abstand** — die Kernannahme aus dem Konzept ("Label wird bei
ausreichender Nähe übernommen") trägt in dieser Form nicht.

**Offene Richtungen für die weitere Kalibrierung:**
1. Relativer Abstand statt fixer Schwelle — z. B. Marge zwischen Rang 1 und Rang 2/3, oder Abstand
   zur Verteilung der Negativ-Distanzen statt einer festen Zahl.
2. Referenzmenge ist noch dünn — einige Techniken haben nur 1–3 Beispiele (siehe Setup), das macht
   "Nähe" pro Technik verrauscht; mit mehr Beispielen könnte sich die Trennung verbessern.

## Embedding-Modell-Vergleich (Konzept-Punkt 4)

`paraphrase-multilingual-mpnet-base-v2` vs. `all-MiniLM-L6-v2` — bildet das erste Modell
tatsächlich strukturelle/rhetorische statt nur thematische Nähe besser ab?

## Fazit / Konsequenz für das Konzept

<!-- z.B.: Schwellenwert X festgelegt, Modell Y gewählt, Klasse 1 für Techniken A/B/C geeignet,
für D/E ungeeignet (zu breite Streuung, siehe Konzept "Thema als zusätzliche Dimension") -->
