# Analyse: Pipeline-Bestimmung des Orwell Index

**Datum:** 2026-09-15  
**Thema:** Stufenweise Untersuchung der Ermittlung des Orwell Index (`orwell_index`), Analyse der Signalfusion und Identifikation von Fehlerquellen und Inkonsistenzen.

---

## 1. Definition und mathematische Grundlage

Der **Orwell Index** misst den Grad an **rhetorischem Extremismus, Feindbildkonstruktion und dystopischer Zuspitzung** in einem Artikel auf einer Skala von $0.0$ (rein sachlich) bis $1.0$ (existenzielle Bedrohung / Mobilisierung).

Im aktuellen Systemdesign ist der finale Index das **Maximum aus zwei unabhängigen Teilkanälen**:

$$\text{orwell\_index} = \max(\text{orwell\_index\_structural}, \text{quote\_amplification\_index})$$

* **`orwell_index_structural` (Pass 1):** Bewertet die originäre rhetorische Stimme des Autors auf dem *anonymisierten und mechanisch zitatbereinigten* Text.
* **`quote_amplification_index` (Pass 2):** Bewertet die manipulative *Auswahl und Rahmung von Drittzitaten* auf dem *vollständigen Originaltext*.

Zusätzlich speisen zwei Hilfssignale in Pass 1 ein:
1. Ein regelbasiertes **Keywordsignal** (`extremism_score` $\in [0.0, 1.0)$).
2. Dynamisch via Vektorsuche geladene **Kalibrierungs-Anker** (`anchor_store`).

---

## 2. Stufenweise Analyse der Berechnungs-Pipeline

```
Originaltext
   │
   ├─► [Stufe 1: Keyword-Signal] ───────────────┐
   │                                            ▼
   ├─► [Stufe 2: Pass 0 Anonymisierung] ──► [Stufe 4: Pass 1 LLM]
   │          & Zitat-Stripping                 ▲ (anonymisiert, zitatbereinigt)
   │                                            │
   │   [Stufe 3: Dynamische Anker (RAG)] ───────┘
   │
   ├─► [Stufe 5: Pass 2 LLM] (Originaltext mit Zitaten)
   │
   └─► [Stufe 6: Signalfusion & Speicherung] ──► orwell_index = max(structural, quote_amplification)
```

---

### Stufe 1: Keyword-Signal-Berechnung (Heuristischer Prior)
* **Ort im Code:** [src/news_analyser/keywords.py](src/news_analyser/keywords.py)
* **Mechanismus:**  
  Zählt Substring-Treffer aus drei kuratierten Wortlisten (`keywords_extreme_left.txt`, `keywords_extreme_right.txt`, `keywords_general.txt`) auf dem Kleinbuchstaben-Volltext.
  $$\text{extremism\_score} = \frac{\text{total\_hits}}{\text{total\_hits} + 5}$$
* **Schwachstellen & Inkonsistenzen:**
  1. **Kontextblindheit (Adversarial Framing / Zitierverwendung):**  
     Ein seriöser Qualitätsartikel, der extremistische Parolen analysiert oder zitiert (*„Die AfD fordert Remigration“* oder *„Kritik an Systemüberwindung“*), erhält denselben hohen Score wie ein Propagandatext.
  2. **Substring-Matching-Artefakte:**  
     Einfache Substring-Prüfung (`kw in text_lower`) ohne Wortgrenzen-Regex (`\b`) erzeugt False Positives bei zusammengesetzten Wörtern.
  3. **Verankerungseffekt im LLM:**  
     Das Signal wird Pass 1 im JSON-Input als `extremism_score` übergeben. Auch wenn es als „schwacher Prior (20–30 %)“ deklariert ist, erzeugt eine numerische Vorab-Einschätzung bei LLMs einen starken Verankerungseffekt (*Anchoring Bias*).

---

### Stufe 2: Textvorbereitung für Pass 1 (Anonymisierung & Zitat-Stripping)
* **Ort im Code:** [src/news_analyser/agents/analyzer.py](src/news_analyser/agents/analyzer.py#L130-L192)
* **Mechanismus:**  
  1. Akteure/Gruppen werden durch `Akteur_A`, `Akteur_B`, `[Person]` etc. ersetzt.
  2. Direkte Zitate in Anführungszeichen (`„...“`, `»...«`, `"..."`) werden durch `[…]` ersetzt (`_strip_quoted_material`).
* **Schwachstellen & Inkonsistenzen:**
  1. **Asymmetrisches Stripping bei Interviews:**  
     Dialoge nach dem Muster `Name: Antwort...` ohne typografische Anführungszeichen bleiben im Text stehen. Pass 1 muss dann instruktionsbasiert entscheiden, ob der Text ignoriert wird. Scheitert diese Instruktion, bewertet Pass 1 die Zitate fälschlicherweise als Autorenstimme $\rightarrow$ `orwell_index_structural` schießt hoch.
  2. **Verlust des semantischen Rahmens durch Anonymisierung:**  
     Das Modell sieht `Akteur_A fordert Maßnahme_X gegen Gruppe_B`. Ohne Weltwissen neigen Modelle dazu, abstrakte Konflikte pessimistischer und feindseliger zu interpretieren, da die friedliche Routine realer Institutionen hinter den Platzhaltern unsichtbar wird (im ADR 0008 als *„Anonymisation charity gap“* beschrieben).

---

### Stufe 3: Dynamische Kalibrierungs-Anker (RAG)
* **Ort im Code:** [src/news_analyser/repositories/anchor_store.py](src/news_analyser/repositories/anchor_store.py)
* **Mechanismus:**  
  Sucht per Kosinus-Ähnlichkeit in ChromaDB nach bis zu $k=3$ bereits analysierten Artikeln (`orwell_anchors`), formatiert diese und hängt sie als Kalibrierungsbeispiele an den Pass-1-Systemprompt an.
* **Schwachstellen & Inkonsistenzen:**
  1. **Rückkopplungsschleifen (Feedback-Loop / Error Propagation):**  
     Wird ein Artikel durch einen Fehlgriff des LLMs mit einem viel zu hohen oder zu niedrigen Orwell-Index gespeichert, wird dieser Ausreißer als Referenzanker an nachfolgende ähnliche Artikel übergeben (*„Nutze diese Referenzen zur Kalibrierung...“*). Das System kann sich dadurch selbst destabilisieren.
  2. **Thematische statt rhetorische Ähnlichkeit:**  
     Text-Embeddings clustern nach *Inhalt und Thema* (z. B. Ukraine-Krieg, Asyldebatte), nicht nach *rhetorischem Stil*. Ein sachlicher Bericht über ein extremes Thema matcht semantisch auf einen extremistischen Kommentar zum selben Thema. Die übergebenen Anker-Scores passen dann stilistisch nicht zum Zieltext.
  3. **Kaltstart & Drift:**  
     Solange wenige Anker vorhanden sind (`< MIN_ANCHORS`), fehlen sie ganz; sobald sie aktiv sind, ändert sich die Prompt-Struktur sprunghaft.

---

### Stufe 4: LLM-Extraktion in Pass 1 (`orwell_index_structural`)
* **Ort im Code:** [src/news_analyser/prompts/system/pass1.md](src/news_analyser/prompts/system/pass1.md)
* **Mechanismus:**  
  Das Modell schätzt auf Basis von Text, Keyword-Signal und Ankern einen Float-Wert `orwell_index` $\in [0.0, 1.0]$.
* **Schwachstellen & Inkonsistenzen:**
  1. **Keine Zitatpflicht / Grounding für den Index:**  
     Im Gegensatz zu den `detected_techniques` gibt es für den `orwell_index` **keine Zitatpflicht und keine deterministische Validierung**. Der Wert ist eine rein generative Freitext-Schätzung. Ein Halluzinieren oder systematisches Drift-Verhalten kann nachgelagert nicht durch Code abgefangen werden.
  2. **Ambiguität der Bänder (0.4–0.6 vs. 0.7–0.9):**  
     Der Prompt definiert grobe Bänder:
     * `0.4–0.6`: *Clearly emotional / one-sided*
     * `0.7–0.9`: *Strong enemy images, emotionalisation, black-and-white thinking*  
     Die Grenze zwischen „einseitig/emotional“ und „Feindbild/Schwarz-Weiß“ ist fließend. Wenn ein Modell eine pointierte Glosse analysiert, entscheidet oft ein einzelnes Token darüber, ob der Score bei 0.45 oder 0.75 landet.
  3. **Kumulations-Missverständnis:**  
     Trotz der Regel im Prompt, dass mehrere schwache Instanzen (0.2–0.4) sich nicht zu 0.7+ aufsummieren dürfen, neigen Modelle autoregressiv dazu: Finden sie 5–8 Techniken, setzen sie den Orwell-Index intuitiv parallel nach oben, da sie eine Korrelation zwischen Technikdichte und Extremismus annehmen.

---

### Stufe 5: LLM-Extraktion in Pass 2 (`quote_amplification_index`)
* **Ort im Code:** [src/news_analyser/prompts/system/pass2.md](src/news_analyser/prompts/system/pass2.md)
* **Mechanismus:**  
  Pass 2 analysiert den Originaltext und bewertet, ob durch die *Auswahl* der Zitate extremes Gedankengut unkommentiert verstärkt wird.
* **Schwachstellen & Inkonsistenzen:**
  1. **Struktureller Konflikt bei Einzelquellen / Interviews:**  
     Das Kriterium *„Missing rebuttal / one-sided platforming“* schlägt bei Texten fehl, die definitionsgemäß nur eine Stimme abbilden (z. B. Interview mit einem Experten, Gastkommentar, Nachruf). Das Modell neigt dazu, das Fehlen einer Gegenstimme als manipulative Quote Amplification abzustrafen, selbst wenn das Interview journalistisch transparent geführt wurde.
  2. **Quote-Attribution vs. Amplification:**  
     Der Prompt warnt zwar davor, dass sauber eingeordnete Zitate keine Amplification darstellen, aber Modelle lassen sich durch drastische Formulierungen im Zitat oft verleiten, den Zitat-Inhalt dem Artikel anzulasten.
  3. **Wiederum keine Zitat-Grounding-Pflicht:**  
     Es wird kein konkreter Textnachweis gefordert, aus dem hervorgeht, welches Zitat die Verstärkung ausgelöst hat.

---

### Stufe 6: Signalfusion (`max()`-Operation)
* **Ort im Code:** [src/news_analyser/agents/analyzer.py:291](src/news_analyser/agents/analyzer.py#L291)
* **Mechanismus:**  
  ```python
  orwell = max(orwell_structural, quote_amplification)
  ```
* **Schwachstellen & Inkonsistenzen:**
  1. **Extreme Asymmetrie und Fehler-Verstärkung (Ratchet-Effekt):**  
     Die `max()`-Operation fungiert als Einweg-Gleichrichter. Wenn Pass 1 fehlerfrei einen neutralen Text erkennt (`orwell_structural = 0.15`), Pass 2 aber aufgrund eines einzelnen pointierten Zitats halluziniert oder überreagiert (`quote_amplification = 0.65`), wird der Gesamtwert sofort auf `0.65` hochgerissen. Ein Fehler nach oben setzt sich immer durch; eine konservative, korrekte Schätzung hat gegen eine Überreaktion keine Chance.
  2. **Verlust der Trennschärfe im UI:**  
     Im Dashboard und in Listenansichten wird primär `orwell_index` angezeigt. Dem Nutzer ist nicht sofort ersichtlich, ob der Autor selbst hetzt oder lediglich unglücklich zitiert hat.

---

## 3. Übersicht der Problemfelder

| Stufe | Problem | Ursache | Auswirkung auf Orwell Index |
|---|---|---|---|
| **Stufe 1** | Fehlgeleiteter Prior | Substring-Treffer ohne syntaktischen Kontext | Hoher `extremism_score` bei Artikeln, die Extremismus nur zitieren/kritisieren |
| **Stufe 2** | Anonymisierungs-Bias | Abstrakte Platzhalter (`Akteur_A`) wirken konfrontativer | Modell überschätzt Feindseligkeit routinierter Akteure |
| **Stufe 3** | Anker-Kontamination | Feedback-Schleife bei Speicherung ungenauer Anker | Fehlerhafte Scores pflanzen sich in thematisch ähnliche Artikel fort |
| **Stufe 4** | Fehlende Belegpflicht | Kein Quote-Grounding für `orwell_index_structural` | Ungeprüfte, rein probabilistische Einstufung durch das Modell |
| **Stufe 5** | Genre-Fehlurteil | Fehlende Gegenstimme in Einzelinterviews | Zitat-Verstärkung wird bei regulären Interviews fälschlich positiv gewertet |
| **Stufe 6** | `max()` Ratchet-Effekt | Monoton steigende Fusion zweier fehlerbehafteter Signale | Jede Überreaktion in einem der beiden Pässe dominiert das Endergebnis |

---

## 4. Handlungsempfehlungen

1. **Belegpflicht (Quote Grounding) für Pass 2 Quote-Amplification:**  
   Wenn `quote_amplification_index > 0.3`, muss das Modell das konkrete Zitat benennen, das die Verstärkung trägt, analog zu den `manipulation_targets`. Fehlt der Beleg, wird der Sub-Score auf $\le 0.3$ gedeckelt.
2. **Dämpfung der Signalfusion:**  
   Statt eines harten `max()` sollte eine gewichtete Fusion oder eine konditionale Freigabe geprüft werden (z. B. `max()` nur dann anwenden, wenn `quote_amplification_index` durch belegte Zitate verifiziert ist; andernfalls `orwell_structural` mit moderatem Zuschlag).
3. **Keyword-Signal auf Wortgrenzen umstellen:**  
   In [src/news_analyser/keywords.py](src/news_analyser/keywords.py) reguläre Ausdrücke mit `\b` verwenden und Zitatabschnitte bei der Keywordzählung ausklammern.
4. **Anker-Qualitätsfilter:**  
   Nur Artikel als Referenz-Anker in ChromaDB aufnehmen, deren Analyse manuell verifiziert wurde oder deren Scores eine hohe interne Konsistenz aufweisen (keine extremen Diskrepanzen zwischen Pass 1 und Pass 2).
