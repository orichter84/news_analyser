# News Analyser

Analyses news articles for manipulation techniques, rhetorical extremism and political framing. The analysis pipeline and database run locally — for the LLM backend you can choose between a local model (LM Studio) or a cloud service (OpenAI, Anthropic, GitHub Copilot).

**Indicators:** Orwell Index (extremism), Bernays Score (manipulation intensity), Dunning-Kruger Index (unsubstantiated certainty), political leaning, manipulation targets, 23 documented techniques.

**License:** GNU Affero General Public License v3.0 — see [LICENSE](LICENSE)

---

## Requirements

- Python 3.10–3.12 (recommended: 3.12) — 3.13+ may have compatibility issues with ChromaDB and PyTorch
- [uv](https://github.com/astral-sh/uv) (recommended package manager — `pip install uv`)
- Node.js 18+ (frontend only)
- Access to an LLM backend (OpenAI, Anthropic, LM Studio, Claude CLI etc.)

---

## Installation

### 1. Clone the repository

```bash
git clone <repo-url>
cd news_analyser
```

### 2. Virtual environment & dependencies

**Option A — with uv (recommended):**

```bash
uv venv
source .venv/bin/activate      # Linux/macOS
.venv\Scripts\activate         # Windows
uv pip install -r requirements.txt -r requirements-api.txt
python -m spacy download de_core_news_md
```

**Option B — without uv (classic):**

```bash
python -m venv .venv
source .venv/bin/activate      # Linux/macOS
.venv\Scripts\activate         # Windows
pip install -r requirements.txt -r requirements-api.txt
python -m spacy download de_core_news_md
```

> Both options create a `.venv/` environment — use one, not both.

### 3. Configure environment variables

```bash
cp .env.example .env
# Open .env in an editor and fill in your values
```

At minimum set `LLM_PROVIDER`. Depending on the provider an API key may be required — `cli` and `lm_studio` work without one. All options are documented in `.env.example`.

### 4. Frontend (optional)

```bash
cd frontend
npm install
```

---

## Starting

### All-in-one (recommended)

**Linux/macOS:**
```bash
./start.sh
```

**Windows (PowerShell):**
```powershell
.\start.ps1
```

Starts ChromaDB, backend and frontend in the correct order. Stop all services with `Ctrl+C`.

| Service  | URL |
|----------|-----|
| Frontend | http://localhost:4200 |
| Backend  | http://localhost:8000 |
| ChromaDB | http://localhost:8001 |

### Manual startup (three terminals)

ChromaDB must be started first — the backend connects to it on startup.

**Terminal 1 — ChromaDB (Port 8001)**

```bash
# Linux/macOS
chroma run --host localhost --port 8001 --path data/chroma_db
```
```powershell
# Windows
.venv\Scripts\chroma.exe run --host localhost --port 8001 --path data\chroma_db
```

**Terminal 2 — Backend (Port 8000)**

```bash
# Linux/macOS
cd backend
uvicorn main:app --reload
```
```powershell
# Windows
cd backend
.venv\Scripts\uvicorn.exe main:app --reload
```

**Terminal 3 — Frontend (Port 4200)**

```bash
# Linux/macOS
cd frontend
ng serve
```
```powershell
# Windows
cd frontend
npx ng serve --port 4200
```

The web UI is available at [http://localhost:4200](http://localhost:4200).  
The API docs at [http://localhost:8000/docs](http://localhost:8000/docs).

### Watcher (RSS feed continuous mode)

```bash
# Single run
python run.py --feed

# Continuous mode (interval from .env: FEED_INTERVAL)
python run.py --feed --auto

# Analyse a single article
python run.py --url https://www.spiegel.de/...
```

---

## LLM Backends

The backend is selected via `LLM_PROVIDER` in `.env`:

| Provider | Env variable | Description |
|---|---|---|
| `openai` | `OPENAI_API_KEY` | OpenAI API (default) |
| `anthropic` | `ANTHROPIC_API_KEY` | Anthropic API |
| `cli` | — | Claude Code CLI (no API key required) |
| `lm_studio` | — | LM Studio local server |
| `copilot` | `GITHUB_TOKEN` | GitHub Copilot |
| `m365_copilot` | `M365_COPILOT_ACCESS_TOKEN` | Microsoft 365 Copilot |

### Claude Code CLI (`cli`)

The `cli` provider uses the locally installed [Claude Code CLI](https://claude.ai/code) as a subprocess — no separate API key needed, authentication is handled via CLI login.

**Installation (Node.js 18+ required):**

```bash
npm install -g @anthropic-ai/claude-code
```

**Login:**

```bash
claude login
```

A browser window opens for authentication with your Anthropic account. After login the CLI can be used directly.

**Configure `.env`:**

```env
LLM_PROVIDER=cli
```

### LM Studio (`lm_studio`)

[LM Studio](https://lmstudio.ai) enables running local language models without cloud connectivity — no API key required.

**Installation:**

1. Download and install LM Studio from [lmstudio.ai](https://lmstudio.ai)
2. In the **Discover** tab, download a model (recommended: Mistral 7B Q8 or Llama 3 8B Q8)
3. In the **Local Server** tab, load the model and start the server — runs on port 1234 by default

**Configure `.env`:**

```env
LLM_PROVIDER=lm_studio
```

The active model is set within LM Studio itself — `OPENAI_MODEL` has no effect. `OPENAI_BASE_URL` does not need to be set either; the connector automatically uses `http://localhost:1234/v1`.

> **Alternative: Ollama** — also works locally via the `openai` provider, as Ollama offers an OpenAI-compatible API:
> ```env
> LLM_PROVIDER=openai
> OPENAI_API_KEY=ollama
> OPENAI_BASE_URL=http://localhost:11434/v1
> OPENAI_MODEL=llama3.2
> ```
> Download the model first: `ollama pull llama3.2`

---

## Project Structure

```
news_analyser/
├── src/news_analyser/       Analysis pipeline (Python package)
│   ├── agents/              LLM analysis (two-pass architecture)
│   ├── repositories/        ChromaDB access (articles, anchors, techniques)
│   ├── prompts/             Editable system prompts (Markdown)
│   └── data/                Keyword lists, techniques JSON, feeds
├── src/llm_adapter/         LLM backend abstraction layer
├── backend/                 FastAPI REST API
│   ├── routers/             Endpoints: articles, analyse, stats, search, techniques
│   └── schemas/             Pydantic request/response models
├── frontend/                Angular 17+ SPA
├── docs/                    Architecture documentation and concept tests
├── data/                    ChromaDB (local, persistent, not in repo)
├── config/                  User configuration (committed, no secrets)
│   ├── feeds.txt            RSS feed URLs (one per line, # for comments)
│   └── rerun_urls.txt       URLs for manual re-analysis (--file)
├── run.py                   CLI entry point (--url, --feed, --stats, --file)
├── start.sh                 Start all services — Linux/macOS
├── start.ps1                Start all services — Windows (PowerShell)
├── requirements.txt         Analysis pipeline dependencies
├── requirements-api.txt     Backend dependencies (FastAPI etc.)
└── .env.example             Configuration template (secrets + provider selection)
```

---

## Documentation

| Document | Contents |
|---|---|
| [docs/reference.md](docs/reference.md) | Technical reference: JSON output schema, indicators, paywall detection, techniques database |
| [docs/analyse_architektur.md](docs/analyse_architektur.md) | Indicators, two-pass architecture, bias mitigation |
| [docs/web_architecture.md](docs/web_architecture.md) | API endpoints, frontend structure |
| [docs/todo.md](docs/todo.md) | Open features and extension ideas |
| [docs/concept/](docs/concept/) | Calibration tests and bias validation |
