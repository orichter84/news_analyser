# News Analyser

Analysiert Nachrichtenartikel auf Manipulationstechniken, rhetorischen Extremismus und politisches Framing. Die Analyse-Pipeline und Datenbank laufen lokal — für das LLM-Backend kann wahlweise ein lokales Modell (LM Studio) oder ein Cloud-Dienst (OpenAI, Anthropic, GitHub Copilot) verwendet werden.

**Indikatoren:** Orwell-Index (Extremismus), Bernays-Score (Manipulationsintensität), Dunning-Kruger-Index (unbelegte Gewissheit), politische Strömung, Manipulation Targets, 19 dokumentierte Techniken.

---

## Voraussetzungen

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (empfohlener Package Manager — `pip install uv`)
- Node.js 18+ (nur für das Frontend)
- Zugang zu einem LLM-Backend (OpenAI, Anthropic, LM Studio, Claude CLI o.ä.)

---

## Installation

### 1. Repository klonen

```bash
git clone <repo-url>
cd news_analyser
```

### 2. Virtuelle Umgebung + Abhängigkeiten installieren

**Option A — mit uv (empfohlen):**

```bash
uv venv
source .venv/bin/activate      # Linux/macOS
.venv\Scripts\activate         # Windows
uv pip install -r requirements.txt -r requirements-api.txt
python -m spacy download de_core_news_md
```

**Option B — ohne uv (klassisch):**

```bash
python -m venv .venv
source .venv/bin/activate      # Linux/macOS
.venv\Scripts\activate         # Windows
pip install -r requirements.txt -r requirements-api.txt
python -m spacy download de_core_news_md
```

> Beide Optionen erzeugen eine `.venv/`-Umgebung — eine davon reicht, nicht beide.

### 4. Umgebungsvariablen konfigurieren

```bash
cp .env.example .env
# .env mit einem Editor öffnen und API-Key eintragen
```

Mindestens `LLM_PROVIDER` setzen. Je nach Provider wird zusätzlich ein API-Key benötigt — `cli` und `lm_studio` funktionieren ohne. Alle Optionen sind in `.env.example` dokumentiert.

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
