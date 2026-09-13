# News Analyser

Analyses news articles for manipulation techniques, rhetorical extremism and political framing. The analysis pipeline and database run locally — for the LLM backend you can choose between a local model (LM Studio) or a cloud service (OpenAI, Anthropic, GitHub Copilot).

**Indicators:** Orwell Index (extremism), Bernays Score (manipulation intensity), Dunning-Kruger Index (unsubstantiated certainty), political leaning, manipulation targets, 28 documented techniques.

**License:** GNU Affero General Public License v3.0 — see [LICENSE](LICENSE)

---

## Requirements

- Python 3.10–3.12 (recommended: 3.12)
- Node.js 18+ (frontend only)
- Access to an LLM backend (OpenAI, Anthropic, LM Studio, Claude CLI etc.)

For installation and first-time setup, see **[docs/environments/local.md](docs/environments/local.md)**.

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

For manual startup (separate terminals) and troubleshooting, see **[docs/environments/local.md](docs/environments/local.md)**.

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

With `LLM_PROVIDER=gemini`, an exhausted Gemini quota pauses feed processing for
24 hours. The cooldown is retained across feed-process restarts in `data/`.

---

## LLM Backends

The backend is selected via `LLM_PROVIDER` in `.env`:

| Provider | Env variable | Description |
|---|---|---|
| `openai` | `OPENAI_API_KEY` | OpenAI API (default) |
| `anthropic` | `ANTHROPIC_API_KEY` | Anthropic API |
| `cli` | — | Claude Code CLI (no API key required) |
| `lm_studio` | — | LM Studio local server |
| `gemini` | `OPENAI_API_KEY` | Google AI Studio via Gemini's OpenAI-compatible endpoint |
| `copilot` | `GITHUB_TOKEN` | GitHub Copilot |
| `m365_copilot` | `M365_COPILOT_ACCESS_TOKEN` | Microsoft 365 Copilot |

Setup instructions for each provider (API keys, CLI login, LM Studio, Ollama) are in **[docs/environments/local.md](docs/environments/local.md)**.

---

## Project Structure

```
news_analyser/
├── src/news_analyser/       Analysis pipeline (Python package)
│   ├── agents/              LLM analysis (Pass 0 preparation + two analysis passes)
│   ├── repositories/        ChromaDB access (articles, anchors, techniques)
│   ├── prompts/             Editable system prompts (Markdown)
│   └── data/                Keyword lists, techniques JSON, feeds
├── src/llm_adapter/         LLM backend abstraction layer
├── backend/                 FastAPI REST API
│   ├── routers/             Endpoints: articles, analyse, stats, search, techniques, status
│   └── schemas/             Pydantic request/response models
├── frontend/                Angular SPA
├── docs/                    Full documentation (see docs/index.md)
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

Full documentation lives in [`docs/`](docs/index.md), organised by category
(reference, environments, concepts & decisions, planning, archive) — see
**[docs/index.md](docs/index.md)** for the complete index.
