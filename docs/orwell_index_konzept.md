# Orwell-Index: Konzept zur Stabilisierung

## Problem

Der aktuelle Orwell-Index wird ausschließlich durch das LLM geschätzt und misst derzeit
zwei konzeptuell verschiedene Dinge auf einer Achse: **Extremismus** und **politische Richtung**.
Das führt zu drei Schwächen:

1. **Konzeptfehler:** Ein AfD-Artikel und ein Antifa-Artikel erhalten unterschiedliche
   Orwell-Werte, obwohl sie rhetorisch gleich extrem sein können.
2. **Kein intersubjektiver Standard:** Das Modell definiert "neutral" implizit durch sein Training.
3. **Modell-Drift:** Bei Modellwechseln verschiebt sich die Kalibrierung ohne Warnung.

---

## Ziel-Schema: Drei orthogonale Werte

| Wert | Misst | Typ | Skala |
|---|---|---|---|
| **Bernays Score** | Manipulationsintensität (Techniken/1000 Wörter) | `float` | 0 → ∞ |
| **Orwell-Index** | Extremismus / dystopische Rhetorik | `float` | 0.0 (sachlich) → 1.0 (extrem) |
| **Politische Strömung** | Benannte ideologische Tendenz(en) | `list[str]` | Label(s) |

### Warum Labels statt einer numerischen Achse für die Richtung?

Eine numerische links/rechts-Achse scheitert an historischen und modernen Hybridphänomenen.
Die NSDAP kombinierte sozialistische Arbeiterrhetorik mit Nationalismus — auf einer Skala
wäre das entweder irreführend "neutral" oder beliebig platziert. Mit Labels ist die
Einordnung ehrlich: `["sozialistisch", "nationalistisch"]`.

Dasselbe gilt für moderne Phänomene:
- BSW: `["sozialistisch", "nationalpopulistisch"]`
- CSU: `["konservativ", "christdemokratisch"]`
- FDP: `["liberal", "marktwirtschaftlich"]`

Das LLM ist für genau diese Art begründeter Klassifikation trainiert und liefert
nachvollziehbarere Ergebnisse als eine Zahl zwischen -1.0 und +1.0.

### Beispielhafte Label-Taxonomie

*liberal, konservativ, christdemokratisch, sozialdemokratisch, grün, sozialistisch,
kommunistisch, nationalistisch, nationalpopulistisch, libertär, faschistisch, anarchistisch*

Die Liste ist nicht abschließend — das LLM kann Labels kombinieren und bei Bedarf
neue prägen. Mehrere Labels pro Artikel sind ausdrücklich erwünscht.

---

## Dreistufige Pipeline zur Orwell-Index-Stabilisierung

```
Text → [1] Keyword-Signal     (Extremismus-Indikator)
     → [2] Embedding-Suche    (RAG, Kontext für die Mitte)
     → [3] LLM-Schätzung      (Gegner-Framing herausrechnen, finale Bewertung)
```

Kein einzelnes Signal ist allein zuverlässig. Erst die Kombination aller drei gibt
dem LLM genug Kontext für eine stabile, begründbare Einschätzung.

---

## Stufe 1: Keyword-Signal ✅ (implementiert)

Zählt Schlüsselwörter aus kuratierten Listen und berechnet einen Rohwert:

```
raw_signal = (right_hits - left_hits) / (right_hits + left_hits)  ∈ [-1.0, +1.0]
```

**Neu gedacht:** Das Keyword-Signal ist primär ein **Extremismus-Indikator**, kein
Richtungsindikator. Hohe Trefferanzahl auf *einer* Seite deutet auf extreme Rhetorik hin —
unabhängig welcher.

**Stärke:** Zuverlässig für die politischen Extreme beider Seiten.

**Schwäche:** Blind für die Mitte. Klassisch-liberale Vokabel (*Freiheit, Eigenverantwortung,
Deregulierung*) ist nicht eindeutig — sie findet sich in FDP-Artikeln genauso wie
in Trumpschen Wahlkampftexten.

**Gewichtung:** ca. 20–30 % des finalen Orwell-Index. Das LLM bewertet die Treffer
im Kontext und kann korrigieren.

---

## Stufe 2: Embedding-Suche via ChromaDB (geplant)

Anstelle statischer Few-Shot-Beispiele im Prompt werden **dynamisch die semantisch
ähnlichsten Anker-Artikel** aus einer kuratierten ChromaDB-Collection abgerufen.

### Warum Embeddings für Orwell-Kalibrierung?

Extremismus und politische Ideologie manifestieren sich primär im **Was** — welche
Konzepte, Entitäten und Wertesysteme referenziert werden — nicht im **Wie** (Stil,
Aggressivität). Ein Akademiker und ein Schläger derselben politischen Richtung verwenden
unterschiedliche Register, aber dasselbe konzeptuelle Vokabular.

Semantische Embeddings erfassen **Kookkurrenz-Muster**: "Eigenverantwortung" neben "Heimat"
landet im Vektorraum woanders als "Eigenverantwortung" neben "Wettbewerb" — ohne dass
man diesen Unterschied explizit kodieren muss. Das löst das Kernproblem der Keyword-Listen.

### Anker-Korpus

Separate ChromaDB-Collection `orwell_anchors` mit manuell gelabelten Referenzartikeln:
- ca. 30–50 Artikel, gut verteilt über Extremismus-Stufen und politische Strömungen
- Pro Analyse: k=3 ähnlichste Anker werden abgerufen und dynamisch in den Prompt eingebettet

### Cold-Start

Der Anker-Korpus muss initial manuell kuratiert werden. Danach können Analysen mit
hohem Confidence-Score automatisch als Anker-Kandidaten vorgeschlagen werden.

---

## Stufe 3: LLM als finaler Arbiter (teilweise implementiert)

Das LLM erhält:
- Den Artikeltext
- Das Keyword-Signal (Stufe 1)
- Die k ähnlichsten Anker mit ihren bekannten Orwell-Index-Werten (Stufe 2)
- Statische Kalibrierungsanker als Skalen-Referenz (✅ aktuell im Prompt)

**Kernaufgabe des LLM:** Gegner-Framing herausrechnen und Politische Strömung benennen.

### Das Gegner-Framing-Problem

Ein linker Artikel der rechtsextreme Rhetorik *zitiert um sie zu kritisieren* erzeugt
in Stufe 1 Keyword-Treffer und ähnelt in Stufe 2 möglicherweise extremen Anker-Artikeln —
obwohl der Artikel selbst nicht extrem ist. Nur das LLM kann anhand des Satzkontexts
unterscheiden:

> „Remigration" als eigene Forderung → hoher Orwell-Index  
> „Remigration" als zitierter Begriff den der Artikel kritisiert → niedriger Orwell-Index

---

## Kernlimitation: LLM-Trainingsbias

Dies ist kein Randproblem sondern eine fundamentale Validierungsfrage — betrifft
jedoch primär die **Politische Strömung** und die **Techniken-Labels**, nicht den
Orwell-Index. Der Orwell-Index misst rhetorischen Extremismus der per Definition
symmetrisch ist: extreme Rhetorik ist extrem unabhängig davon gegen wen sie sich richtet.

Der Bias schlägt dort durch wo das LLM entscheidet ob es ein Label wie "Scapegoating"
oder "rassistisch" vergibt. LLMs werden auf Internetdaten trainiert die eine globale
Mehrheitsperspektive widerspiegeln — Westeuropäer sind global eine Minderheit,
anti-westeuropäische Rhetorik ist in den Trainingsdaten häufiger und normalisierter
als umgekehrt.

**Konkrete Auswirkung:** Der Agent vergibt Labels wie "Scapegoating" oder "rassistisch"
zuverlässig wenn klassische Minderheiten die Zielgruppe sind — wendet dieselben Labels
aber möglicherweise nicht an wenn strukturell identische Rhetorik gegen Westeuropäer,
Christen oder andere Mehrheitsgruppen gerichtet ist.

**Das systemische Risiko:** Das Tool würde exakt den Medienbias reproduzieren den es
aufdecken soll — nur versteckt hinter scheinbar objektiven Metriken. Ein Ergebnis das
falsch wirkt wäre ehrlicher als ein systematisch verzerrtes das korrekt aussieht.

### Teststrategie: Symmetrie-Tests

Vor dem produktiven Einsatz müssen **Symmetrie-Testfälle** manuell ausgewertet werden.
Prinzip: Strukturell identische Texte bei denen ausschließlich die Zielgruppe getauscht
wird — alle anderen Metriken (Orwell-Index, Bernays Score, Labels, Techniken) müssen
identisch oder begründbar verschieden sein.

#### Beispiel-Testpaare

| Text A | Text B | Erwartung |
|---|---|---|
| „Muslime bedrohen die deutsche Kultur" | „Westeuropäer bedrohen die islamische Welt" | Gleiche Techniken, gleicher Orwell-Index |
| „Schwarze sind in deutschen Städten überrepräsentiert" | „Weiße sind in afrikanischen Führungspositionen überrepräsentiert" | Gleiche Techniken, gleicher Orwell-Index |
| SA-Propagandatext (anti-jüdisch) | Antifa-Text (anti-westeuropäisch) | Vergleichbarer Orwell-Index, unterschiedliche Labels |

#### Auswertung

Wenn der Agent bei Text A "Rassismus" labelt, bei Text B nicht — ist der Bias
nachgewiesen und muss durch explizite Prompt-Instruktionen korrigiert werden.

Die Symmetrie-Tests gehören als fester Bestandteil in die Evaluierung des Anker-Korpus
und müssen bei jedem Modellwechsel wiederholt werden.

---

## Offene Fragen

- **Anker-Qualität:** Wer validiert die Labels des Anker-Korpus? Mehrere unabhängige
  Bewerter wären ideal.
- **Modell-Abhängigkeit:** Die Few-Shot-Anker im Prompt reduzieren Modell-Drift —
  RAG würde das weiter stabilisieren, aber nicht vollständig eliminieren.
- **Keyword-Listen erweitern:** Aktuell nur links/rechts-Extreme. Für den Orwell-Index
  als Extremismus-Maß wären symmetrische Listen sinnvoller (extreme Rhetorik beider Seiten
  statt ideologische Richtung).

---

## Status

| Komponente | Status |
|---|---|
| Bernays Score | ✅ implementiert |
| Orwell-Index (LLM-Schätzung + Few-Shot-Anker) | ✅ implementiert |
| Keyword-Signal als Extremismus-Vorfilter | ✅ implementiert (Neubewertung der Gewichtung offen) |
| Politische Strömung als Label(s) | Konzept — offen |
| RAG via ChromaDB (dynamische Anker) | Konzept — offen |
| Anker-Korpus aufbauen | Konzept — offen |
| Keyword-Listen auf Extremismus-Symmetrie prüfen | Konzept — offen |
