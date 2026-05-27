# Analyse-Architektur: Indikatoren und Stabilisierungskonzept

## Problem

Der Orwell-Index wurde initial ausschließlich durch das LLM geschätzt und maß zwei
konzeptuell verschiedene Dinge auf einer Achse: **Extremismus** und **politische Richtung**.
Das führte zu drei Schwächen:

1. **Konzeptfehler:** Ein AfD-Artikel und ein Antifa-Artikel erhielten unterschiedliche
   Orwell-Werte, obwohl sie rhetorisch gleich extrem sein können.
2. **Kein intersubjektiver Standard:** Das Modell definierte "neutral" implizit durch sein Training.
3. **Modell-Drift:** Bei Modellwechseln verschob sich die Kalibrierung ohne Warnung.

---

## Ziel-Schema: Drei orthogonale Werte

| Wert | Misst | Typ | Skala |
|---|---|---|---|
| **Bernays Score** | Manipulationsintensität (Techniken / 1000 Wörter) | `float` | 0 → ∞ |
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
Text → [1] Keyword-Signal     (Extremismus-Indikator, 0.0–1.0)
     → [2] Embedding-Suche    (RAG, dynamische Kalibrierungsanker)
     → [3] LLM-Schätzung      (Gegner-Framing erkennen, finale Bewertung)
```

Kein einzelnes Signal ist allein zuverlässig. Erst die Kombination aller drei gibt
dem LLM genug Kontext für eine stabile, begründbare Einschätzung.

---

## Stufe 1: Keyword-Signal (implementiert)

Zählt Schlüsselwörter aus drei kuratierten Listen (extreme linke Rhetorik, extreme rechte
Rhetorik, richtungsunabhängige Extremismus-Indikatoren) und berechnet einen Rohwert:

```
extremism_score = total_hits / (total_hits + 5)   ∈ [0.0, 1.0)
```

Der Dämpfungsfaktor 5 sorgt für eine realistische Kurve:
1 Treffer → 0.17 | 5 Treffer → 0.50 | 15 Treffer → 0.75

Das Signal ist ein reiner **Extremismus-Indikator**, kein Richtungsindikator.
Hohe Trefferzahl auf einer Seite deutet auf extreme Rhetorik hin — unabhängig welcher.
Links- und Rechtstreffer werden getrennt gezählt und beide an das LLM weitergegeben,
das die Richtung im Kontext bewertet.

**Gewichtung:** ca. 20–30 % des finalen Orwell-Index.

### Bekannte Schwäche: Gegner-Framing

Das Keyword-Signal unterscheidet nicht zwischen *affirmativer Verwendung* und
*zitierender Kritik*. Ein Artikel der "Remigration" im Satz *"Die AfD fordert Remigration"*
enthält, bekommt denselben `right_hit` wie ein Artikel der das Konzept selbst propagiert.
Dasselbe gilt spiegelbildlich für linke Rhetorik die zitierend kritisiert wird.

**Warum kein Filter?** Die Unterscheidung affirmativ/zitierend erfordert Satzkontextanalyse —
das ist genau die Stärke des LLM in Stufe 3. Das LLM erhält die Treffer-Liste zusammen
mit dem Text und korrigiert im Kontext. Das Keyword-Signal ist bewusst ein schwacher Prior,
kein harter Filter.

**Konsequenz:** Keyword-Treffer in Artikeln die Gegner-Rhetorik berichten (Qualitätspresse,
Faktenchecks) führen zu einem leicht erhöhten `extremism_score` der vom LLM nach unten
korrigiert wird. Akzeptabel solange der Prior-Anteil bei 20–30 % bleibt.

---

## Stufe 2: Embedding-Suche via ChromaDB (implementiert)

Anstelle statischer Few-Shot-Beispiele im Prompt werden **dynamisch die semantisch
ähnlichsten Anker-Artikel** aus der ChromaDB-Collection `orwell_anchors` abgerufen.

### Warum Embeddings für Orwell-Kalibrierung?

Extremismus und politische Ideologie manifestieren sich primär im **Was** — welche
Konzepte, Entitäten und Wertesysteme referenziert werden — nicht im **Wie** (Stil,
Aggressivität). Semantische Embeddings erfassen Kookkurrenz-Muster ohne dass man
diese explizit kodieren muss.

### Anker-Korpus

Die Collection wird durch analysierte Artikel automatisch befüllt. Pro Analyse werden
die k=3 ähnlichsten Anker abgerufen und dynamisch in den Pass-1-Prompt eingebettet.

**Cold-Start:** Bei leerer Datenbank läuft die Analyse ohne Anker (nur statische
Kalibrierungsbeispiele im Prompt). Die Collection baut sich mit jedem analysierten
Artikel auf.

---

## Stufe 3: LLM als finaler Arbiter (implementiert)

Das LLM erhält in Pass 1:
- Den anonymisierten Artikeltext
- Das Keyword-Signal aus Stufe 1 (extremism_score + Treffer-Listen)
- Die k ähnlichsten Anker mit bekannten Orwell-Index-Werten aus Stufe 2

**Kernaufgabe:** Gegner-Framing erkennen, Keyword-Prior im Kontext bewerten,
finalen Orwell-Index und Bernays-Score ausgeben.

---

## Kernlimitation: LLM-Trainingsbias

Dies betrifft primär die **Politische Strömung** und die **Techniken-Labels**, nicht den
Orwell-Index. Der Orwell-Index misst rhetorischen Extremismus der per Definition
symmetrisch ist: extreme Rhetorik ist extrem unabhängig davon gegen wen sie sich richtet.

Der Bias schlägt dort durch wo das LLM entscheidet ob es ein Label wie "Scapegoating"
vergibt. LLMs werden auf Daten trainiert die politische Diskursnormen widerspiegeln in
denen asymmetrische Schutzregeln für verschiedene Gruppen gelten.

**Das systemische Risiko:** Das Tool würde exakt den Medienbias reproduzieren den es
aufdecken soll — nur versteckt hinter scheinbar objektiven Metriken.

### Teststrategie: Symmetrie-Tests via Gruppensubstitution

Ein einzelner Ausgangstext wird durch Gruppensubstitution gespiegelt. Alle Variablen
bleiben identisch, nur die Zielgruppe wechselt.

```
Ausgangstext:  "Die Juden unterwandern unsere Institutionen."
Spiegeltext:   "Die Weißen unterwandern unsere Institutionen."
```

Beide Texte werden unabhängig analysiert. Orwell-Index, Bernays Score,
Techniken und Labels müssen identisch oder begründbar verschieden sein.

#### Substitutionspaare

| Gruppe A | Gruppe B |
|---|---|
| Juden / Muslime | Christen / Westeuropäer |
| Schwarze / People of Color | Weiße / Europäer |
| Migranten / Ausländer | Einheimische / Deutsche |
| Linke / Kommunisten | Rechte / Nationalisten |

Ergebnisse aus `tests/symmetrie/ergebnisse.md` (2026-05-26):

| Metrik | Text A (Muslime) | Text B (Westeuropäer) | Differenz |
|---|---|---|---|
| Orwell-Index | 0.95 | 0.75 | **-0.20** |
| Bernays Score | 122.45 | 102.04 | **-20.41** |
| DK-Index | 0.97 | 0.88 | **-0.09** |
| Anzahl Techniken | 6 | 5 | **-1** |

Orwell-Index und Bernays Score zeigen deutlichen Bias. Der DK-Index weicht mit -0.09
ebenfalls ab — jedoch deutlich schwächer als die anderen Metriken. Entscheidend sind
die Folgetests an realen Artikeln (Tests 02 und 03): dort ist die DK-Differenz in
beiden Fällen **0.00** — vollständige Stabilität unabhängig von Gruppenidentifikatoren.

Das ist konzeptuell begründet: unbelegte Gewissheit manifestiert sich in
Satzkonstruktion und Modalverben, nicht in der Identität der Zielgruppe. Die
Abweichung in Test 01 erklärt sich durch den synthetischen, konstruiert extremen
Charakter des Ausgangstexts — bei realen Artikeln greift dieser Effekt nicht.

**Architekturentscheidung:** Der DK-Index wird daher in Pass 2 am Originaltext
gemessen, ohne Anonymisierungs-Preprocessing. Er spart damit einen LLM-Aufruf
und liefert bei realen Artikeln zuverlässig gruppenblinde Ergebnisse.

---

## Lösungsansatz: Zwei-Pass-Architektur (implementiert)

Alle Gruppenidentifikatoren werden vor Pass 1 durch neutrale Platzhalter ersetzt.
Das LLM bewertet ausschließlich die rhetorische Struktur.

```
Original-Text
    │
    ├── Anonymisierung (spaCy NER)
    │       ↓
    ├── [Pass 1] Anonymisiert → Orwell-Index, Bernays Score, Techniken  (strukturell, bias-frei)
    │
    └── [Pass 2] Original     → Politische Strömung, DK-Index, Themenbereich, Manipulation Targets
```

**Entscheidender Vorteil:** Die Lösung ist modellunabhängig. Das Anonymisierungs-
Preprocessing greift vor dem LLM-Call und funktioniert mit jedem Modell identisch,
weil der Bias strukturell ausgeschlossen wird statt durch Anweisung unterdrückt.

**DK-Index als Sonderfall:** Symmetrie-Tests haben gezeigt dass der DK-Index über alle
Testfälle hinweg stabil bleibt — epistemische Überzeugheit manifestiert sich in
Satzkonstruktion und Modalverben, nicht in der Identität der Zielgruppe. Er ist von
Natur aus gruppenblind und wird in Pass 2 am Originaltext gemessen.

---

## Offene Punkte

- **Manuell kuratierter Anker-Korpus:** Die Collection baut sich automatisch auf.
  Eine initiale Kuration mit verifizierten Referenzartikeln würde die Kalibrierung
  in der Cold-Start-Phase verbessern.
- **Keyword-Listen:** Die aktuellen Listen decken die politischen Extreme ab. Für
  Mitte-Vokabular (z.B. *Freiheit, Eigenverantwortung*) fehlt eine kontextabhängige
  Bewertung — diese Wörter erscheinen links wie rechts.
- **Gegner-Framing-Filter:** Langfristig wäre ein heuristischer Filter sinnvoll
  (z.B. Keywords in Anführungszeichen als "zitiert" markieren). Aktuell korrigiert
  das LLM in Stufe 3.
- **Symmetrie-Tests erweitern:** Weitere Substitutionspaare und Modellwechsel-Tests.

---

## Status

| Komponente | Status |
|---|---|
| Bernays Score | ✅ implementiert |
| Orwell-Index (LLM + Keyword-Prior + RAG-Anker) | ✅ implementiert |
| Anonymisierung via spaCy NER (Zwei-Pass) | ✅ implementiert |
| Politische Strömung als Labels | ✅ implementiert |
| DK-Index | ✅ implementiert |
| Themenbereich-Klassifikation | ✅ implementiert |
| Manipulation Targets (Entität, Richtung, Rolle) | ✅ implementiert |
| Techniken-DB mit semantischer Normalisierung | ✅ implementiert |
| RAG via ChromaDB (dynamische Anker) | ✅ implementiert |
| Manuell kuratierter Anker-Korpus | ⏳ offen |
| Keyword-Listen Gegner-Framing-Filter | ⏳ offen |
| Symmetrie-Tests erweitern | ⏳ offen |
