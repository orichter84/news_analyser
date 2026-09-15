# Vorschlag & Maßnahmenplan: Pipeline-Härtung und Bugfixes

**Datum:** 2026-09-15  
**Status:** Vorschlag / In Abstimmung  
**Kontext:** Synthese aus den vier Indikator-Analysen und der [Meta-Validierung von Claude](meta_validierung_gemini_analysen.md).

---

## Übersicht & Priorisierung

Die Maßnahmen sind nach Aufwand, Risiko und direktem Nutzen in drei Phasen gegliedert:

1. **Phase 1: Quick-Wins & Backend-Bugs** (Minimaler Aufwand, sofortige Fehlerbehebung im API- und UI-Layer)
2. **Phase 2: Code-Validierung & Datenintegrität** (Deterministische Prüfungen im Analyzer, Verhinderung von Halluzinationen und Dubletten)
3. **Phase 3: Metrik- & Vorverarbeitungs-Härtung** (Strukturelle Bereinigung von Mismatches und Vorverarbeitungslogik)

---

## Phase 1: Sofortmaßnahmen / Quick-Wins

### 1.1 Fix des Dunning-Kruger Null-Bugs (API-Router)
* **Dateien:** `backend/routers/articles.py` (Zeilen 56 und 84)
* **Problem:**  
  Der Ausdruck `float(m.get("dunning_kruger_index", 0.0)) or None` wandelt den gültigen Bestwert `0.0` (maximale epistemische Bescheidenheit) in Python `None` um. Der Score verschwindet im Frontend und wird als „nicht vorhanden“ angezeigt.
* **Maßnahme:**  
  Explizite Prüfung auf `None`:
  ```python
  # Listen- und Detail-Endpunkt:
  val = m.get("dunning_kruger_index")
  full.setdefault("dunning_kruger_index", float(val) if val is not None else None)
  ```
* **Akzeptanzkriterium:** Ein Artikel mit DK-Index `0.0` liefert in `GET /articles` und `GET /articles/{id}` den Wert `0.0` und nicht `null`.

---

### 1.2 Fix des Doppel-Flattening bei `politische_stroemung` (Detail-Endpunkt)
* **Datei:** `backend/routers/articles.py` (Zeilen 76–80)
* **Problem:**  
  `get_article()` deserialisiert `analysis_json` (welches Zitate enthält: `[{"label": "...", "quote": "..."}]`) in `full`. Unmittelbar danach wird `full = _parse_meta(full)` aufgerufen. Diese Funktion wandelt die Dicts fälschlich wieder in reine Label-Strings um. Das Frontend (`article-detail.component.html:49-58`) kann die vorhandenen Zitate daher niemals anzeigen.
* **Maßnahme:**  
  `_parse_meta` so anpassen oder im Detail-Endpunkt umgehen, dass die Objektstruktur für `politische_stroemung` im Detail-View erhalten bleibt:
  ```python
  def _parse_meta(meta: dict[str, Any], flatten_stroemung: bool = True) -> dict[str, Any]:
      ...
      if flatten_stroemung:
          ps = meta.get("politische_stroemung", [])
          if ps and isinstance(ps[0], dict):
              meta["politische_stroemung"] = [item.get("label", "") for item in ps if isinstance(item, dict)]
      return meta
  ```
* **Akzeptanzkriterium:** `GET /articles/{id}` liefert Objekte mit `label` und `quote`, sofern Zitate existieren; das Frontend rendert das Zitat im Blockquote.

---

## Phase 2: Code-Validierung & Datenintegrität

### 2.1 Grounding-Validierung für `politische_stroemung`-Zitate
* **Datei:** `src/news_analyser/agents/analyzer.py`
* **Problem:**  
  Techniken und Targets werden per Code gegen den Quelltext validiert (`_validate_quote_grounding`). Für `politische_stroemung` fehlt diese Prüfung vollständig; halluzinierte oder ungenaue Zitate werden ungeprüft übernommen.
* **Maßnahme:**  
  Implementierung einer Funktion `_validate_stroemung_grounding(stroemung, source_text)`:
  * Prüft für jedes Label-Objekt mit Quote, ob `quote.strip()` im Originaltext vorhanden ist.
  * Wenn nicht auffindbar: `quote = None` setzen (oder Label verwerfen, falls nicht `neutral`).
* **Akzeptanzkriterium:** Nicht im Text nachweisbare Zitate werden bereinigt und nicht gespeichert.

---

### 2.2 Deduplizierung nach `normalize_technique` in Pass 1
* **Datei:** `src/news_analyser/agents/analyzer.py` (nach Zeile 236)
* **Problem:**  
  Verschiedene Freitext-Begriffe, die semantisch auf dieselbe kanonische Technik gemappt werden, werden in `detected_techniques` nicht zusammengeführt. Sie zählen im Bernays Score doppelt.
* **Maßnahme:**  
  Nach der Normalisierung prüfen, ob dieselbe Technik mehrfach auf demselben oder überlappenden Textabschnitt liegt, und Dubletten entfernen:
  ```python
  seen = set()
  deduped = []
  for t in techniques:
      key = (t["technique"], t.get("quote", "").strip())
      if key not in seen:
          seen.add(key)
          deduped.append(t)
  result1["detected_techniques"] = deduped
  ```
* **Akzeptanzkriterium:** Keine identischen (Technik, Zitat)-Paare in `detected_techniques`.

---

### 2.3 Begründungspflicht für Dunning-Kruger Index
* **Dateien:** `src/news_analyser/prompts/system/pass2.md`, `src/news_analyser/agents/analyzer.py`
* **Problem:**  
  Der DK-Index ist ein unbegründeter Float-Wert ohne Nachvollziehbarkeit.
* **Maßnahme (abgestimmt nach Claude-Feedback, abwärtskompatibel):**  
  Um ein Breaking Change im Schema (Verschachtelung) zu vermeiden, bleibt `dunning_kruger_index` als flacher Float bestehen und wird lediglich um das Geschwisterfeld `dunning_kruger_explanation` ergänzt:
  ```json
  "dunning_kruger_index": <float 0.0 to 1.0>,
  "dunning_kruger_explanation": "<1-2 Sätze Begründung der epistemischen Einstufung>"
  ```
  *(Hinweis aus Meta-Validierung: Kein starres Substring-Hard-Dropping, da DK eine Gesamteigenschaft des Duktus ist, aber Verpflichtung zur qualitativen Rechtfertigung ohne Schema-Bruch).*
* **Akzeptanzkriterium:** Die Erklärung wird in `analysis_json` persistiert und ist im UI einsehbar, während bestehende Leser von `dunning_kruger_index` (Analyzer, DB-Storage, API) voll kompatibel bleiben.

---

## Phase 3: Metrik- & Vorverarbeitungs-Härtung

### 3.1 Konsistenz des Bernays-Score-Nenners
* **Dateien:** `src/news_analyser/scraper.py`, `src/news_analyser/repositories/db_storage.py`, `src/news_analyser/agents/analyzer.py`
* **Problem:**  
  `bernays_score = len(techniques) / word_count * 1000`. `word_count` ist der Gesamttext, während `techniques` aus dem um Zitate bereinigten Pass-1-Text stammt. Bei zitatreichen Artikeln (z. B. Interviews) verzerrt dies den Score nach unten.
* **Maßnahme:**  
  In Pass 1 die Wortanzahl des tatsächlich analysierten Textes (`pass1_word_count`) ermitteln und entweder als Nenner verwenden oder im Metadata-Record transparent ausweisen.

---

### 3.2 Mechanische Erkennung von Interview-Turns (Pass 0)
* **Dateien:** `src/news_analyser/agents/analyzer.py`, `src/news_analyser/anonymizer/`
* **Problem:**  
  Dialogformate ohne typografische Anführungszeichen (`Name: Antwort...`) entgehen `_strip_quoted_material`. Die Filterung beruht rein auf Prompt-Compliance, was zu Schwankungen führt (ADR 0008: „known limitation").
* **Maßnahme:**  
  Heuristische Erkennung von Interview-Mustern vor Pass 1 (z. B. Regex auf Sprecherpräfixe am Zeilenanfang) und gezieltes Ausblenden der Expertenantworten vor der Pass-1-Übergabe.

---

### 3.3 Normalisierung freier Strömungs-Labels
* **Dateien:** `src/news_analyser/repositories/stroemung_store.py` (neu) oder Regelwerk
* **Problem:**  
  Freie Wortschöpfungen des LLMs (`wirtschaftsliberal`, `neoliberal`, `marktwirtschaftlich`) zersplittern Publisher-Profile und statistische Aggregationen.
* **Maßnahme:**  
  Einführung einer Mapping-Tabelle oder Vektornormalisierung für Strömungen analog zu `normalize_technique`.
