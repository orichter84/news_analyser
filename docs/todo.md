# ToDo & Ausbaustufen

## Implementiert

### Analyse-Engine
- [x] Artikel-Scraping (trafilatura + BeautifulSoup Fallback)
- [x] Paywall-Erkennung: HTML-Marker (Piano/TinyPass, verlagsspezifisch) + Wortanzahl-Fallback
- [x] Titel-Extraktion: og:title → h1 → title-Tag Fallback
- [x] Zwei-Pass-LLM-Architektur (Anonymisierung + Originaltext)
- [x] Anonymisierungs-Preprocessing via spaCy de_core_news_md
- [x] Keyword-Signal als Extremismus-Vorfilter (keywords.py)
- [x] Adapter-Abstraktion (OpenAI, Anthropic, CLI, LM Studio, M365 Copilot)
- [x] Systemprompts als editierbare Markdown-Dateien (pass1.md, pass2.md)

### Indikatoren
- [x] Orwell-Index — reiner Extremismus-Indikator (0.0–1.0, richtungsblind)
- [x] Bernays-Score — Manipulationstechniken pro 1000 Wörter
- [x] Dunning-Kruger-Index — unbelegte Gewissheit (0.0–1.0)
- [x] Politische Strömung — benannte Labels (`list[str]`)
- [x] Themenbereich — Klassifikation (Politik, Wirtschaft, Technologie, …)
- [x] Manipulation Targets — Entität, Richtung, Rolle (strukturiertes JSON) mit optionalen Zitat-Belegen (`direction_quote`, `rolle_quote`)
- [x] Rollen-KB — 10 Rollen in `roles.json`, Lazy Loading via `role_store.py` + `{{ROLES}}`-Placeholder im Prompt, Fuzzy-Normalisierung
- [x] Techniken-DB — 24 dokumentierte Techniken mit semantischer Normalisierung
- [x] Politische Strömung mit Zitat-Belegen — `pass2.md` gibt pro Label einen charakteristischen Textzitat zurück; Detailansicht zeigt Quote unter dem Label
- [x] Modell-Metadaten — `llm_provider` und `llm_model` werden in jeder Analyse gespeichert; LM Studio erkennt das aktive Modell automatisch per `/api/v0/models`

### Datenbank & RAG
- [x] ChromaDB lokal persistent (articles, orwell_anchors, techniques)
- [x] ChromaDB HTTP-Server-Integration — alle Repositories nutzen `HttpClient` statt `PersistentClient`. Zentraler `chroma_client.py` liest `CHROMA_HOST` + `CHROMA_PORT` aus ENV (Standard: `localhost:8001`). Ermöglicht Netzwerkbetrieb ohne Code-Änderung.
- [x] RAG-Anker-Korpus (anchor_store.py, lazy-loaded ab 5 Ankern)
- [x] Techniken-Collection mit Auto-Seeding aus technique_store.py

### Feed & Datenerfassung
- [x] RSS-Feed-Collector mit Dedup-Check gegen DB
- [x] Manueller und automatischer Feed-Modus (FEED_MODE env)
- [x] Themenvorfilter (topic_filter.py, keyword-basiert, kein LLM-Call)
- [x] FEED_TOPICS konfigurierbar per Env-Variable (inkl. `all` für kein Filter)

### Statistiken
- [x] Statistik-Report (Top-Techniken, Bernays, Orwell, DK, Domains, Sentiments)
- [x] Politische Strömung in stats.py
- [x] Thema-Bernays-Auswertung (thema_bernays)
- [x] Entity-Targeting-Auswertung (entity_targeting)

### Web-UI
- [x] FastAPI Backend mit allen REST-Endpunkten
- [x] Angular 17+ Frontend (Standalone Components, Lazy Loading)
- [x] Dashboard — KPI-Kacheln, Top-Techniken, Top-Strömungen, letzte Artikel
- [x] Artikel-Liste — filterbar nach Domain, Orwell-Range, Limit
- [x] Artikel-Detail — Scores, Framing, Manipulation Targets, Techniken (verlinkt)
- [x] Statistik-Seite — Sub-Navigation (Übersicht / Verlauf), Domain-Tabelle, Top-Techniken, Strömungen
- [x] Statistik-Verlauf — Tagesbasierte Liniendiagramme (Orwell, Bernays, DK) mit Domain-Filter und Median/Maximum-Toggle (Chart.js)
- [x] Paywall-Warnung beim manuellen Einreichen — eigener Job-Status `paywall` mit Hinweis im UI
- [x] URL-Submission — Formular mit Job-Status-Polling
- [x] Techniken-Übersicht `/techniques` — gruppiert nach Kategorie
- [x] Techniken-Detail `/techniques/:id` — eigene URL pro Technik (verlinkbar)
- [x] "Über dieses Projekt" `/knowledge` — Methodik, Indikatoren, Quellen

### Dokumentation & Validierung
- [x] Erster Konzepttest mit Kalibrierungsergebnissen (docs/konzept/base-tests.md)
- [x] Bias-Validation: Symmetrie-Tests mit Gruppensubstitution (docs/konzept/bias-validation/)
- [x] Architektur-Dokumentation (docs/analyse_architektur.md)
- [x] Refaktorierung Orwell-Index als Konsequenz der Symmetrie-Tests dokumentiert

---

## Offen

### 🔴 Priorität

- [~] **Netzwerk-Betrieb / Multi-Gerät** — ChromaDB läuft als HTTP-Server, `CHROMA_HOST`/`CHROMA_PORT` per ENV konfigurierbar ✅. Offen: `/config`-Endpoint mit Feature-Flags (`SUBMIT_ENABLED=true|false`), Frontend blendet "Einreichen" je nach Flag aus. Ziel: Mac Mini = Viewer-Modus (Netzwerk-ChromaDB, kein Submit).

### Auswertung & Visualisierung
- [ ] **entity_targeting und thema_bernays in /stats API** — Endpunkt exponieren und im Frontend visualisieren
- [ ] **Quellenvergleich** — Interaktives Balkendiagramm Domain × Orwell-Index (Chart.js)
- [x] **Zeitverlauf** — Score-Entwicklung pro Quelle/Thema über Zeit (Liniendiagramm)
- [ ] **Technik-Heatmap** — Domain × Technik als Matrix in der Stats-Ansicht
- [ ] **Richtung/Rolle-Korrelation** — Empirische Auswertung: Hypothese "Passivität = Positiv" (positive Manipulation targets fast immer Opfer, kein handelnder positiver Akteur)

### Frontend
- [ ] **Pagination** — Artikel-Liste und Backend-Endpoint auf Cursor- oder Offset-Pagination umstellen (relevant ab ~500 Artikeln)

### Datenerfassung
- [ ] **Feed-Health-Check** — Beim Start prüfen ob alle Feed-URLs erreichbar sind, tote Feeds melden
- [ ] **MSN-Feed** — MSN Deutschland als zentraler Aggregator testen
- [ ] **Englische Feeds** — BBC, Reuters, AP, The Guardian als Gegenquellen zu deutschen Portalen. Spracherkennung im Scraper ergänzen (langdetect o.ä.), Keyword-Listen für Englisch.
- [ ] **Russische Gegenquellen** — TASS English, RIA Novosti English als methodischen Spiegel. Nicht als Wahrheitsquelle, sondern zur Diskrepanzerkennung: gleicher Vorfall, andere Darstellung.

### Cross-Source-Verifikation
- [ ] **Ereignis-Clustering** — Semantisch ähnliche Artikel zum selben Vorfall in ChromaDB gruppieren (Query auf anonymisierten Text, Zeitfenster ±24h). Grundlage für Quellen-Vergleich.
- [ ] **Diskrepanz-Detektor** — Für geclusterte Artikel: Orwell-Index, Techniken und Manipulation Targets vergleichen. Große Abweichungen zwischen Quellen als Warnsignal melden.
- [ ] **Strategische Omission** — Erkennen wenn ein Ereignis in deutschen Quellen berichtet wird, aber wichtige Kontextinformationen fehlen die in englischen/nicht-westlichen Quellen vorhanden sind.
- [ ] **Agentur-Bias-Erkennung** — Wenn alle deutschen Portale denselben Wortlaut verwenden (hohe semantische Ähnlichkeit), als "Agenturmeldung ohne Eigenrecherche" markieren. Konsens ≠ Wahrheit.

### Qualität & Tests
- [ ] **Symmetrie-Tests erweitern** — Weitere Substitutionspaare (Schwarze/Weiße, Migranten/Einheimische, Linke/Rechte)
- [ ] **Keyword-Listen** — Gegner-Framing-Filter (Keywords in Anführungszeichen als "zitiert" markieren)
- [ ] **Keyword Lazy-Update** — SQLite-DB speichert Keyword-Treffer mit Kontext-Satz; periodischer Job klassifiziert affirmativ vs. zitierend und schreibt Korrekturen zurück in die Keyword-Listen
- [ ] **Manuell kuratierter Anker-Korpus** — Initiale Kuration mit verifizierten Referenzartikeln für bessere Cold-Start-Kalibrierung
- [ ] **Unit Tests** — tests/ befüllen: Scraper-Mocks, JSON-Parser, Adapter-Interface
- [ ] **Analyse-Validierung** — Prüfen ob zurückgegebene quote-Felder tatsächlich im Artikeltext enthalten sind

### LLM-Betrieb
- [ ] **Hybrid-Provider** — Nach Pass 1: wenn `orwell_index > threshold` oder Domain in Prioritätsliste → tiefer Cloud-Provider (`LLM_PROVIDER_DEEP`), sonst lokales Modell (`LLM_PROVIDER`). Konfigurierbar via `DEEP_ANALYSIS_THRESHOLD` in `.env`. Warten auf Apple Silicon Hardware für lokalen LLM-Betrieb.
- [ ] **MCP-Server** — Lokaler MCP-Server als Brücke zwischen Claude Desktop (Cloud-Scheduling) und lokalem Backend. Tools: `trigger_feed()`, `get_stats()`. Ermöglicht Remote-Trigger ohne öffentlich erreichbares Backend.

### Export & Integration
- [ ] **CSV/JSON-Export** — Alle gespeicherten Analysen exportieren
- [ ] **Authentifizierung** — Optionaler API-Key-Schutz für den Analyse-Endpunkt
- [ ] **Logging** — Strukturiertes Logging in logs/ statt print()-Ausgaben
