# Analyse: Pipeline-Bestimmung des Bernays Scores und Zitatvalidierung

**Datum:** 2026-09-15  
**Thema:** Stufenweise Untersuchung der Bernays-Score-Berechnung, Zitatpflicht (*Quote Grounding*) und Ursachen für Zählinkonsistenzen.

---

## 1. Definition und mathematische Grundlage

Der **Bernays Score** misst die Intensität/Dichte von Manipulationstechniken in einem Artikel:

$$\text{Bernays Score} = \frac{|\text{detected\_techniques}|}{\text{word\_count}} \times 1000$$

Das Ergebnis wird auf zwei Nachkommastellen gerundet in der Datenbank persistiert (`src/news_analyser/repositories/db_storage.py:70-72`).

Jede Ungenauigkeit im Zähler ($|\text{detected\_techniques}|$) oder im Nenner ($\text{word\_count}$) schlägt direkt linear oder reziprok auf den finalen Wert durch.

---

## 2. Stufenweise Analyse der Berechnungs-Pipeline

### Stufe 1: Extraktion & Nenner-Bestimmung (`word_count`)
* **Ort im Code:** `src/news_analyser/scraper.py:151`
* **Mechanismus:**  
  Nach der HTML-Extraktion via `trafilatura` (Fallback: `BeautifulSoup`) wird die Wortanzahl des Roh-Artikels ermittelt:
  ```python
  words = len(text.split())
  ```
* **Schwachstellen & Inkonsistenzen:**
  1. **Diskrepanz zwischen Normierungsbasis und Analysetext:**  
     `word_count` basiert auf dem ungekürzten Gesamtergebnis des Scrapers. Vor Pass 1 (aus dem die Techniken stammen) werden jedoch direkte Zitate durch `[…]` ersetzt (`_strip_quoted_material`). Ein Artikel mit hohem Zitatanteil (z. B. Interviews) besitzt daher in Pass 1 eine drastisch reduzierte effektive Wortanzahl, wird jedoch durch die hohe Gesamtwortzahl geteilt.
  2. **Scraper-Boilerplate:**  
     Nicht vollständig bereinigte Bildunterschriften, Autorenboxen oder Cookie-/Navigationsfragmente blähen `word_count` auf und senken den Bernays Score künstlich ab.

---

### Stufe 2: Textvorbereitung für Pass 1 (Anonymisierung & Zitat-Stripping)
* **Ort im Code:** `src/news_analyser/agents/analyzer.py:130-192`
* **Mechanismus:**  
  1. Gruppen/Akteure werden durch Tokens (`Akteur_A`, `Akteur_B`) ersetzt.
  2. Direkte Zitate in Anführungszeichen (`„...“`, `»...«`, `"..."`) werden per Regex durch `[…]` ersetzt (`_strip_quoted_material`).
* **Schwachstellen bezüglich Zitatpflicht:**
  1. **Interview-Formate ohne Anführungszeichen:**  
     Dialoge nach dem Muster `Name: Antwort...` werden vom Regex nicht erfasst. Das Modell muss im Prompt selbst entscheiden, Expertenantworten zu ignorieren. Schlägt dies fehl, vervielfacht sich das für Techniken verfügbare Textmaterial (z. B. von 150 Wörtern Journalistenfragen auf 1.159 Wörter Gesamttext), was unmittelbar zu massiven Zählsprüngen führt.
  2. **Veränderte Zitatgrundlage:**  
     Das Modell zitiert aus dem anonymisierten Text. Ersetzt das LLM Platzhalter zurück in Klarnamen, schlägt das anschließende exakte Quote Grounding fehl.

---

### Stufe 3: LLM-Extraktion in Pass 1 (Technik-Detektion)
* **Ort im Code:** `src/news_analyser/prompts/system/pass1.md`
* **Mechanismus:**  
  Das Modell liefert ein JSON-Array zurück:
  ```json
  {
    "technique": "<Technique>",
    "quote": "<exact text excerpt>",
    "explanation": "<1-3 Sätze>"
  }
  ```
* **Schwachstellen & Inkonsistenzen:**
  1. **Mehrfach-Etikettierung derselben Textstelle (Overlapping Spans):**  
     Eine Passage wie *„Ich vertraue bei den großen Tech-Konzernen nicht darauf... Sie haben rein wirtschaftliche Interessen.“* kann semantisch sowohl als *Framing* als auch als *Loaded Language* oder *Scapegoating* gelesen werden. Zwar fordert der Prompt *„One technique per passage“*, dies wird jedoch auf Modellebene oft ignoriert, wenn Sub-Sätze separat zitiert werden.
  2. **Keine feste Zitat-Granularität:**  
     Ein Zitat kann ein einzelnes Wort (*„abernten“*), ein Satz oder ein ganzer Absatz sein. Wenn das Modell in einem Durchlauf Absätze als Einheit bewertet und im nächsten Durchlauf einzelne Teilsätze als separate rhetorische Instanzen zählt, schwankt die Listenlänge drastisch.
  3. **Autoregressives Momentum:**  
     Die Generierung ist eine offene Liste. Werden zu Beginn des Textes frühzeitig Techniken generiert, sinkt die Schwelle für weitere Detektionen im weiteren Textverlauf.

---

### Stufe 4: Zitatvalidierung (`_validate_quote_grounding`)
* **Ort im Code:** `src/news_analyser/agents/analyzer.py:61-91`
* **Implementierung:**
  ```python
  def _validate_quote_grounding(
      techniques: list[dict[str, Any]], source_text: str
  ) -> list[dict[str, Any]]:
      quote_counts: dict[str, int] = {}
      validated = []
      dropped = 0
      for t in techniques:
          quote = (t.get("quote") or "").strip()
          if not quote:
              dropped += 1
              continue
          occurrences = source_text.count(quote)
          if occurrences == 0:
              dropped += 1
              continue
          quote_counts[quote] = quote_counts.get(quote, 0) + 1
          if quote_counts[quote] > occurrences:
              dropped += 1
              continue
          validated.append(t)
      return validated
  ```
* **Kritische Analyse der Zitatvalidierung:**
  1. **Typografische Diskrepanzen (Hard Failure bei Bagatellen):**  
     `source_text.count(quote)` verlangt einen exakten Byte-/Zeichen-Match. Wenn das LLM Anführungszeichen normalisiert (`"..."` statt `„...“`), Leerzeichen vereinheitlicht (z. B. geschütztes Leerzeichen `\u00a0` vs. reguläres Leerzeichen) oder Bindestriche variiert (`–` vs. `-`), ist `occurrences == 0`. Das Zitat wird **ersatzlos verworfen**, und der Bernays Score sinkt unberechtigt.
  2. **Ellipsen und Textkürzungen:**  
     Fügt das Modell im Zitat Auslassungen ein (`[…]` oder `...`), schlägt der String-Match fehl, selbst wenn der Inhalt real existiert.
  3. **Keine Erkennung von Zitat-Überlappungen (Substrings):**  
     Die Funktion zählt nur identische Strings.  
     * Beispiel: Zitat 1 = `"Tech-Konzerne haben wirtschaftliche Interessen. Daten sind Geld."` und Zitat 2 = `"Daten sind Geld."`.  
     Beide kommen $\ge 1\times$ vor. Beide werden akzeptiert. Die Code-Validierung verhindert somit nicht die Mehrfachzählung derselben rhetorischen Einheit, wenn das Zitat nur leicht beschnitten wird.

---

### Stufe 5: Nachgelagerte Normalisierung & Speicherung
* **Ort im Code:** `src/news_analyser/agents/analyzer.py:233-236`, `src/news_analyser/repositories/db_storage.py:70-72`
* **Mechanismus:**  
  1. Techniken werden semantisch auf kanonische Namen gemappt (`normalize_technique`).
  2. Berechnung des Bernays Scores anhand `len(techniques)`.
* **Schwachstellen & Inkonsistenzen:**
  1. **Fehlende Deduplizierung nach Normalisierung:**  
     Werden zwei unterschiedliche Freitext-Begriffe auf dieselbe kanonische Technik normalisiert (z. B. `"Emotional Appeal"` und `"Gefühlsbetonte Sprache"` $\rightarrow$ `"Emotional Manipulation"`), findet keine Deduplizierung statt. `len(techniques)` bleibt unverändert hoch.
  2. **Unbegrenzte Skalierung:**  
     Der Bernays Score ist nach oben offen. Bei kurzen Texten mit stark zergliederten Zitaten treten unverhältnismäßig hohe Extremwerte auf.

---

## 3. Übersicht der Problemfelder

| Stufe | Problem | Ursache | Effekt auf den Bernays Score |
|---|---|---|---|
| **Stufe 1** | Basis-Verzerrung | Gesamtwortzahl vs. zitatbereinigter Text | Score bei zitatreichen Texten / Interviews künstlich zu niedrig |
| **Stufe 2** | Interview-Leck | Unmarkierte Dialoge entgehen Regex-Stripping | Modell schwankt zwischen Auslassung (niedrig) und Vollanalyse (hoch) |
| **Stufe 3** | Multi-Labeling | Abstrakte Meta-Technik (*Framing*) vs. Detail-Technik | Künstliche Vervielfachung einzelner Passagen |
| **Stufe 4** | Typografie-Ausfall | Striktes `source_text.count(quote)` | Streichung valider Funde bei geringsten Zeichenunterschieden |
| **Stufe 4** | Substring-Lücke | Keine Überlappungsprüfung im Code | Teilzitate desselben Satzes werden mehrfach gewertet |
| **Stufe 5** | Normalisierungs-Dubletten | Keine Deduplizierung nach kanonischem Mapping | Doppelt gezählte Techniken nach Synonym-Auflösung |

---

## 4. Handlungsempfehlungen

1. **Normalisiertes Quote Grounding:**  
   Whitespace-Normalisierung und Vereinheitlichung typografischer Sonderzeichen (Quotes, Dashes, Spaces) vor dem Substring-Match in `_validate_quote_grounding`.
2. **Deterministische Überlappungsprüfung (Span-Deduplizierung):**  
   Prüfung, ob Zitate sich signifikant überlappen (Substring-Beziehung oder Token-Jaccard > Schwellenwert). Bei Überlappung sollte deterministisch nur der spezifischere Eintrag erhalten bleiben.
3. **Mechanische Erkennung von Interview-Strukturen:**  
   Erweiterung von Pass 0 um heuristisches Strippen von Sprecher-Präfixen (`Name: ...`), um die Trennung von Autoren- und Sprecherstimme nicht allein dem LLM aufzubürden.
4. **Normierungsgrundlage abstimmen:**  
   Entweder den Bernays Score auf den tatsächlich an Pass 1 übergebenen Text normieren oder Zitatanteile transparent ausweisen.
