# Web Architecture

FastAPI REST backend + Angular single-page application. Both layers are fully decoupled and communicate exclusively via HTTP/JSON.

For the JSON output schema see [reference.md](reference.md).

---

## Overview

```
Browser (Angular SPA, port 4200)
   ↕  HTTP/JSON
FastAPI Backend (port 8000)
   ├── /articles        Article list and detail view
   ├── /analyse         Submit article + job status
   ├── /stats           Aggregated statistics, trends, publisher profiles
   ├── /search          Semantic search
   ├── /techniques      Manipulation techniques database
   ├── /status          Backend/ChromaDB/feed health + log tailing
   ├── /health          Liveness probe
   └── /config          Frontend feature flags (e.g. submit_enabled)
        ↕
   ChromaDB (local, persistent)
   ├── articles         Analysed articles
   ├── orwell_anchors   RAG calibration anchors
   └── techniques       Documented manipulation techniques
```

---

## Stack

| Layer | Technology | Rationale |
|---|---|---|
| Backend | FastAPI + uvicorn | Async, automatic OpenAPI docs, fits the Python codebase |
| Frontend | Angular (Standalone Components) | Lazy loading, signal-based state management |
| HTTP client | Angular HttpClient + fetch | Modern browser-native transport |
| Styling | SCSS (dark theme) | No CSS framework, full control |
| Routing | Angular Router (lazy-loaded) | Code splitting per feature module |

---

## Project Structure

```
news_analyser/
├── backend/
│   ├── main.py                     FastAPI app, CORS, router registration, /health, /config
│   └── routers/
│       ├── articles.py             GET /articles, GET /articles/{id}
│       ├── analyse.py              POST /analyse, GET /analyse/job/{id}
│       ├── stats.py                GET /stats, /stats/trends, /stats/publisher, /stats/verlauf
│       ├── search.py               GET /search
│       ├── techniques.py           GET /techniques, GET /techniques/{id}
│       └── status.py               GET /status, GET /status/logs/{name}
│
└── frontend/src/app/
    ├── app.routes.ts               Lazy-loaded top-level routes
    ├── app.html                    Navigation + router outlet
    ├── app.config.ts               provideRouter, provideHttpClient
    │
    ├── core/
    │   ├── models/
    │   │   ├── article.model.ts    ArticleListItem, ArticleDetail, ManipulationTarget (incl. quotes)
    │   │   ├── stats.model.ts      StatsResponse, PublisherProfile, TrendResponse, VerlaufEntry
    │   │   ├── analyse.model.ts    AnalyseRequest, AnalyseResponse, JobStatus
    │   │   ├── technique.model.ts  Technique
    │   │   └── status.model.ts     SystemStatus, LogName, LogResponse
    │   └── services/
    │       └── api.service.ts      All HTTP calls (HttpClient)
    │
    └── features/
        ├── dashboard/              KPI cards, top techniques, recent articles
        ├── articles/               Article list (filter) + detail view
        ├── stats/                  uebersicht, verlauf, herausgeber, trends (4 sub-pages)
        ├── submit/                 Submit URL + job status polling
        ├── knowledge/              "About this project" (7 sub-pages, see below)
        ├── system/                 Live status dashboard (Backend/ChromaDB/Feed/Logs)
        └── techniques/             Single-technique detail page (linked from article detail)
```

The techniques *catalogue* is rendered inside `knowledge/knowledge-techniken.component.ts`, not under `features/techniques/`. `features/techniques/` only holds the single-item detail page (`/techniques/:id`), reached by clicking a technique name on the article detail page.

---

## API Endpoints

### Articles

```
GET  /articles
     ?domain=spiegel.de
     &orwell_min=0.0&orwell_max=1.0
     &limit=50

GET  /articles/{url_encoded_id}
     Response: Full analysis JSON incl. manipulation_targets
```

### Analysis

```
POST /analyse
     Body: { "url": "https://...", "force": false }
     Response: { "job_id": "...", "status": "accepted", "message": "..." }
     Existing URL (force=false): { "job_id": null, "status": "skipped", "message": "..." }

GET  /analyse/job/{job_id}
     Response: { "status": "pending|done|paywall|error", "message": "...", "result"?: {...} }
     A completed job includes the full analysis as `result`.
```

### Statistics

```
GET  /stats
     Response:
     {
       "total_articles": 342,
       "top_techniques": {...}, "top_domains": {...}, "top_stroemungen": {...},
       "orwell_distribution": {...}, "bernays_distribution": {...},
       "dk_distribution": {...} | null,
       "domain_averages": [{ "domain": "spiegel.de", "artikel": 45,
                              "orwell_avg": 0.35, "bernays_avg": 3.2, "dk_avg": 0.1 }],
       "sentiment_distribution": {...}
     }

GET  /stats/trends
     Response: { "trend_cards": [...], "topic_heatmap": {"weeks": [...], "rows": [...]},
                 "domain_comparison": [...], "weeks": [...] }
     Domain trend cards (14d vs. previous 14d), weekly topic×Orwell heatmap,
     weekly multi-domain Orwell-Index comparison.

GET  /stats/publisher
     Response: list of { "domain", "artikel", "stroemung": {label: count},
                          "abhaengigkeit": {dimension: {label, score, positiv, negativ, neutral, total}} }
     Political-leaning aggregation + geopolitical/party dependency scores per domain
     (see [publisher_profiling.md](publisher_profiling.md)).

GET  /stats/verlauf?domain=spiegel.de
     Response: list of daily aggregates (Orwell/Bernays median per day), optionally filtered by domain.
```

### Search

```
GET  /search?q=NATO+Trump&n=10
     Semantic search via ChromaDB query_similar()
```

### Techniques

```
GET  /techniques
     Response: List of all documented techniques (from ChromaDB techniques collection)

GET  /techniques/{id}
     Response: Single technique (e.g. /techniques/appeal-to-fear)
```

`GET /techniques/{id}` backs the `/techniques/:id` frontend detail page (`features/techniques/technique-detail.component.ts`).

### Status

```
GET  /status
     Response: { "backend": {"status": "ok"},
                  "chroma": {"status": "ok"|"error", "detail"?},
                  "feed": {"pid", "mode", "started_at", "last_run_at",
                           "last_run_status", "last_run_articles", "next_run_at", "running"} }

GET  /status/logs/{name}
     name ∈ app | chroma | backend | frontend
     Response: { "lines": [...] }  (tail of the log file, max 300 lines)
```

### Health & Config

```
GET  /health   → { "status": "ok" }
GET  /config   → { "submit_enabled": true|false }   (reads SUBMIT_ENABLED env var)
```

---

## Frontend Pages

### Dashboard `/dashboard`
- KPI cards: total articles, analysed domains, average Orwell Index and Bernays Score
- Top 5 techniques and top 5 political leanings
- Recent articles (table)

### Article List `/articles`
- Filterable by domain, Orwell min/max, limit
- Columns: title, domain, date, Orwell Index, Bernays Score, techniques

### Article Detail `/articles/{encoded_url}`
- Score cards: Orwell Index, Bernays Score, DK Index
- Framing: narrative, sentiment, political leaning, topic area
- Manipulation targets: entity, direction (▲ positive / ▼ negative / ● neutral), role — with optional quote evidence for direction and role
- Detected techniques with quote and explanation — technique names link to `/techniques/:id`

### Statistics `/stats`
Four sub-pages under a shared layout:
- `/stats/uebersicht` — domain table with average scores, top techniques and political leanings
- `/stats/verlauf` — daily Orwell/Bernays trend, optionally filtered by domain
- `/stats/herausgeber` — publisher profiles (political leaning + dependency scores), see [publisher_profiling.md](publisher_profiling.md)
- `/stats/trends` — 14-day trend cards, topic×week heatmap, multi-domain comparison

### Submit `/submit`
- URL form → POST /analyse → job status polling → link to result
- Hidden/disabled when `GET /config` returns `submit_enabled: false`

### About `/knowledge`
Seven sub-pages (default redirect: `problem`) — background, approach, pipeline, indicators, limitations, techniques catalogue, sources. See the in-app pages themselves for content; there is no separate `/techniques` overview page — the catalogue lives at `/knowledge/techniken`, fetched live from `GET /techniques`.

### System Status `/system`
- Live view of backend/ChromaDB/feed-grabber health (`GET /status`) and tailed log files (`GET /status/logs/{name}`) for `app`, `chroma`, `backend`, `frontend`.

### Technique Detail `/techniques/{id}`
- Single-technique view (name, category, description, example, Wikipedia source link) — reached by clicking a technique name on the article detail page
- Not linked from navigation or the `/knowledge/techniken` catalogue; it only exists as a link target

---

## CORS Configuration

```python
app.add_middleware(
     CORSMiddleware,
     allow_origin_regex=r"https?://(localhost|[\d]{1,3}\.[\d]{1,3}\.[\d]{1,3}\.[\d]{1,3}|[a-z0-9_.-]+)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```
