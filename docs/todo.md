# ToDo & Ausbaustufen

## Implementiert

- [x] Artikel-Scraping (trafilatura + BeautifulSoup Fallback)
- [x] LLM-Analyse-Agent mit strukturiertem JSON-Output
- [x] Systemprompt als editierbare Markdown-Datei ausgelagert
- [x] Vektordatenbank (ChromaDB, lokal persistent)
- [x] Connector-Abstraktion (OpenAI, Anthropic, CLI, LM Studio, M365 Copilot)
- [x] CLIConnector (Claude Code CLI als Subprocess)
- [x] Statistik-Report (Top-Techniken, Bernays-Verteilung, Domains, Sentiments)
- [x] RSS-Feed-Collector mit Dedup-Check gegen DB
- [x] Manueller und automatischer Feed-Modus (konfigurierbar per Env-Variable)
- [x] Erweiterte Metadaten: Autor, Titel, Publikationsdatum, Wortanzahl
- [x] Erster Proof of Concept mit Kalibrierungsergebnissen (docs/test_ergebnisse.md)
- [x] Keyword-Signal als Extremismus-Vorfilter (keywords.py)
- [x] Few-Shot-Anker im Systemprompt (Orwell-Skalenkalibrierung)
- [x] Portal-Durchschnitt im Statistik-Report (domain_averages)
- [x] Konzept Orwell-Index Stabilisierung (docs/orwell_index_konzept.md)

---

## Offen

### Indikator-Refactoring (Priorität 1)

Konzept: docs/orwell_index_konzept.md

- [ ] **Orwell-Index** — Umbau auf reinen Extremismus-Indikator (0.0–1.0, richtungsblind)
- [ ] **Politische Strömung** — Neues Feld als `list[str]` mit benannten Labels
      (z.B. `["sozialistisch", "nationalistisch"]`), ersetzt die numerische links/rechts-Achse
- [ ] **Keyword-Listen** — Auf Extremismus-Symmetrie prüfen und anpassen:
      extreme Rhetorik beider Seiten statt ideologische Richtung
- [ ] **Few-Shot-Anker** — Im Systemprompt auf neuen Orwell-Index (Extremismus) anpassen
- [ ] **RAG-Anker-Korpus** — Kuratierte ChromaDB-Collection `orwell_anchors` aufbauen
      (30–50 Artikel mit validierten Labels, Symmetrie-Testpaare inklusive)
- [ ] **Symmetrie-Tests** — Testpaare bei denen nur die Zielgruppe getauscht wird,
      manuelle Validierung der Label-Konsistenz (LLM-Trainingsbias prüfen)
- [ ] **Statistik & Ausgabe** — Neue Felder in db_storage, stats und CLI-Output

---

### Web-Oberfläche (Priorität 2)

Ziel: Das System von einem lokalen CLI-Werkzeug zu einer zugänglichen Web-Applikation machen.

#### Backend — FastAPI
- [ ] **REST API** — Endpunkte für Artikel-Abfragen, Filter und Statistiken
  - `GET /articles` — Liste mit Filter (domain, score-range, technik, datum)
  - `GET /articles/{id}` — Detailansicht mit Zitaten und Erklärungen
  - `POST /analyse` — URL einreichen und Analyse anstoßen
  - `GET /stats` — Aggregierte Statistiken als JSON
  - `GET /search?q=...` — Semantische Suche via ChromaDB
- [ ] **Authentifizierung** — Optionaler API-Key-Schutz für den Analyse-Endpunkt
- [ ] **Job-Queue** — Asynchrone Analyse-Jobs (FastAPI BackgroundTasks oder Celery)

#### Frontend
- [ ] **Dashboard** — Übersichtsseite mit aktuellen Analysen und Kennzahlen
- [ ] **Quellenvergleich** — Orwell-Index-Vergleich zwischen Domains (Balkendiagramm)
- [ ] **Zeitverlauf** — Score-Entwicklung pro Quelle/Thema über Zeit (Liniendiagramm)
- [ ] **Technik-Heatmap** — Domain × Technik als Matrix
- [ ] **Artikel-Detailansicht** — Vollständige Analyse mit hervorgehobenen Textzitaten
- [ ] **URL-Submission** — Formular zum Einreichen eigener Artikel-URLs

#### Stack-Entscheidung
- [ ] **Option A: FastAPI + HTMX** — Schlank, kein JS-Framework, server-seitiges Rendering. Empfohlen für MVP.
- [ ] **Option B: FastAPI + React** — Mehr Aufwand, aber reichhaltigere Interaktivität. Sinnvoll wenn das Dashboard komplex wird.

#### Knowledge Base
- [ ] **Technik-Glossar** — Erklärung jeder Manipulationstechnik mit Beispielen (FUD, Framing, Loaded Language, etc.)
- [ ] **Methodik-Seite** — Wie funktioniert das System, was misst der Orwell-Index, welche Limitierungen gibt es
- [ ] **Historischer Kontext** — Bernays, Goebbels, Propaganda-Geschichte als Hintergrundartikel
- [ ] **Quellen-Steckbriefe** — Pro analysierter Domain eine Zusammenfassung mit Durchschnittswerten

---

### Auswertung & Analyse

- [ ] **Quellen-Vergleich** — Orwell-Index-Vergleich zwischen Domains als tabellarische Übersicht (`--stats --compare`)
- [ ] **Zeitlicher Verlauf** — Wie verändert sich das Framing eines Themas über Wochen? Plot oder Tabelle pro Domain/Keyword
- [ ] **Technik-Fingerprinting** — Welche Manipulationstechnik nutzt welche Quelle systematisch? Heatmap Domain × Technik
- [ ] **Semantische Suche** — `--search "Suchbegriff"` findet thematisch ähnliche gespeicherte Artikel via ChromaDB `query_similar()`

### Datenerfassung

- [ ] **MSN-Feed einbinden** — MSN Deutschland als zentraler Aggregator für deutschsprachige Quellen in `feeds.txt` ergänzen und testen
- [ ] **Feed-Health-Check** — Beim Start prüfen ob alle Feed-URLs erreichbar sind und tote Feeds melden
- [ ] **Paywall-Erkennung** — Artikel mit zu wenig extrahiertem Text (< 500 Zeichen) als "Paywall" markieren statt als Fehler behandeln

### Export & Integration

- [ ] **CSV-Export** — Alle gespeicherten Analysen als CSV exportieren (`--export csv`)
- [ ] **JSON-Export** — Vollständige Analyse-JSONs als Dump exportieren (`--export json`)
- [ ] **Logging** — Strukturiertes Logging in `logs/` statt `print()`-Ausgaben

### Qualität & Tests

- [ ] **Unit Tests** — `tests/` befüllen: Scraper-Mocks, JSON-Parser, Connector-Interface
- [ ] **Prompt-Versionierung** — Mehrere Systemprompt-Varianten (`prompts/system/`) vergleichbar machen, z.B. `--prompt strict` vs. `--prompt balanced`
- [ ] **Analyse-Validierung** — Prüfen ob zurückgegebene `quote`-Felder tatsächlich im Artikeltext enthalten sind
