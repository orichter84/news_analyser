# Analyse: Pipeline-Bestimmung der Politischen Strömung

**Datum:** 2026-09-15  
**Thema:** Stufenweise Untersuchung der Klassifikation der Politischen Strömung (`politische_stroemung`), Analyse der Zitatpflicht (*Quote Grounding*) und Identifikation von Fehlerquellen und Inkonsistenzen.

---

## 1. Definition und konzeptionelle Grundlage

Die **Politische Strömung** ordnet einen Artikel einer oder mehreren ideologischen Traditionen zu (z. B. `konservativ`, `liberal`, `sozialdemokratisch`, `grün`, `nationalpopulistisch`, `neutral`).

Im Unterschied zu klassischen 1D-Links/Rechts-Skalen verwendet das System ein **multi-label taxonomisches Modell** (vgl. Architektur-Dokumentation [docs/reference/analyse_architektur.md](../../reference/analyse_architektur.md)):
* Reale politische Phänomene sind oft hybrid (z. B. BSW = `["sozialistisch", "nationalpopulistisch"]`, CSU = `["konservativ", "christdemokratisch"]`).
* Die Labels werden in **Pass 2 auf dem Originaltext** bestimmt.
* Laut Systemprompt gilt eine **strikte Zitatpflicht**: Zu jedem Label muss das charakteristischste Wortsatz-Zitat angegeben werden:
  ```json
  "politische_stroemung": [
    {"label": "konservativ", "quote": "<verbatim sentence from the article...>"}
  ]
  ```

---

## 2. Stufenweise Analyse der Berechnungs-Pipeline

```
Originaltext
   │
   ▼
[Stufe 1: Pass-2-Input] (Volltext unanonymisiert, inklusive Zitate)
   │
   ▼
[Stufe 2: LLM-Extraktion in Pass 2] (Label-Vergabe + supporting quote)
   │
   ▼
[Stufe 3: Nachbearbeitung & Validierung] (Gezielte Validierungs-Lücke im Code)
   │
   ▼
[Stufe 4: Speicherung & Datenabflachung] (ChromaDB JSON-Flattening)
   │
   ▼
[Stufe 5: API-Auslieferung & Frontend] (Quote-Verlust & Visualisierung)
```

---

### Stufe 1: Textbasis und Input-Formung
* **Ort im Code:** [src/news_analyser/agents/analyzer.py:248-251](src/news_analyser/agents/analyzer.py#L248-L251)
* **Mechanismus:**  
  Pass 2 erhält den vollständigen, unbereinigten und unanonymisierten Originaltext.
* **Schwachstellen & Inkonsistenzen:**
  1. **Klarnamen-Bias des Modells:**  
     Pass 2 sieht die Klarnamen (z. B. Parteien, Medienmarken wie *Spiegel*, *FAZ*, *taz* oder Namen prominenter Politiker). LLMs bringen starkes Weltwissen mit. Dies führt dazu, dass das Modell dazu neigt, eine `politische_stroemung` primär anhand der Quelle (*„taz ist grün/links“*, *„FAZ ist konservativ“*) oder der genannten Politiker vorherzusagen, statt die konkrete Argumentation des spezifischen Textes zu prüfen.
  2. **Einstrahlung von Fremd-Zitaten:**  
     Wird ein extrem positionierter Politiker ausführlich zitiert (z. B. Redeauszug von AfD oder Linke), greift das Modell häufig fälschlicherweise diesen Inhalt auf und weist dem *Artikel* die Strömung des *Zitierten* zu, obwohl die Prompt-Regel (`Quoted material rule`) dies explizit untersagt.

---

### Stufe 2: LLM-Klassifikation und Zuweisungslogik
* **Ort im Code:** [src/news_analyser/prompts/system/pass2.md:50-74](src/news_analyser/prompts/system/pass2.md#L50-L74)
* **Mechanismus:**  
  Das Modell wählt aus einer offenen Liste von Labels:
  ```
  liberal | konservativ | christdemokratisch | sozialdemokratisch | grün |
  sozialistisch | kommunistisch | nationalistisch | nationalpopulistisch |
  libertär | faschistisch | anarchistisch | islamistisch | zionistisch |
  ökologisch | feministisch | technokratisch | neutral
  ```
  Zusätzlich darf das Modell freie Labels erfinden (*„not exhaustive — coin new ones if needed“*).
* **Schwachstellen & Inkonsistenzen:**
  1. **Fehlende Normalisierung freier Labels:**  
     Während `detected_techniques` und `manipulation_targets.rolle` per Vektorähnlichkeit auf kanonische Listen normalisiert werden (`normalize_technique`, `normalize_role`), existiert für `politische_stroemung` **keine Normalisierungsfunktion**. Wenn das Modell `neoliberal`, `wirtschaftsliberal`, `marktwirtschaftlich` oder `klassisch-liberal` zurückgibt, bleiben all diese Begriffe unvereinheitlicht nebeneinander bestehen. Dies zersplittert statistische Aggregationen und Publisher-Profile.
  2. **Ambiguität von „Neutral“ vs. „Sachlich berichtend“:**  
     Der Prompt besagt: *„If the article is factual reporting without ideological promotion: [{"label": "neutral", "quote": null}]“*.  
     Oft mischt das Modell jedoch `neutral` mit politischen Labels (z. B. `["neutral", "konservativ"]`), was einen semantischen Widerspruch darstellt.
  3. **Mehrdeutigkeit beim Zitatnachweis:**  
     Der Prompt fordert: *„provide the most characteristic verbatim sentence (1–2 sentences max) that best supports the classification.“*  
     Bei komplexen, subtilen Framings lässt sich eine ideologische Haltung jedoch oft nicht an einem isolierten Satz festmachen, sondern ergibt sich aus der Gesamtauswahl der Themen. Das Modell neigt dann dazu, irgendeinen peripheren Satz als Alibi-Zitat auszuwählen.

---

### Stufe 3: Zitatvalidierung & Code-Prüfung (Kritische Lücke)
* **Ort im Code:** [src/news_analyser/agents/analyzer.py:270-275](src/news_analyser/agents/analyzer.py#L270-L275)
* **Schwachstellen & Zitatvalidierungs-Lücke:**
  1. **Vollständiges Fehlen eines `_validate_quote_grounding` für Strömungs-Zitate:**  
     In `analyzer.py` werden die Zitate der Techniken (`_validate_quote_grounding`) und der Manipulation Targets (`_validate_manipulation_target_grounding`) strikt gegen den Text geprüft.  
     **Für `politische_stroemung` existiert keinerlei programmatische Zitatprüfung!**  
     Wenn das Modell ein frei erfundenes oder paraphrasiertes Zitat liefert, wird dies ungeprüft akzeptiert und gespeichert.
  2. **Keine Prüfung auf Widerspruch zwischen Label und Text:**  
     Es wird im Code nicht kontrolliert, ob das Zitat überhaupt im Quelltext vorkommt (`quote in article.text`).

---

### Stufe 4: Persistierung und Flachklopfen in ChromaDB
* **Ort im Code:** [src/news_analyser/repositories/db_storage.py:30-41, 73-76](src/news_analyser/repositories/db_storage.py#L30-L41)
* **Mechanismus:**  
  Vor dem Schreiben in ChromaDB werden die Metadaten aufbereitet:
  ```python
  def _extract_stroemung_labels(stroemung: list) -> list[str]:
      labels = []
      for item in stroemung:
          if isinstance(item, dict):
              labels.append(item.get("label", ""))
          elif isinstance(item, str):
              labels.append(item)
      return [l for l in labels if l]
  ```
  In den ChromaDB-Metadaten wird das Feld `politische_stroemung` als serialisiertes JSON-Array von reinen Strings gespeichert: `["konservativ", "liberal"]`.
* **Schwachstellen & Datenverlust:**
  1. **Vernichtung des Zitatbelegs in den Top-Level-Metadaten:**  
     Das im Prompt mühsam generierte `quote` wird aus dem Metadaten-Feld herausgefiltert und verworfen! Es überlebt ausschließlich tief im serialisierten Roh-Blob `analysis_json`.
  2. **Keine Filterung ungültiger / leerer Labels:**  
     Gibt das Modell fehlerhafte Strukturen zurück, kann ein leerer String oder Müllwert im Array landen.

---

### Stufe 5: API-Bereitstellung und Frontend-Darstellung
* **Ort im Code:** 
  * [backend/routers/articles.py:23-28](backend/routers/articles.py#L23-L28)
  * [frontend/src/app/features/articles/article-detail.component.html:49-54](frontend/src/app/features/articles/article-detail.component.html#L49-L54)
* **Schwachstellen:**
  1. **Fehlende Zitat-Darstellung im Frontend:**  
     Weder in der Artikelliste noch im Detail-View des Frontends wird das Belegzitat für die politische Strömung angezeigt. Es werden lediglich farbige Badges gerendert:
     ```html
     @for (s of a.politische_stroemung; track s) {
       <span class="badge">{{ s }}</span>
     }
     ```
     Damit ist die im Prompt geforderte Zitatpflicht für den Endanwender komplett wirkungslos: Der Nutzer sieht ein Label, erfährt aber nicht, woran das System diese Einordnung festmacht.
  2. **List-View vs. Detail-View Diskrepanz:**  
     In `backend/routers/articles.py:23-28` wird das Feld `politische_stroemung` bei Dictionaries rigoros auf Strings flachgeklopft. Selbst wenn das Frontend Zitate unterstützen wollte, erhielte es über die Standard-Route `/articles` nur String-Arrays.

---

## 3. Übersicht der Problemfelder

| Stufe | Problem | Ursache | Auswirkung auf Politische Strömung |
|---|---|---|---|
| **Stufe 1** | Quellen-/Autoren-Bias | Unanonymisierter Text in Pass 2 | Einstufung erfolgt nach Publikationsmedium statt nach Textargumentation |
| **Stufe 1** | Zitat-Reflexion | Ungestrippte Politikerzitate | Gesinnung des Interviewten wird fälschlich dem Artikel zugeschrieben |
| **Stufe 2** | Label-Zersplitterung | Keine Normalisierung freier Labels | Synonyme (z. B. marktliberal vs. wirtschaftsliberal) werden nicht aggregiert |
| **Stufe 3** | **Keine Code-Validierung** | **Fehlendes `_validate_quote_grounding` für Strömung** | **Halluzinierte oder ungenaue Zitate werden ungeprüft übernommen** |
| **Stufe 4** | **Metadaten-Verlust** | **`_extract_stroemung_labels` verwirft `quote`** | **Der Beleg geht für Standard-DB-Abfragen verloren** |
| **Stufe 5** | Frontend-Intransparenz | Nur Badge-Anzeige ohne Tooltip/Quote | Mangelnde Nachvollziehbarkeit für den Nutzer |

---

## 4. Handlungsempfehlungen

1. **Programmatische Zitatvalidierung analog zu `detected_techniques`:**  
   Implementierung einer Funktion `_validate_stroemung_grounding(stroemung, source_text)` in `analyzer.py`. Labels, deren `quote` nicht im Quelltext nachweisbar ist (ausgenommen `label: "neutral"` mit `quote: null`), werden entweder verworfen oder auf `quote: null` gesetzt.
2. **Kanonische Normalisierung der Labels:**  
   Einführung eines `normalize_stroemung(label)`-Moduls (analog zu `technique_store`), das Synonyme und freie Modellschöpfungen auf eine kontrollierte Kern-Taxonomie mappt.
3. **Beleg-Erhalt in DB und API:**  
   Speicherung des vollen Objekts `[{"label": "...", "quote": "..."}]` in den Metadaten bzw. strukturierte Rückgabe im Detail-Endpunkt `/articles/{id}`.
4. **Visualisierung im Frontend:**  
   Im UI die Badges mit Tooltips oder Accordions ausstatten, die beim Hovern/Klicken das zugrundeliegende Originalzitat aus dem Artikel hervorheben.

---

## 5. Nachtrag (2026-09-16): Umgesetzt, aber Zitatpflicht weiterhin nur weich

Empfehlungen 1–4 wurden umgesetzt — `_validate_stroemung_grounding`, `normalize_stroemung`
(`stroemung_store.py`), Beleg-Erhalt im Detail-Endpunkt und die Frontend-Anzeige (siehe
[ADR 0009](../concepts/decisions/0009-pipeline-hardening-after-gemini-meta-review.md),
[Meta-Validierung §8](meta_validierung_gemini_analysen.md)). Beim direkten Vergleich
von vier Qwen3-14B-Läufen desselben Artikels (siehe
[`prompting_patterns.md`](../reference/prompting_patterns.md)-Diskussion vom selben Tag)
zeigte sich aber eine Lücke, die über die ursprüngliche Empfehlung hinausgeht:

**Es gibt weiterhin keine Pflicht, ein Label überhaupt mit einem Zitat zu belegen** —
weder im Prompt noch im Code:

- **Prompt (`pass2.md`):** *"For each label, provide the most characteristic verbatim
  sentence... If no single sentence supports it, use the most representative
  passage."* — eine Bitte, kein *"strictly enforced"* wie bei `detected_techniques`
  (Grounding rule) oder `manipulation_targets` (General grounding requirement). Nur
  für `neutral` ist `quote: null` explizit vorgesehen; für alle anderen Labels bleibt
  offen, was passiert, wenn das Modell trotzdem `quote: null` liefert.
- **Code (`_validate_stroemung_grounding`):** prüft ein Zitat nur, *wenn* eines
  mitgeliefert wurde (`if quote and quote not in source_text`). Ist `quote` von
  vornherein `null` oder leer, greift die Funktion gar nicht — das Label bleibt
  unverändert stehen, unabhängig davon, wie stark es die Einordnung des Artikels
  prägt (`sozialdemokratisch`, `faschistisch`, etc.).

**Empirischer Beleg:** vier Qwen3-14B-Läufe desselben Artikels ergaben `["neutral"]`,
`["konservativ", "sozialdemokratisch"]`, `["neutral"]`, `["sozialdemokratisch",
"neutral"]` — eine über die Läufe hinweg instabile inhaltliche Einordnung, die von
keinem der beiden Mechanismen (Prompt-Bitte, Code-Validierung) aufgefangen wird, weil
beide nur bei *vorhandenem* Zitat greifen.

**Ergänzende Empfehlung:** `pass2.md` auf dieselbe *"strictly enforced"*-Sprache wie
bei den anderen Feldern umstellen (Zitat verpflichtend für jedes Label außer
`neutral`), und `_validate_stroemung_grounding` um eine Prüfung erweitern, die ein
fehlendes Zitat bei einem Nicht-neutral-Label als Grounding-Verstoß behandelt —
analog zu `_validate_manipulation_target_grounding`, die ein Feld ohne belegtes
Zitat aktiv auf `None` setzt, statt es unangetastet durchzureichen.
