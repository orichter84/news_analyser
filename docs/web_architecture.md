# Web-Architektur — Konzept

Erweiterung des news_analyser von einem lokalen CLI-Werkzeug zu einer Web-Applikation mit Analyse-Datenbank, Dashboard und Knowledge Base.

---

## Übersicht

```
Browser
   ↕  HTTP
FastAPI (Backend)
   ├── /api/*        REST-Endpunkte
   ├── /app/*        HTMX-gerenderte Seiten
   └── /static/*     CSS, JS
        ↕
   ChromaDB          (bestehend, unverändert)
   news_analyser     (bestehend: scraper, analyzer, feed)
```

---

## Stack

### Empfehlung: FastAPI + HTMX (MVP)

| Komponente | Technologie | Begründung |
|---|---|---|
| Backend | FastAPI | Async, automatische OpenAPI-Docs, passt zu Python-Codebase |
| Templating | Jinja2 | In FastAPI eingebaut, kein JS-Build-Step |
| Interaktivität | HTMX | Partielle Seitenaktualisierungen ohne React/Vue |
| Charts | Chart.js (CDN) | Leichtgewichtig, via HTMX nachladen |
| CSS | Tailwind CSS (CDN) | Kein Build-Step nötig |

**Vorteil**: Kein JavaScript-Framework, kein npm, kein Build-Pipeline. Schnell produktionsfähig.

### Alternative: FastAPI + React (wenn nötig)
Sinnvoll wenn das Dashboard sehr interaktiv wird (Drag & Drop, Echtzeit-Updates, komplexe Filter). Höherer Initialaufwand.

---

## Projektstruktur (Erweiterung)

```
news_analyser/
├── src/news_analyser/
│   ├── (bestehend)
│   └── api/                    NEU
│       ├── __init__.py
│       ├── main.py             FastAPI App + Router-Registrierung
│       ├── routers/
│       │   ├── articles.py     GET /articles, GET /articles/{id}
│       │   ├── analyse.py      POST /analyse
│       │   ├── stats.py        GET /stats
│       │   └── search.py       GET /search
│       ├── templates/          Jinja2 HTML-Templates
│       │   ├── base.html
│       │   ├── dashboard.html
│       │   ├── article.html
│       │   ├── compare.html
│       │   └── knowledge/
│       │       ├── index.html
│       │       ├── techniques.html
│       │       └── methodology.html
│       └── static/
│           └── css/
│               └── custom.css
└── run_web.py                  NEU — Web-Server Einstiegspunkt
```

---

## API-Endpunkte

### Artikel

```
GET  /api/articles
     ?domain=spiegel.de
     &score_min=-1.0&score_max=1.0
     &technique=FUD
     &from=2026-01-01&to=2026-12-31
     &limit=20&offset=0

GET  /api/articles/{url_encoded_id}

POST /api/analyse
     Body: { "url": "https://..." }
     Response: Analyse-JSON oder Job-ID (async)
```

### Statistiken

```
GET  /api/stats
     ?domain=spiegel.de   (optional, sonst alle)

     Response:
     {
       "total_articles": 342,
       "domains": [{ "domain": "spiegel.de", "count": 45, "bernays_avg": -0.52 }],
       "top_techniques": [{ "technique": "Framing", "count": 187 }],
       "bernays_distribution": { "left": 201, "neutral": 89, "right": 52 }
     }
```

### Suche

```
GET  /api/search?q=NATO+Trump&limit=10
     Semantische Suche via ChromaDB query_similar()
```

---

## Seiten (HTMX)

### Dashboard `/`
- Kennzahlen: Gesamt-Artikel, analysierte Domains, Durchschnitt Orwell-Index
- Letzte Analysen (Tabelle, sortierbar)
- Bernays-Score-Verteilung (Histogramm, Chart.js)
- Top-5-Techniken (Balkendiagramm)

### Quellenvergleich `/compare`
- Domains nebeneinander: Durchschnitt-Score, häufigste Techniken, Artikel-Anzahl
- Heatmap: Domain × Technik

### Artikel-Detail `/article/{id}`
- Vollständiger Analyse-Output
- Textzitate hervorgehoben mit Technik-Label
- Orwell-Index visuell auf der Skala (−1 bis +1)

### URL-Einreichung `/submit`
- Formular: URL eingeben → Analyse starten → Ergebnis anzeigen
- Optionaler Status-Fortschrittsbalken via HTMX polling

### Knowledge Base `/knowledge`
- `/knowledge/techniques` — Alle Techniken mit Definition und Beispiel
- `/knowledge/methodology` — Wie funktioniert das System, Limitierungen
- `/knowledge/bernays` — Historischer Hintergrund

---

## Einstiegspunkt

```python
# run_web.py
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "src.news_analyser.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
```

```bash
python run_web.py
# → http://localhost:8000
```

---

## Neue Abhängigkeiten

```
fastapi>=0.111
uvicorn>=0.30
jinja2>=3.1
python-multipart>=0.0.9   # für Formular-Uploads
httpx>=0.27               # für async HTTP in Tests
```

---

## Migrations-Hinweis

Die bestehende ChromaDB bleibt **unverändert**. Die Web-API liest nur — Schreibzugriff läuft weiterhin über den CLI-Analyzer und den Feed-Collector. Kein Datenmigrations-Aufwand.
