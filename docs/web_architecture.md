# Web Architecture

FastAPI REST backend + Angular 17+ single-page application. Both layers are fully decoupled and communicate exclusively via HTTP/JSON.

For the JSON output schema see [reference.md](reference.md).

---

## Overview

```
Browser (Angular SPA, port 4200)
   ↕  HTTP/JSON
FastAPI Backend (port 8000)
   ├── /articles        Article list and detail view
   ├── /analyse         Submit article + job status
   ├── /stats           Aggregated statistics
   ├── /search          Semantic search
   └── /techniques      Manipulation techniques database
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
| Frontend | Angular 17+ (Standalone Components) | Lazy loading, signal-based state management |
| HTTP client | Angular HttpClient + fetch | Modern browser-native transport |
| Styling | SCSS (dark theme) | No CSS framework, full control |
| Routing | Angular Router (lazy-loaded) | Code splitting per feature module |

---

## Project Structure

```
news_analyser/
├── backend/
│   ├── main.py                     FastAPI app, CORS, router registration
│   └── routers/
│       ├── articles.py             GET /articles, GET /articles/{id}
│       ├── analyse.py              POST /analyse, GET /analyse/job/{id}
│       ├── stats.py                GET /stats
│       ├── search.py               GET /search
│       └── techniques.py           GET /techniques, GET /techniques/{id}
│
└── frontend/src/app/
    ├── app.routes.ts               Lazy-loaded top-level routes
    ├── app.html                    Navigation + router outlet
    ├── app.config.ts               provideRouter, provideHttpClient
    │
    ├── core/
    │   ├── models/
    │   │   ├── article.model.ts    ArticleListItem, ArticleDetail, ManipulationTarget (incl. quotes)
    │   │   ├── stats.model.ts      StatsResponse, DomainAverage
    │   │   ├── analyse.model.ts    AnalyseRequest, JobStatus
    │   │   └── technique.model.ts  Technique
    │   └── services/
    │       └── api.service.ts      All HTTP calls (HttpClient)
    │
    └── features/
        ├── dashboard/              KPI cards, top techniques, recent articles
        ├── articles/               Article list (filter) + detail view
        ├── stats/                  Statistics tables and charts
        ├── submit/                 Submit URL + job status polling
        ├── techniques/             Techniques overview + detail page
        └── knowledge/              "About this project" (methodology, indicators, sources)
```

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
     Body: { "url": "https://..." }
     Response: { "job_id": "...", "status": "queued" }

GET  /analyse/job/{job_id}
     Response: { "status": "done|running|error", "result_id": "..." }
```

### Statistics

```
GET  /stats
     Response:
     {
       "total_articles": 342,
       "domains": [{ "domain": "spiegel.de", "count": 45, "bernays_avg": 3.2,
                     "orwell_avg": 0.35 }],
       "top_techniques": [{ "technique": "Framing", "count": 187 }],
       "top_stroemungen": [{ "label": "konservativ", "count": 94 }]
     }
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
- Domain table with average scores
- Top techniques and political leanings

### Submit `/submit`
- URL form → POST /analyse → job status polling → link to result

### Techniques `/techniques`
- Overview of all 19 documented techniques, grouped by category
- Detail page `/techniques/:id` — individual URL per technique (linkable, for educational use)

### About `/knowledge`
- Background, approach, pipeline, indicators, limitations, sources

---

## CORS Configuration

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```
