# Analyse: Pipeline-Bestimmung des Dunning-Kruger Index

**Datum:** 2026-09-15  
**Thema:** Stufenweise Untersuchung der Ermittlung des Dunning-Kruger Index (`dunning_kruger_index`), Analyse der epistemischen Bewertungslogik und Identifikation von Fehlerquellen und Inkonsistenzen.

---

## 1. Definition und mathematische Grundlage

Der **Dunning-Kruger Index** misst die **epistemische Selbstüberhebung** (*epistemic overconfidence*) eines Autors auf einer Skala von $0.0$ bis $1.0$:

* **Niedrig ($0.0 \dots 0.2$):** Hohe epistemische Demut, fundierte Einbettung, Quellenangaben, Konjunktiv, explizite Unsicherheitsmarker (*„laut Experten“*, *„möglicherweise“*, *„Studien legen nahe“*).
* **Mittel ($0.3 \dots 0.6$):** Mischform aus belegten Fakten und unbelegten Werturteilen oder Kausalbehauptungen.
* **Hoch ($0.7 \dots 1.0$):** Absolute Gewissheit, apodiktische Behauptungen ohne Nachweise, Leugnung von Komplexität oder alternativen Erklärungen.

Konzeptionell ist der Index orthogonal zu politischer Richtung und rhetorischem Extremismus (ADR [0004](../../concepts/decisions/0004-add-dunning-kruger-index.md)): Ein Text kann ideologisch neutral sein und dennoch epistemisch anmaßend auftreten (oder umgekehrt).

---

## 2. Stufenweise Analyse der Berechnungs-Pipeline

```
Originaltext
   │
   ▼
[Stufe 1: Scraper & Textbasis] (Unveränderter Volltext inkl. Zitate)
   │
   ▼
[Stufe 2: Pass 2 LLM-Generierung] (Epistemische Bewertung im Prompt)
   │
   ▼
[Stufe 3: Extraktion & Validierung] (JSON-Parsing, None-Fallback, KEINE Belegprüfung)
   │
   ▼
[Stufe 4: Speicherung & Aggregation] (ChromaDB Metadata & Pandas Stats)
```

---

### Stufe 1: Textbasis und Input-Formung
* **Ort im Code:** [src/news_analyser/agents/analyzer.py:248-251](src/news_analyser/agents/analyzer.py#L248-L251)
* **Mechanismus:**  
  Im Gegensatz zu Pass 1 (anonymisiert und zitatbereinigt) wird Pass 2 auf dem **vollen, unbereinigten Originaltext** ausgeführt:
  ```python
  pass2_input = {
      **base_meta,
      "text": article.text,
  }
  ```
* **Schwachstellen & Inkonsistenzen:**
  1. **Kein mechanisches Zitat-Stripping:**  
     Pass 2 sieht direkte Zitate in voller Länge. Der Prompt instruiert das Modell zwar, die Bewertung ausschließlich auf die Autorenstimme zu stützen, aber Zitate von z. B. selbstsicheren Politikern oder Aktivisten (*„Das wird zu 100 % scheitern!“*) strahlen unweigerlich auf die epistemische Wahrnehmung des gesamten Textes ab (*Halo-Effekt*).
  2. **Genre-Verzerrung bei Interview-Texten:**  
     In Interviews besteht der Text zu 80–90 % aus den Antworten des Interviewten. Wenn der Experte stark pointiert und thesenhaft formuliert, das Modell aber die Trennung zwischen Interviewer und Gast kognitiv nicht strikt durchhält, wird der DK-Index des Autors durch den Interviewgast verfälscht.

---

### Stufe 2: LLM-Generierung in Pass 2 (Prompt-Instruktion)
* **Ort im Code:** [src/news_analyser/prompts/system/pass2.md:76-88](src/news_analyser/prompts/system/pass2.md#L76-L88)
* **Mechanismus:**  
  Das Modell schätzt auf Basis qualitativer Kriterien einen Float-Wert:
  ```
  Score HIGH (→1.0) when the article makes bold, certain assertions without sources, hedges, or acknowledgement of complexity.
  Score LOW (→0.0) when claims are properly qualified ("laut Experten", "möglicherweise", "Studien zeigen"), sources are cited, and uncertainty is acknowledged.
  Do not score high merely because settled facts are stated tersely and directly...
  ```
* **Schwachstellen & Inkonsistenzen:**
  1. **Konflikt zwischen journalistischer Verknappung (News Wire Style) und Anmaßung:**  
     Nachrichtenagenturen (dpa, Reuters) formulieren extrem faktenorientiert und knapp (*„Der Bundestag beschloss am Freitag das Gesetz“*). Unerfahrene Modelle werten die Abwesenheit von Konjunktiven oder Quellenverweisen in jedem Satz oft fälschlich als *epistemic overconfidence* ab (im ADR 0008 partiell adressiert, bleibt aber für das Modell interpretativ).
  2. **Fließender Übergang zwischen Fachautorität und Dunning-Kruger:**  
     Schreibt ein renommierter Wissenschaftler oder Fachjournalist über etabliertes Grundwissen seines Fachgebiets, zitiert er nicht zwingend für jede Feststellung eine Fußnote. Das Modell kann oft nicht unterscheiden, ob ein Autor Sachverstand voraussetzt oder ob er anmaßend spekuliert.
  3. **Keine Verankerung (Anchoring) im Prompt:**  
     Während Pass 1 dynamische Anker (`anchor_store`) und ein Keyword-Signal erhält, wird der Dunning-Kruger Index in Pass 2 **völlig frei ohne quantitative Eichmarken** geschätzt. Das Modell hat keinerlei Few-Shot-Referenzen für typische 0.2-, 0.5- oder 0.8-Texte.

---

### Stufe 3: Nachbearbeitung, Extraktion und fehlendes Grounding
* **Ort im Code:** [src/news_analyser/agents/analyzer.py:265-275, 303](src/news_analyser/agents/analyzer.py#L265-L275)
* **Mechanismus:**  
  ```python
  "dunning_kruger_index": result2.get("dunning_kruger_index", 0.0)
  ```
* **Kritische Analyse der Zitatpflicht (Quote Grounding):**
  1. **Vollständiges Fehlen einer Belegpflicht:**  
     * Für `detected_techniques` gibt es ein striktes `_validate_quote_grounding`.
     * Für `manipulation_targets` gibt es `_validate_manipulation_target_grounding` (mit `rolle_quote` und `direction_quote`).
     * Für `politische_stroemung` verlangt der Prompt ein Belegzitat.
     * **Für den Dunning-Kruger Index gibt es weder im Prompt noch im Code eine Zitat- oder Belegpflicht!**  
     Das Modell gibt einfach eine Zahl `0.35` oder `0.80` aus, ohne auch nur einen einzigen Satz zitieren zu müssen, an dem die vermeintliche epistemische Selbstüberhebung festgemacht wird.
  2. **Nicht überprüfbar und nicht auditierbar:**  
     Wird ein Artikel mit einem DK-Index von `0.75` bewertet, kann der Nutzer im Frontend ([frontend/src/app/features/articles/article-detail.component.html](frontend/src/app/features/articles/article-detail.component.html#L35-L39)) lediglich die Zahl sehen. Es gibt keine Textstellen-Hervorhebung, keine Erklärung und keine Möglichkeit zu verifizieren, ob der Score gerechtfertigt ist oder auf einer Modell-Halluzination beruht.

---

### Stufe 4: Speicherung, API und statistische Aggregation
* **Ort im Code:** 
  * [src/news_analyser/repositories/db_storage.py:65](src/news_analyser/repositories/db_storage.py#L65)
  * [backend/routers/articles.py:56](backend/routers/articles.py#L56)
  * [src/news_analyser/stats.py:107-111, 462](src/news_analyser/stats.py#L107-L111)
* **Schwachstellen & Inkonsistenzen:**
  1. **Typ-Inkonsistenz (Float vs. Null):**  
     In `db_storage.py` wird `float(ft.get("dunning_kruger_index", 0.0))` gespeichert. Wenn der Wert `0.0` ist (maximale epistemische Bescheidenheit), wandelt `backend/routers/articles.py`:
     ```python
     "dunning_kruger_index": float(m.get("dunning_kruger_index", 0.0)) or None
     ```
     den Score `0.0` fälschlicherweise in `None` um! Ein perfekter Score von `0.0` wird dadurch im Frontend als „nicht vorhanden / nicht berechnet“ dargestellt, anstatt als minimaler Wert.
  2. **Historische Altdaten:**  
     Artikel, die vor Einführung des DK-Index (ADR 0004) analysiert wurden, besitzen kein `dunning_kruger_index`-Feld. Aggregationen müssen diesen Fall über Auslassung (`dropna`) abfangen.

---

## 3. Übersicht der Problemfelder

| Stufe | Problem | Ursache | Effekt auf den Dunning-Kruger Index |
|---|---|---|---|
| **Stufe 1** | Zitat-Einstrahlung | Pass 2 liest den ungestrippten Volltext | Selbstsichere Zitate Dritter färben auf den Autoren-Score ab |
| **Stufe 2** | Fehlen von Ankern / Eichung | Keine Few-Shot-Beispiele oder RAG-Anker in Pass 2 | Subjektive, von Run zu Run schwankende Schwellenwerte |
| **Stufe 2** | Agentur-Missverständnis | Kurzer Nachrichtenstil ohne Konjunktive | Sachliche Kurzmeldungen werden als überheblich eingestuft |
| **Stufe 3** | **Fehlende Zitatpflicht** | **Weder Zitat noch Erklärung im JSON-Schema gefordert** | **Ergebnis ist eine unbegründete Blackbox-Zahl** |
| **Stufe 4** | Null-Konvertierungs-Bug | Python `or None` wandelt echten Float `0.0` in `None` | Perfekt fundierte Texte verlieren ihren Score in der API |

---

## 4. Handlungsempfehlungen

1. **Einführung einer Zitat- und Begründungspflicht (Quote Grounding):**  
   Das Schema in `pass2.md` sollte um Belegzitate und eine kurze Begründung erweitert werden:
   ```json
   "dunning_kruger": {
     "score": <float 0.0 to 1.0>,
     "evidence_quote": "<verbatim sentence exhibiting overconfidence, or null>",
     "explanation": "<short justification>"
   }
   ```
   Bei Scores $> 0.3$ muss ein Textzitat vorliegen, das über `source_text.count(quote)` verifiziert werden kann. Fehlt der Beleg, wird der Score automatisch nach unten korrigiert.
2. **Behebung des Null-Werte-Bugs im API-Router:**  
   In [backend/routers/articles.py](backend/routers/articles.py#L56) und Zeile 84 die fehlerhafte `or None`-Logik ersetzen:
   ```python
   # Falsch:
   "dunning_kruger_index": float(m.get("dunning_kruger_index", 0.0)) or None
   # Richtig:
   "dunning_kruger_index": float(m["dunning_kruger_index"]) if "dunning_kruger_index" in m and m["dunning_kruger_index"] is not None else None
   ```
3. **Explizite Kalibrierungsbeispiele im Pass-2-Prompt:**  
   Analoge Bänder-Definitionen und 2–3 prägnante Mini-Beispiele für 0.1 (vorsichtig abwägend), 0.5 (teils thesenhaft) und 0.9 (unbelegte Gewissheit) direkt in [src/news_analyser/prompts/system/pass2.md](src/news_analyser/prompts/system/pass2.md) hinterlegen.
