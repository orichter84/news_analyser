# Todo & Roadmap

## Implemented

### Analysis Engine
- [x] Article scraping (trafilatura + BeautifulSoup fallback)
- [x] Paywall detection: HTML markers (Piano/TinyPass, publisher-specific) + word count fallback
- [x] Title extraction: og:title → h1 → title tag fallback
- [x] Two-pass LLM architecture (anonymisation + original text)
- [x] Anonymisation preprocessing via spaCy de_core_news_md
- [x] Keyword signal as extremism pre-filter (keywords.py)
- [x] Adapter abstraction (OpenAI, Anthropic, CLI, LM Studio, M365 Copilot)
- [x] System prompts as editable Markdown files (pass1.md, pass2.md)

### Indicators
- [x] Orwell Index — pure extremism indicator (0.0–1.0, direction-blind)
- [x] Bernays Score — manipulation techniques per 1000 words
- [x] Dunning-Kruger Index — unsubstantiated certainty (0.0–1.0)
- [x] Political leaning — named labels (`list[str]`)
- [x] Topic area — classification (Politik, Wirtschaft, Technologie, …)
- [x] Manipulation targets — entity, direction, role (structured JSON) with optional quote evidence (`direction_quote`, `rolle_quote`)
- [x] Roles KB — 10 roles in `roles.json`, lazy loading via `role_store.py` + `{{ROLES}}` placeholder in prompt, fuzzy normalisation
- [x] Techniques DB — 24 documented techniques with semantic normalisation
- [x] Political leaning with quote evidence — `pass2.md` returns a characteristic text quote per label; detail view shows quote below the label
- [x] Model metadata — `llm_provider` and `llm_model` stored with every analysis; LM Studio auto-detects the active model via `/api/v0/models`

### Database & RAG
- [x] ChromaDB local persistent (articles, orwell_anchors, techniques)
- [x] ChromaDB HTTP server integration — all repositories use `HttpClient` instead of `PersistentClient`. Central `chroma_client.py` reads `CHROMA_HOST` + `CHROMA_PORT` from ENV (default: `localhost:8001`). Enables network operation without code changes.
- [x] **Network operation / multi-device** — ChromaDB runs as HTTP server, `CHROMA_HOST`/`CHROMA_PORT` configurable via ENV. `/config` endpoint with feature flag `SUBMIT_ENABLED`. Frontend hides "Submit" depending on flag. Mac Mini = viewer mode.
- [x] RAG anchor corpus (anchor_store.py, lazy-loaded from 5 anchors)
- [x] Techniques collection with auto-seeding from technique_store.py

### Feed & Data Collection
- [x] RSS feed collector with dedup check against DB
- [x] Manual and automatic feed mode (FEED_MODE env)
- [x] Topic pre-filter (topic_filter.py, keyword-based, no LLM call)
- [x] FEED_TOPICS configurable via env variable (incl. `all` for no filter)

### Statistics
- [x] Statistics report (top techniques, Bernays, Orwell, DK, domains, sentiments)
- [x] Political leaning in stats.py
- [x] Topic-Bernays evaluation (thema_bernays)
- [x] Entity targeting evaluation (entity_targeting)

### Web UI
- [x] FastAPI backend with all REST endpoints
- [x] Angular 17+ frontend (standalone components, lazy loading)
- [x] Dashboard — KPI tiles, top techniques, top leanings, recent articles
- [x] Article list — filterable by domain, Orwell range, limit
- [x] Article detail — scores, framing, manipulation targets, techniques (linked)
- [x] Statistics page — sub-navigation (overview / timeline), domain table, top techniques, leanings
- [x] Statistics timeline — day-based line charts (Orwell, Bernays, DK) with domain filter and median/maximum toggle (Chart.js)
- [x] Paywall warning on manual submission — dedicated job status `paywall` with notice in UI
- [x] URL submission — form with job status polling
- [x] Techniques overview `/techniques` — grouped by category
- [x] Technique detail `/techniques/:id` — individual URL per technique (linkable)
- [x] "About this project" `/knowledge` — methodology, indicators, sources

### Documentation & Validation
- [x] First concept test with calibration results (docs/concept/base-tests.md)
- [x] Bias validation: symmetry tests with group substitution (docs/concept/bias-validation/)
- [x] Architecture documentation (docs/analyse_architektur.md)
- [x] Orwell Index refactoring documented as consequence of symmetry tests

---

## Open

### Evaluation & Visualisation
- [ ] **entity_targeting and thema_bernays in /stats API** — expose endpoint and visualise in frontend
- [ ] **Source comparison** — interactive bar chart domain × Orwell Index (Chart.js)
- [x] **Timeline** — score development per source/topic over time (line chart)
- [ ] **Technique heatmap** — domain × technique as matrix in the stats view
- [ ] **Direction/role correlation** — empirical analysis: hypothesis "passivity = positive" (positive manipulation targets almost always victims, no acting positive agent)

### Frontend
- [ ] **Pagination** — switch article list and backend endpoint to cursor- or offset-based pagination (relevant from ~500 articles)

### Data Collection
- [ ] **Feed health check** — check on startup whether all feed URLs are reachable, report dead feeds
- [ ] **MSN feed** — test MSN Germany as a central aggregator
- [ ] **English feeds** — BBC, Reuters, AP, The Guardian as counter-sources to German outlets. Add language detection to scraper (langdetect etc.), keyword lists for English.
- [ ] **Russian counter-sources** — TASS English, RIA Novosti English as a methodological mirror. Not as a truth source, but for discrepancy detection: same event, different framing.

### Cross-Source Verification
- [ ] **Event clustering** — group semantically similar articles about the same incident in ChromaDB (query on anonymised text, time window ±24h). Foundation for source comparison.
- [ ] **Discrepancy detector** — for clustered articles: compare Orwell Index, techniques and manipulation targets. Flag large deviations between sources as a warning signal.
- [ ] **Strategic omission** — detect when an event is reported in German sources but important context is missing that is present in English/non-western sources.
- [ ] **Agency bias detection** — when all German outlets use the same wording (high semantic similarity), mark as "wire report without original research". Consensus ≠ truth.

### Quality & Tests
- [ ] **Extend symmetry tests** — additional substitution pairs (migrants/natives, left/right)
- [x] **Pass 0 — dynamic group identification** — implemented: LLM pass before anonymisation identifies group markers (`[{"term": "...", "type": "racial|ethnic_origin|..."}]`). Code replaces deterministically with `Gruppe-A` etc. Validated by test 04 (symmetry Black/White, Δ Orwell 0.01, Δ Bernays 0.00).
- [ ] **Anonymise ambiguous racial attributes** — `schwarz` and `weiß` as racial attributes are dynamically detected and replaced by pass 0. Static list remains as fallback for clear cases. Residual problem: pass 0 might incorrectly classify colour adjectives as racial attributes — validation pending.
- [ ] **Keyword lists** — adversarial framing filter (mark keywords in quotation marks as "cited")
- [ ] **Keyword lazy update** — SQLite DB stores keyword hits with context sentence; periodic job classifies affirmative vs. citing and writes corrections back to keyword lists
- [ ] **Manually curated anchor corpus** — initial curation with verified reference articles for better cold-start calibration
- [ ] **Unit tests** — populate tests/: scraper mocks, JSON parser, adapter interface
- [ ] **Analysis validation** — verify that returned quote fields are actually present in the article text

### Language Models & Local Models
- [ ] **Adapt local models for language specialisation**
  - [x] Externalise model names from code (`SPACY_MODEL`, `EMBEDDING_MODEL`) — previously hardcoded in `anonymizer.py` and all three ChromaDB repositories; load from ENV on startup; add defaults + descriptions to `.env.example`
  - [x] Select appropriate German-language models as new defaults — `de_core_news_md` (spaCy, unchanged), `paraphrase-multilingual-MiniLM-L12-v2` (embeddings, replaces `all-MiniLM-L6-v2`)

### LLM Operation
- [ ] **Hybrid provider** — after pass 1: if `orwell_index > threshold` or domain in priority list → deep cloud provider (`LLM_PROVIDER_DEEP`), otherwise local model (`LLM_PROVIDER`). Configurable via `DEEP_ANALYSIS_THRESHOLD` in `.env`. Pending Apple Silicon hardware for local LLM operation.
- [ ] **MCP server** — local MCP server as bridge between Claude Desktop (cloud scheduling) and local backend. Tools: `trigger_feed()`, `get_stats()`. Enables remote triggering without a publicly accessible backend.

### Open Source / Internationalisation
- [ ] **UI multilingual (DE/EN)** — integrate Angular i18n or ngx-translate; externalise all UI texts into language files; language switcher in UI (DE/EN toggle)
- [ ] **Frontend UI texts** — translate all German labels, error messages and captions to English (prerequisite for multilingual support)
- [ ] **spaCy language detection** — `langdetect` for automatic language detection; load `de_core_news_md` vs. `en_core_web_md` dynamically
- [ ] **English keyword lists** — curate English equivalents for `keywords_extreme_left.txt`, `keywords_extreme_right.txt`, `keywords_general.txt`

### Documentation & Code Translation

**Markdown documentation:**
- [x] [README.md](../README.md) — project overview, architecture, installation, configuration
- [x] [SETUP.md](../SETUP.md) — setup guide, common errors
- [x] [docs/reference.md](reference.md) — technical reference: JSON schema, indicators, paywall, techniques DB
- [x] [docs/web_architecture.md](web_architecture.md) — stack, project structure, API endpoints
- [x] [docs/analyse_architektur.md](analyse_architektur.md) — indicators, two-pass architecture (technically complex)
- [x] [docs/todo.md](todo.md) — roadmap

**Python comments & docstrings:**
- [ ] [src/news_analyser/anonymizer.py](../src/news_analyser/anonymizer.py)
- [ ] [src/news_analyser/feed.py](../src/news_analyser/feed.py)
- [ ] [src/news_analyser/main.py](../src/news_analyser/main.py)
- [ ] [src/llm_adapter/cli_adapter.py](../src/llm_adapter/cli_adapter.py)
- [ ] [src/news_analyser/agents/analyzer.py](../src/news_analyser/agents/analyzer.py)
- [ ] [src/news_analyser/repositories/anchor_store.py](../src/news_analyser/repositories/anchor_store.py)
- [ ] [src/news_analyser/repositories/role_store.py](../src/news_analyser/repositories/role_store.py)
- [ ] [backend/main.py](../backend/main.py)
- [ ] [backend/routers/analyse.py](../backend/routers/analyse.py)

**TypeScript comments:**
- [ ] [frontend/src/app/features/stats/stats-verlauf.component.ts](../frontend/src/app/features/stats/stats-verlauf.component.ts)

### Export & Integration
- [ ] **CSV/JSON export** — export all stored analyses
- [ ] **Authentication** — optional API key protection for the analysis endpoint
- [ ] **Logging** — structured logging to logs/ instead of print() statements
