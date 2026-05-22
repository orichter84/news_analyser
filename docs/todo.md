# ToDo & Ausbaustufen

## Implementiert

- [x] Artikel-Scraping (trafilatura + BeautifulSoup Fallback)
- [x] LLM-Analyse-Agent mit strukturiertem JSON-Output
- [x] Systemprompt als editierbare Markdown-Datei ausgelagert
- [x] Vektordatenbank (ChromaDB, lokal persistent)
- [x] Connector-Abstraktion (OpenAI, Anthropic, CLI, LM Studio, M365 Copilot)
- [x] CLIConnector (Claude Code CLI als Subprocess)
- [x] Statistik-Report (Top-Techniken, Bias-Verteilung, Domains, Sentiments)
- [x] RSS-Feed-Collector mit Dedup-Check gegen DB
- [x] Manueller und automatischer Feed-Modus (konfigurierbar per Env-Variable)

---

## Offen

### Auswertung & Analyse

- [ ] **Quellen-Vergleich** — Bias-Score-Vergleich zwischen Domains als tabellarische Übersicht (`--stats --compare`)
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
