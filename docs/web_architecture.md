# Web-Architektur

FastAPI REST-Backend + Angular 17+ Single-Page-Application. Beide Schichten sind
vollständig getrennt und kommunizieren ausschließlich über HTTP/JSON.

---

## Übersicht

```
Browser (Angular SPA, Port 4200)
   ↕  HTTP/JSON
FastAPI Backend (Port 8000)
   ├── /articles        Artikel-Liste und Detailansicht
   ├── /analyse         Artikel einreichen + Job-Status
   ├── /stats           Aggregierte Statistiken
   ├── /search          Semantische Suche
   └── /techniques      Manipulationstechniken-Datenbank
        ↕
   ChromaDB (lokal, persistent)
   ├── articles         Analysierte Artikel
   ├── orwell_anchors   RAG-Kalibrierungsanker
   └── techniques       Dokumentierte Manipulationstechniken
```

---

## Stack

| Schicht | Technologie | Begründung |
|---|---|---|
| Backend | FastAPI + uvicorn | Async, automatische OpenAPI-Docs, passt zur Python-Codebase |
| Frontend | Angular 17+ (Standalone Components) | Lazy Loading, Signal-basiertes State Management |
| HTTP-Client | Angular HttpClient + fetch | Moderner Browser-nativer Transport |
| Styling | SCSS (Dark Theme) | Kein CSS-Framework, volle Kontrolle |
| Routing | Angular Router (lazy-loaded) | Code Splitting pro Feature-Modul |

---

## Projektstruktur

```
news_analyser/
├── backend/
│   ├── main.py                     FastAPI App, CORS, Router-Registrierung
│   └── routers/
│       ├── articles.py             GET /articles, GET /articles/{id}
│       ├── analyse.py              POST /analyse, GET /analyse/job/{id}
│       ├── stats.py                GET /stats
│       ├── search.py               GET /search
│       └── techniques.py           GET /techniques, GET /techniques/{id}
│
└── frontend/src/app/
    ├── app.routes.ts               Lazy-loaded Top-Level-Routen
    ├── app.html                    Navigation + Router Outlet
    ├── app.config.ts               provideRouter, provideHttpClient
    │
    ├── core/
    │   ├── models/
    │   │   ├── article.model.ts    ArticleListItem, ArticleDetail, ManipulationTarget
    │   │   ├── stats.model.ts      StatsResponse, DomainAverage
    │   │   ├── analyse.model.ts    AnalyseRequest, JobStatus
    │   │   └── technique.model.ts  Technique
    │   └── services/
    │       └── api.service.ts      Alle HTTP-Calls (HttpClient)
    │
    └── features/
        ├── dashboard/              KPI-Karten, Top-Techniken, letzte Artikel
        ├── articles/               Artikel-Liste (Filter) + Detailansicht
        ├── stats/                  Statistik-Tabellen und Auswertungen
        ├── submit/                 URL einreichen + Job-Status-Polling
        ├── techniques/             Techniken-Übersicht + Detailseite
        └── knowledge/              "Über dieses Projekt" (Methodik, Indikatoren, Quellen)
```

---

## API-Endpunkte

### Artikel

```
GET  /articles
     ?domain=spiegel.de
     &orwell_min=0.0&orwell_max=1.0
     &limit=50

GET  /articles/{url_encoded_id}
     Response: Vollständiges Analyse-JSON inkl. manipulation_targets
```

### Analyse

```
POST /analyse
     Body: { "url": "https://..." }
     Response: { "job_id": "...", "status": "queued" }

GET  /analyse/job/{job_id}
     Response: { "status": "done|running|error", "result_id": "..." }
```

### Statistiken

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

### Suche

```
GET  /search?q=NATO+Trump&n=10
     Semantische Suche via ChromaDB query_similar()
```

### Techniken

```
GET  /techniques
     Response: Liste aller dokumentierten Techniken (aus ChromaDB techniques-Collection)

GET  /techniques/{id}
     Response: Einzelne Technik (z.B. /techniques/appeal-to-fear)
```

---

## Frontend-Seiten

### Dashboard `/dashboard`
- KPI-Karten: Gesamt-Artikel, analysierte Domains, Durchschnitt Orwell-Index und Bernays-Score
- Top-5-Techniken und Top-5-Strömungen
- Letzte Artikel (Tabelle)

### Artikel-Liste `/articles`
- Filterbar nach Domain, Orwell-Min/Max, Limit
- Spalten: Titel, Domain, Datum, Orwell-Index, Bernays-Score, Techniken

### Artikel-Detail `/articles/{encoded_url}`
- Score-Karten: Orwell-Index, Bernays-Score, DK-Index
- Framing: Narrativ, Sentiment, Politische Strömung, Themenbereich
- Manipulation Targets: Entität, Richtung (▲ positiv / ▼ negativ / ● neutral), Rolle
- Erkannte Techniken mit Zitat und Erklärung — Technik-Namen verlinken auf `/techniques/:id`

### Statistiken `/stats`
- Domain-Tabelle mit Durchschnittswerten
- Top-Techniken und Strömungen

### Einreichen `/submit`
- URL-Formular → POST /analyse → Job-Status-Polling → Link zum Ergebnis

### Techniken `/techniques`
- Übersicht aller 19 dokumentierten Techniken, gruppiert nach Kategorie
- Detailseite `/techniques/:id` — eigene URL pro Technik (verlinkbar, für Lehrzwecke)

### Über dieses Projekt `/knowledge`
- Ausgangssituation, Lösungsansatz, Pipeline, Indikatoren, Limitierungen, Quellen

---

## CORS-Konfiguration

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Starten

```bash
# Backend (Port 8000)
cd backend
uvicorn main:app --reload

# Frontend (Port 4200)
cd frontend
ng serve
```
