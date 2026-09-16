# Analyse: Sampling-Konfiguration als bisher unbeachtete Stellschraube

**Datum:** 2026-09-16
**Thema:** Zwei Adapter-Konfigurationswerte (`temperature`, `json_mode`), die bei der
Dokumentation der Prompting-Techniken ([`prompting_patterns.md`](../reference/prompting_patterns.md))
auffielen, aber nichts mit Prompt-Text zu tun haben — Einordnung im Kontext der
Lauf-zu-Lauf-Varianz, die bei den vier lokalen Digitaltrainer-Läufen beobachtet wurde
(siehe [ADR 0010](../concepts/decisions/0010-quote-amplification-grounding-and-debug-run-history.md)).

---

## 1. Befund: `temperature`

* **Ort im Code:** `llm_adapter`s `OpenAIAdapter` (`.venv/.../llm_adapter/openai_adapter.py`) — Default `temperature: 0.2`.
* **Konfiguration:** Die `gemini`-Provider-Registrierung
  (`src/news_analyser/__init__.py`) überschreibt `temperature` nicht — Pass 0, 1 und 2
  laufen damit alle bei `0.2`, nicht bei `0`.
* **Bei Claude (`cli`-Adapter):** laut dessen eigenem Docstring gar nicht steuerbar —
  *"temperature und max_tokens werden vom CLI nicht unterstützt und ignoriert."*
  Provider-Vergleiche (ADR 0007/0008) vergleichen damit implizit auch unterschiedliche
  Sampling-Regime, nicht nur unterschiedliche Modelle.

**Einordnung (Hypothese, nicht bestätigt):** `temperature > 0` ist der Standardmechanismus,
über den Sampling-Nichtdeterminismus in ein LLM gelangt — bei gleichem Prompt und
gleichem Input variiert die Token-Auswahl von Lauf zu Lauf. Das ist ein plausibler
*Teilbeitrag* zu der in ADR 0010 beobachteten Bernays-/Orwell-Schwankung (Struktur
0.45–0.65, Bernays 1.79–7.15 über vier Läufe desselben Artikels). Es ist aber
**nicht belegt**, dass `temperature=0.2` die Hauptursache ist — ADR 0008 führt die
verbleibende Instabilität nach der Prompt-Rekalibrierung stattdessen primär auf
Modell-Sampling-Verhalten bei "graduated judgment"-Aufgaben zurück, ohne Temperature
als Variable zu isolieren. Beides schließt sich nicht aus, wurde aber nie
gegeneinander getestet.

---

## 2. Befund: `json_mode`

* **Ort im Code:** derselbe `OpenAIAdapter` unterstützt ein `json_mode`-Flag, das
  Providern mit OpenAI-kompatiblem `response_format={"type": "json_object"}`
  natives, constrained JSON-Decoding anfordert. Default: `False`.
* **Konfiguration:** Die `gemini`-Registrierung setzt es nicht — JSON-Compliance läuft
  ausschließlich über die Prompt-Anweisung ("Return ONLY a single, valid JSON object")
  plus den nachgelagerten Fallback in `_extract_json`/`json_repair` (`analyzer.py`).

**Einordnung:** Anders als bei Temperature ist hier **kein plausibler Zusammenhang mit
den beobachteten Score-Schwankungen** zu erwarten — `json_mode` beeinflusst, *ob* die
Antwort valides JSON ist (Parse-Erfolg), nicht *welche* Werte das Modell wählt. Es ist
ein separates Robustheits-Thema (Ausfallsicherheit der Pipeline bei malformed Output),
kein Kandidat zur Erklärung der Bernays-/Orwell-Varianz. Beide Funde werden hier nur
gemeinsam dokumentiert, weil sie an derselben Stelle (Adapter-Konfiguration) auffielen.

---

## 3. Handlungsempfehlung

1. **Kontrollierter Vergleichslauf, bevor an der Konfiguration gedreht wird:** denselben
   Artikel (z. B. wieder den Digitaltrainer-Artikel) mehrfach bei `temperature=0` gegen
   mehrfach bei `temperature=0.2` laufen lassen und die Bernays-/Orwell-Schwankungsbreite
   vergleichen. Die Debug-Run-Archivierung aus ADR 0010
   (`data/debug_runs/<run_id>/`) macht das jetzt ohne Datenverlust zwischen den Läufen
   möglich. Erst danach lässt sich sagen, ob Temperature ein relevanter Hebel ist oder
   ob die Varianz überwiegend anderswo entsteht (Technikzahl-Sampling, wie in ADR 0008
   vermutet).
2. **`json_mode` unabhängig davon aktivieren, als Robustheits-, nicht als
   Varianz-Maßnahme** — reduziert das Risiko von JSON-Parse-Fehlern bei der `gemini`-Registrierung,
   ändert aber nichts an der Score-Verteilung selbst. Geringes Risiko, sollte vor der
   Aktivierung kurz gegen ein paar echte Artikel getestet werden (manche
   OpenAI-kompatible Endpoints setzen `json_mode` unterschiedlich strikt um).
3. **Falls Temperature sich als relevant erweist:** eine bewusste Entscheidung treffen,
   ob Determinismus (niedrige/`0` Temperature) oder Antwortvielfalt beim Wording
   (aktuelle `0.2`) für dieses Projekt der richtige Trade-off ist — nicht implizit über
   einen unveränderten Adapter-Default.
