# News Analyser

Analysiert Nachrichtenartikel auf Manipulationstechniken, rhetorischen Extremismus und politisches Framing — lokal, ohne Cloud-Abhängigkeit.

**Indikatoren:** Orwell-Index (Extremismus), Bernays-Score (Manipulationsintensität), Dunning-Kruger-Index (unbelegte Gewissheit), politische Strömung, Manipulation Targets, 19 dokumentierte Techniken.

---

## Voraussetzungen

- Python 3.11+
- Node.js 18+ (nur für das Frontend)
- Zugang zu einem LLM-Backend (OpenAI, Anthropic, LM Studio, Claude CLI o.ä.)

---

## Installation

### 1. Repository klonen

```bash
git clone <repo-url>
cd news_analyser
```

### 2. Virtuelle Umgebung erstellen

```bash
python -m venv .venv
source .venv/bin/activate      # Linux/macOS
.venv\Scripts\activate         # Windows
```

### 3. Abhängigkeiten installieren

```bash
# Analyse-Pipeline
pip install -r requirements.txt

# Backend (FastAPI)
pip install -r requirements-api.txt

# Deutsches spaCy-Sprachmodell (Anonymisierung)
python -m spacy download de_core_news_md
```

### 4. Umgebungsvariablen konfigurieren

```bash
cp .env.example .env
# .env mit einem Editor öffnen und API-Key eintragen
```

Mindestens `LLM_PROVIDER` und den passenden API-Key setzen — siehe `.env.example` für alle Optionen.

### 5. Frontend (optional)

```bash
cd frontend
npm install
```

---

## Starten

### Backend (Port 8000)

```bash
cd backend
uvicorn main:app --reload
```

### Frontend (Port 4200)

```bash
cd frontend
ng serve
```

Die Web-UI ist dann unter [http://localhost:4200](http://localhost:4200) erreichbar.  
Die API-Docs unter [http://localhost:8000/docs](http://localhost:8000/docs).

### Watcher (RSS-Feed-Dauerbetrieb)

```bash
# Einmaliger Lauf
python run.py --feed

# Dauerbetrieb (Intervall aus .env: FEED_INTERVAL)
python run.py --feed --auto

# Einzelnen Artikel analysieren
python run.py --url https://www.spiegel.de/...
```

---

## LLM-Backends

Über `LLM_PROVIDER` in der `.env` wird das Backend gewählt:

| Provider | Env-Variable | Beschreibung |
|---|---|---|
| `openai` | `OPENAI_API_KEY` | OpenAI API (Standard) |
| `anthropic` | `ANTHROPIC_API_KEY` | Anthropic API |
| `cli` | — | Claude Code CLI (lokal, kein API-Key) |
| `lm_studio` | — | LM Studio lokaler Server |
| `copilot` | `GITHUB_TOKEN` | GitHub Copilot |
| `m365_copilot` | `M365_COPILOT_ACCESS_TOKEN` | Microsoft 365 Copilot |

---

## Projektstruktur

```
news_analyser/
├── src/news_analyser/       Analyse-Pipeline (Python-Paket)
│   ├── agents/              LLM-Analyse (Zwei-Pass-Architektur)
│   ├── repositories/        ChromaDB-Zugriff (Artikel, Anker, Techniken)
│   ├── prompts/             Editierbare System-Prompts (Markdown)
│   └── data/                Keyword-Listen, Techniken-JSON, Feeds
├── src/llm_connectors/      LLM-Backend-Abstraktionsschicht
├── backend/                 FastAPI REST-API
│   └── routers/             Endpunkte: articles, analyse, stats, search, techniques
├── frontend/                Angular 17+ SPA
├── data/                    ChromaDB (lokal, persistent, nicht im Repo)
├── requirements.txt         Analyse-Pipeline-Dependencies
├── requirements-api.txt     Backend-Dependencies (FastAPI etc.)
└── .env.example             Konfigurationsvorlage
```

---

## Dokumentation

| Dokument | Inhalt |
|---|---|
| [docs/project.md](docs/project.md) | Konfigurationsreferenz, JSON-Schema, Indikatoren, Paywall-Erkennung |
| [docs/analyse_architektur.md](docs/analyse_architektur.md) | Indikatoren, Zwei-Pass-Architektur, Bias-Mitigierung |
| [docs/web_architecture.md](docs/web_architecture.md) | API-Endpunkte, Frontend-Struktur |
| [docs/todo.md](docs/todo.md) | Offene Features und Erweiterungsideen |
| [docs/konzept/](docs/konzept/) | Kalibrierungstests und Bias-Validierung |
