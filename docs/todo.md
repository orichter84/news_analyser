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

- [x] **Orwell-Index** — Umbau auf reinen Extremismus-Indikator (0.0–1.0, richtungsblind)
- [x] **Politische Strömung** — Neues Feld als `list[str]` mit benannten Labels
- [x] **Few-Shot-Anker** — pass1.md mit Extremismus-Ankern (0.0–1.0)
- [x] **Anonymisierungs-Preprocessing** — Zwei-Pass-Architektur, spaCy de_core_news_md
- [x] **Symmetrie-Tests** — Erste Testfälle dokumentiert: tests/symmetrie/ergebnisse.md
- [ ] **Keyword-Listen** — Auf Extremismus-Symmetrie umstellen (beide Extreme statt links/rechts)
- [ ] **Statistik & Ausgabe** — politische_stroemung in stats.py anzeigen
- [x] **RAG-Anker-Korpus** — Lazy-Loading implementiert, anchor_store.py, aktiv ab 5 Ankern

---

### Web-Oberfläche (Priorität 2)

Ziel: Das System von einem lokalen CLI-Werkzeug zu einer zugänglichen Web-Applikation machen.

#### Backend — FastAPI
- [x] **REST API** — Endpunkte für Artikel-Abfragen, Filter und Statistiken
  - `GET /articles` — Liste mit Filter (domain, orwell-range, limit)
  - `GET /articles/{url}` — Detailansicht mit Zitaten und Erklärungen
  - `POST /analyse` — URL einreichen und Analyse anstoßen (BackgroundTask)
  - `GET /analyse/job/{id}` — Job-Status-Polling
  - `GET /stats` — Aggregierte Statistiken als JSON
  - `GET /search?q=...` — Semantische Suche via ChromaDB
- [ ] **Authentifizierung** — Optionaler API-Key-Schutz für den Analyse-Endpunkt
- [x] **Job-Queue** — Asynchrone Analyse-Jobs (FastAPI BackgroundTasks)

#### Frontend — Angular 17+ Standalone
- [x] **Dashboard** — KPI-Kacheln, Top-Techniken, Top-Strömungen, letzte Artikel
- [x] **Artikel-Liste** — Filterbare Tabelle (Domain, Orwell-Range)
- [x] **Artikel-Detailansicht** — Vollständige Analyse mit Techniken und Zitaten
- [x] **Statistik-Seite** — Balkendiagramme, Portal-Vergleichstabelle, DK-Verteilung
- [x] **URL-Submission** — Formular mit Job-Status-Polling
- [ ] **Pagination** — Artikel-Liste und Backend-Endpoint auf Cursor- oder Offset-Pagination umstellen (relevant ab ~500 Artikeln)
- [ ] **Quellenvergleich** — Interaktives Balkendiagramm Domain × Orwell (Chart.js o.ä.)
- [ ] **Zeitverlauf** — Score-Entwicklung pro Quelle/Thema über Zeit (Liniendiagramm)
- [ ] **Technik-Heatmap** — Domain × Technik als Matrix

#### Stack-Entscheidung
- [x] **FastAPI + Angular 17+ Standalone** — Gewählt. Backend: `backend/`, Frontend: `frontend/`

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
