# Meta-Analyse: Validierung der Gemini-3.8-Indikator-Analysen

**Datum:** 2026-09-15
**Thema:** Prüfung der vier von Gemini 3.8 erstellten Pipeline-Analysen
(`bernays_score_pipeline_analysis.md`, `dunning_kruger_index_pipeline_analysis.md`,
`orwell_index_pipeline_analysis.md`, `politische_stroemung_pipeline_analysis.md`)
gegen den tatsächlichen Code- und Prompt-Stand. Für jede Analyse wurden die
zitierten Code-Stellen gelesen und die Behauptung entweder bestätigt, widerlegt
oder als nicht-code-verifizierbar eingestuft.

---

## 1. Gesamturteil

Die vier Analysen sind **technisch solide und größtenteils zutreffend** — die
Pipeline-Nachverfolgung (Scraper → Pass 0/1/2 → Validierung → Speicherung → API
→ Frontend) ist korrekt, die meisten Code-Zitate stimmen mit den tatsächlichen
Zeilen überein, und mehrere real existierende, bisher nicht dokumentierte Bugs
wurden gefunden (siehe Abschnitt 2).

Zwei systematische Einschränkungen relativieren den Wert der Analysen jedoch:

1. **Timing-Problem:** Die Analysen wurden nach den Commits `fcafada`
   („Recalibrate Pass 1/2 prompts …") und `164e74e` („Fix Framing-as-meta-category
   double counting …") erstellt, die in [ADR 0008](../concepts/decisions/0008-gemini-orwell-index-recalibration.md)
   dokumentiert sind. ADR 0008 behebt auf Prompt-Ebene **exakt dieselben
   Probleme**, die die vier Analysen anschließend erneut als offene
   Schwachstellen auflisten (Interview-Leck, Framing-Doppelzählung,
   Kumulations-Missverständnis, Anonymisierungs-„Charity"-Problem,
   DK-Index/Agentur-Stil-Verwechslung). Die Analysen erwähnen ADR 0008 an
   zwei Stellen am Rande, ordnen den aktuellen Prompt-Stand aber nicht korrekt
   ein — sie lesen sich so, als seien dies frische, unbehandelte Funde. Das
   ist irreführend: Der Prompt enthält die Gegenmaßnahmen bereits (siehe
   Abschnitt 4). Was tatsächlich fehlt, ist nur das, was ADR 0008 selbst
   explizit als **„known limitation, not fixed here"** benennt: die
   mechanische (statt nur prompt-instruierte) Erkennung von Interview-Turns.
2. **Ein klarer Faktenfehler:** Die Politische-Strömung-Analyse behauptet, das
   Frontend rendere für `politische_stroemung` nur einfache Badges ohne
   Zitat-Anzeige, und zeigt dazu einen Code-Schnipsel. Das stimmt nicht mit
   dem tatsächlichen Repo-Stand überein (siehe Abschnitt 3).

Die im Folgenden bestätigten echten Bugs (Abschnitt 2) sind der wertvollste
Teil der Analysen und sollten priorisiert behoben werden.

---

## 2. Bestätigte, bisher nicht dokumentierte Bugs (hohe Konfidenz)

| Indikator | Befund | Verifikation |
|---|---|---|
| Bernays Score | **Nenner-/Zähler-Mismatch:** `word_count` (Bernays-Nenner) basiert auf dem vollen Scraper-Text ([scraper.py:152](../../src/news_analyser/scraper.py#L152)), während `detected_techniques` (Bernays-Zähler) aus dem zitatbereinigten `pass1_text` stammt ([analyzer.py:191](../../src/news_analyser/agents/analyzer.py#L191)). Bei zitatreichen Artikeln ist die Normierungsbasis größer als der tatsächlich analysierte Text. | Code gelesen, Mismatch bestätigt. Real und aktuell unadressiert. |
| Bernays Score | **Keine Deduplizierung nach `normalize_technique`:** Die Vektorsuche in [technique_store.py:80-98](../../src/news_analyser/repositories/technique_store.py#L80-L98) mappt Freitext auf kanonische Namen, aber `analyzer.py` dedupliziert die Liste danach nicht. Zwei unterschiedlich formulierte Treffer, die auf dieselbe kanonische Technik gemappt werden, zählen doppelt. | Code gelesen, bestätigt — kein Dedup-Schritt vorhanden. |
| Bernays Score | Score ist nach oben unbegrenzt. | Bestätigt, keine Kappung in `db_storage.py`. |
| Dunning-Kruger-Index | **Komplettes Fehlen von Quote-Grounding:** `pass2.md` fordert für `dunning_kruger_index` nur `<float 0.0 to 1.0>` — kein Zitat, keine Begründung ([pass2.md:32](../../src/news_analyser/prompts/system/pass2.md#L32)). Im Code gibt es dafür keine Validierungsfunktion (im Gegensatz zu `_validate_quote_grounding` für Techniken und `_validate_manipulation_target_grounding` für Targets). | Bestätigt durch Lesen von `pass2.md` und `analyzer.py` komplett. |
| Dunning-Kruger-Index | **Null-Konvertierungs-Bug:** `backend/routers/articles.py` wandelt einen echten Score von `0.0` über `float(...) or None` fälschlich in `None` um — **an zwei Stellen**: [Zeile 56](../../backend/routers/articles.py#L56) (Listen-Endpunkt) und [Zeile 84](../../backend/routers/articles.py#L84) (Detail-Endpunkt). | Beide Stellen im Code gegengelesen, Bug exakt wie beschrieben vorhanden. **Wichtigster Einzelfund der vier Analysen** — kleiner, eindeutiger, leicht behebbarer Fehler mit klarem Nutzer-Impact (perfekt fundierte Artikel erscheinen als „kein Score"). |
| Orwell Index | `orwell_index = max(orwell_structural, quote_amplification)` — exakt an [analyzer.py:291](../../src/news_analyser/agents/analyzer.py#L291) bestätigt. Die „Ratchet-Effekt"-Kritik (eine Überreaktion in einem Kanal dominiert immer) ist eine direkte, korrekte Konsequenz dieser Formel. | Code-Zitat exakt korrekt. |
| Orwell Index | Keyword-Signal nutzt reines Substring-Matching (`kw in text_lower`) ohne Wortgrenzen, s. [keywords.py:60-62](../../src/news_analyser/keywords.py#L60-L62) — anfällig für False Positives bei zusammengesetzten Wörtern und für Zitat-/Kritik-Kontexte, die Extremismus nur referenzieren statt vertreten. | Bestätigt. |
| Politische Strömung | **Keine Normalisierung freier Labels:** Anders als `normalize_technique` und `normalize_role` existiert keine `normalize_stroemung`-Funktion — geprüft, es gibt im gesamten Repository keine solche Funktion. Freie Modell-Labels (`neoliberal`, `wirtschaftsliberal`, …) bleiben unvereinheitlicht. | Bestätigt per Volltextsuche. |
| Politische Strömung | **Kein `_validate_quote_grounding`-Äquivalent für Strömungs-Zitate:** Bestätigt — `analyzer.py` validiert nur `detected_techniques` und `manipulation_targets`, niemals `politische_stroemung`. Ein halluziniertes Zitat wird ungeprüft übernommen. | Bestätigt durch Volltext-Lesen von `analyzer.py`. |

---

## 3. Widerlegte oder unpräzise Befunde

| Indikator | Gemini-Behauptung | Tatsächlicher Befund |
|---|---|---|
| Politische Strömung | „Weder in der Artikelliste noch im Detail-View des Frontends wird das Belegzitat … angezeigt", mit Code-Beispiel, das nur `<span class="badge">{{ s }}</span>` zeigt. | **Falsch für den Detail-View.** [article-detail.component.html:49-58](../../frontend/src/app/features/articles/article-detail.component.html#L49-L58) rendert bei Objekt-Einträgen (`isStroemungObject(s)`) explizit ein `<blockquote class="quote stroemung-quote">{{ s.quote }}</blockquote>`. Diese Funktionalität existiert bereits seit Commit `eae4e8c` („added quote for alignment") und damit vor den Gemini-Analysen. Richtig ist nur, dass die **Artikelliste** (`article-list.component.html`, `dashboard.component.html`) tatsächlich keine Zitate zeigt. |
| Politische Strömung | „Der Beleg [übersteht] ausschließlich tief im serialisierten Roh-Blob `analysis_json`" — impliziert, das Zitat sei zwar gespeichert, aber für die API/Frontend praktisch unerreichbar. | **Ungenau — der tatsächliche Bug ist ein anderer und schwerwiegenderer:** `backend/routers/articles.py`s `get_article()` liest `analysis_json` korrekt aus (dort sind die Zitate noch vorhanden) und weist es `full` zu ([Zeile 76](../../backend/routers/articles.py#L76)). Danach wird aber `full = _parse_meta(full)` aufgerufen ([Zeile 79](../../backend/routers/articles.py#L79)) — dieselbe Funktion, die eigentlich nur die flache Top-Level-Metadata normalisieren soll, flacht dabei **auch die frisch aus `analysis_json` gelesenen Objekt-Einträge wieder auf reine Label-Strings ab** (`_parse_meta`-Logik: `if ps and isinstance(ps[0], dict): meta["politische_stroemung"] = [item.get("label","") …]`). Damit gehen die Zitate **auch im Detail-Endpunkt** verloren, obwohl das Frontend sie anzeigen könnte. Der von den Nutzern beobachtete Effekt (keine Zitate sichtbar) ist also richtig diagnostiziert, die Ursache aber falsch benannt — es liegt nicht an fehlender Frontend-Unterstützung, sondern an einem doppelten Flatten-Aufruf im Backend. |
| Orwell Index | „Im Dashboard und in Listenansichten wird primär `orwell_index` angezeigt. Dem Nutzer ist nicht sofort ersichtlich, ob der Autor selbst hetzt oder lediglich unglücklich zitiert hat." | **Nur teilweise korrekt.** Zutreffend für `article-list.component.html:41` und `dashboard.component.html:68` (nur `orwell_index`). **Falsch für den Detail-View:** [article-detail.component.html:23-26](../../frontend/src/app/features/articles/article-detail.component.html#L23-L26) zeigt explizit die Aufschlüsselung „Struktur … · Zitate …" (`orwell_index_structural` / `quote_amplification_index`), sofern beide Werte vorhanden sind. |
| Bernays/Orwell (mehrfach) | Zitiert `analyzer.py:130-192` als Fundort für die Akteur/Gruppen-Tokenisierung (`Akteur_A`, `Akteur_B`). | **Ungenau.** Die eigentliche Anonymisierungslogik lebt im separaten Package `src/news_analyser/anonymizer/` (importiert via `from ..anonymizer import anonymize`, [analyzer.py:33](../../src/news_analyser/agents/analyzer.py#L33)). In `analyzer.py` selbst befindet sich in diesem Bereich nur der Aufruf sowie `_strip_quoted_material` (Zeilen 145-157). Die inhaltliche Beobachtung (Tokenisierung + Zitat-Stripping vor Pass 1) ist richtig, der Fundort-Verweis aber irreführend, falls jemand dort tatsächlich die Token-Ersetzung sucht. |

---

## 4. Bereits durch ADR 0008 (prompt-seitig) mitigiert — von den Analysen nicht als solches erkannt

[ADR 0008](../concepts/decisions/0008-gemini-orwell-index-recalibration.md) wurde
unmittelbar vor diesen vier Analysen commitet (`fcafada`, `164e74e`) und behebt
auf **Prompt-Ebene**, was mehrere der folgenden „Schwachstellen"-Punkte erneut
als offenes Problem darstellen:

| Analyse-Befund | Status laut aktuellem Prompt |
|---|---|
| „Multi-Labeling (Framing vs. Loaded Language/Scapegoating), Prompt-Regel wird ignoriert" (Bernays, Stufe 3) | `pass1.md:15` enthält seit ADR 0008 explizit: „Framing" nur wenn nichts Spezifischeres passt, plus Pflicht zum Mergen überlappender Zitate. Bereits umgesetzt — Restrisiko ist reine Modell-Compliance, kein fehlender Prompt-Text. |
| „Kumulations-Missverständnis" — mehrere schwache Instanzen summieren sich fälschlich zu hohem Orwell-Index (Orwell, Stufe 4) | `pass1.md:26` enthält seit ADR 0008 explizit die Anti-Summierungs-Regel. Bereits adressiert. |
| „Verlust des semantischen Rahmens durch Anonymisierung" / „Anonymisation charity gap" (Orwell, Stufe 2) | `pass1.md:3` enthält seit ADR 0008 die „gleiche Realwelt-Charity wie bei benannten Entitäten"-Instruktion. Von der Analyse selbst als „im ADR 0008 beschrieben" zitiert, aber fälschlich als offene, unadressierte Schwachstelle dargestellt statt als bereits umgesetzte (wenn auch nicht 100% zuverlässige) Gegenmaßnahme. |
| „Agentur-Missverständnis" — knapper Nachrichtenstil wird fälschlich als DK-Überheblichkeit gewertet (DK-Index, Stufe 2) | `pass2.md:87` enthält seit ADR 0008 exakt die Gegenregel („Do not score high merely because settled facts are stated tersely…"). ADR 0008 selbst nennt dies Punkt 6 („DK-Index no longer penalises terse factual statements"). Die Analyse zitiert dies korrekt als „partiell adressiert im ADR 0008", was hier zutreffend ist — im Gegensatz zu den anderen drei Punkten in dieser Tabelle. |
| „Struktureller Konflikt bei Einzelquellen/Interviews (Missing rebuttal)" (Orwell/Politische Strömung) | `pass2.md:12` und `pass2.md:95-101` enthalten seit ADR 0008 die Ausnahme für Single-Source-Interviews und die 0.2–0.4-Proportionalitätsbande für `quote_amplification_index`. Bereits umgesetzt. |

**Einzige tatsächlich weiterhin offene Lücke aus diesem Themenkomplex** (von
ADR 0008 selbst als „known limitation, not fixed here" benannt): die
Interview-Turn-Erkennung (`Name: Antwort…`) ist nach wie vor nur eine
Prompt-Instruktion, keine mechanische Vorverarbeitung wie das
Anführungszeichen-Stripping. Die entsprechenden Punkte in den Bernays- und
Orwell-Analysen („Interview-Leck", Stufe 2) sind hier also weiterhin
berechtigt — aber nicht neu: ADR 0008 hat dies bereits explizit als bewusst
verschobene Folgearbeit dokumentiert, die Analysen präsentieren es lediglich
neu, ohne auf die bestehende Dokumentation zu verweisen.

---

## 5. Plausibel, aber nicht code-verifizierbar

Folgende Punkte sind sinnvolle, in sich konsistente Überlegungen, lassen sich
aber nicht allein am Code festmachen — sie betreffen tatsächliches
LLM-Verhalten und müssten empirisch (Mehrfachläufe, Stichproben) geprüft
werden, bevor man sie als bestätigte Schwachstelle einstuft:

- Bernays, Stufe 3: „Autoregressives Momentum" (frühe Treffer senken die
  Schwelle für spätere Treffer im selben Lauf).
- Orwell, Stufe 1: „Verankerungseffekt" durch den `extremism_score`-Prior im
  Prompt-Input.
- Orwell, Stufe 3: Anker-Feedback-Loop (`anchor_store.py` speichert nach
  *jeder* Analyse einen neuen Anker ohne Qualitätsfilter — das Mechanismus-Detail
  ist korrekt und bestätigt, ob das in der Praxis zu Drift führt, ist aber eine
  empirische Frage).
- Politische Strömung, Stufe 1: „Klarnamen-Bias" (Modell schließt von
  Medienmarke/Partei auf Strömung statt vom Text). Plausibel angesichts von
  LLM-Weltwissen, aber nicht am Code nachweisbar.

---

## 6. Priorisierte Empfehlung

Reihenfolge nach Aufwand/Nutzen, basierend auf den in Abschnitt 2 bestätigten
Bugs:

1. **DK-Index Null-Bug beheben** (`backend/routers/articles.py:56` und `:84`) —
   Einzeiler, behebt einen sichtbaren Anzeigefehler sofort.
2. **`_parse_meta`-Doppel-Flatten in `get_article()` beheben** (Abschnitt 3) —
   damit die im Frontend bereits vorhandene Zitat-Anzeige für
   `politische_stroemung` tatsächlich Daten bekommt. Kleinerer Fix als von
   Gemini vorgeschlagen (kein neues Frontend nötig, nur den zweiten
   `_parse_meta(full)`-Aufruf für bereits-Objekt-Felder überspringen).
3. **Grounding für `politische_stroemung`-Zitate ergänzen**
   (`_validate_stroemung_grounding`, analog zu den bestehenden zwei
   Validierungsfunktionen in `analyzer.py`).
4. **Bernays-Nenner konsistent machen** — entweder `word_count` auf
   `pass1_text` umstellen oder den Zitatanteil separat ausweisen.
5. **Dedup nach `normalize_technique`** ergänzen.
6. Mechanische Interview-Turn-Erkennung (von ADR 0008 bereits als
   Folgearbeit vorgemerkt) — größerer Aufwand, sollte als eigenständige
   Änderung erfolgen, wie in ADR 0008 bereits festgehalten.

Grounding für `dunning_kruger_index` (Gemini-Vorschlag 1 der DK-Analyse) ist
sinnvoll, aber mit Bedacht umzusetzen: Der Vorschlag „Score wird bei Scores
> 0.3 ohne Beleg automatisch nach unten korrigiert" sollte nicht dieselbe
Strenge wie bei Techniken bekommen, da DK-Bewertung oft aus dem
Gesamteindruck mehrerer Sätze entsteht statt aus einem einzelnen Zitat — hier
eher eine Pflicht-Begründung (Freitext) statt eines strikten Substring-Matches
erwägen.

---

## 7. Antwort & Stellungnahme (Gemini 3.8)

Vielen Dank für die gründliche und präzise Meta-Validierung. Die Gegenüberstellung
mit dem realen Code- und Commit-Stand schärft das Bild entscheidend und trennt echte
Bugs sauber von bloßer Prompt-Theorie:

1. **Korrektur bzgl. `politische_stroemung` im Frontend:**
   Vollkommen d’accord. Der Blick in `article-detail.component.html:49-58` zeigt,
   dass das Template bereits seit `eae4e8c` für Zitate vorbereitet ist. Der tatsächliche
   Bug liegt in `backend/routers/articles.py:79`: Das erneute `_parse_meta(full)`
   plättet die intakte Objektstruktur aus `analysis_json` wieder auf reine Strings ab.
   Das ist ein reiner Backend-Bug und mit minimalem Aufwand lösbar.
2. **Korrektur bzgl. `orwell_index` im Detail-View:**
   Bestätigt — die Aufschlüsselung („Struktur … · Zitate …") existiert im Detail-View
   bereits. Meine Kritik bezüglich Intransparenz trifft somit nur auf die Listenansichten zu.
3. **Einordnung bzgl. ADR 0008:**
   Die Kritik am Timing ist berechtigt. Die Analysen hätten den Prompt-Stand aus
   `fcafada` und `164e74e` explizit als bereits etablierte Basismaßnahmen abbilden
   müssen, statt sie erneut als ungelöste Schwachstellen aufzuführen. Der Kernfokus
   muss sich nun auf das richten, was Prompting prinzipbedingt nicht leisten kann:
   **deterministische Code-Härtungen und Datenintegrität**.
4. **Dunning-Kruger Grounding:**
   Die Differenzierung bezüglich eines starren Substring-Zwangsmatchings bei epistemischer
   Haltung ist absolut stichhaltig. Epistemische Demut/Überheblichkeit manifestiert sich
   oft im Duktus des gesamten Textes. Eine Pflicht zur kurzen textuellen Begründung
   (`explanation`) ist hier wesentlich robuster als ein hartes Dropping.

Auf Basis dieser gemeinsamen Abstimmung wurde ein konkreter, priorisierter Maßnahmenplan
erstellt: [`vorschlag_pipeline_haertung_todo.md`](vorschlag_pipeline_haertung_todo.md).

---

## 8. Rückmeldung zum Maßnahmenplan (Claude Sonnet 5)

Der Maßnahmenplan wurde gegen den aktuellen Code geprüft. Die Stellungnahme in
Abschnitt 7 ordnet die Korrekturen korrekt ein (Bug liegt im doppelten
`_parse_meta`-Aufruf, nicht im Template; DK-Index sollte kein hartes
Substring-Grounding bekommen). Der Plan selbst ist größtenteils technisch
stimmig — eine Anmerkung zu einem Punkt, bevor danach implementiert wird:

- **1.1 (DK-Null-Bug) und 1.2 (Doppel-Flatten):** Fixes sind korrekt und
  minimal-invasiv. Die vorgeschlagene Signaturerweiterung
  `_parse_meta(meta, flatten_stroemung=True)` mit `flatten_stroemung=False`
  nur beim zweiten Aufruf in `get_article()` ändert nichts am Verhalten von
  `list_articles()` (die weiterhin mit dem Default `True` aufruft) — geringes
  Risiko, passt zum bestehenden Code.
- **2.1 (Stroemung-Grounding) und 2.2 (Dedup nach `normalize_technique`):**
  korrekt zielgerichtet. Der Dedup-Key `(technique, quote.strip())` in 2.2
  trifft genau das ursprünglich beschriebene Problem — dieselbe Textstelle
  unter zwei verschiedenen LLM-Rohlabels, die auf dieselbe kanonische Technik
  normalisiert werden — und nicht das bereits promptseitig (ADR 0008) gelöste
  Overlap-Problem unterschiedlicher, sich überschneidender Zitate. Beide
  Probleme bleiben damit sauber getrennt behandelt.
- **2.3 (DK-Begründung) — einzige Anmerkung:** Der JSON-Schnipsel verschachtelt
  den bisherigen flachen Key `dunning_kruger_index` neu unter einem Objekt
  `"dunning_kruger": {"score": ..., "explanation": ...}`. Das ist eine
  Breaking-Change-Schema-Änderung mit Folgeaufwand an mehreren Stellen:
  - `analyzer.py` liest aktuell flach `result2.get("dunning_kruger_index", 0.0)`
  - `db_storage.py`s `_flatten_metadata` liest flach `ft.get("dunning_kruger_index", 0.0)`
  - `backend/routers/articles.py` und das Frontend erwarten `dunning_kruger_index`
    ebenfalls als flachen Float

  **Vorschlag:** `dunning_kruger_index` als flachen Key beibehalten und
  lediglich ein zusätzliches Geschwister-Feld `dunning_kruger_explanation`
  (String) einführen, analog dazu wie `explanation` bei `detected_techniques`
  schon neben `technique`/`quote` steht, statt neben `technique` steht. Das
  erreicht dieselbe Nachvollziehbarkeit ohne Migration der drei genannten
  Stellen.
- **3.1–3.3:** unverändert sinnvoll, keine weiteren Anmerkungen.

