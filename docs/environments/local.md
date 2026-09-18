# Setup Guide

## Requirements

- **Python 3.10–3.12** (recommended: 3.12) — Python 3.9 is not supported; 3.13+ may cause compatibility issues with ChromaDB
- **Node.js ≥ 18** — for Angular frontend and Claude Code CLI

## 1. Clone the repository

```bash
git clone https://github.com/orichter84/news_analyser.git
cd news_analyser
```

## 2. Set up Python environment

```bash
python3.12 -m venv .venv
source .venv/bin/activate      # Linux/macOS
.venv\Scripts\activate         # Windows
pip install -r requirements.txt -r requirements-api.txt
python -m spacy download de_core_news_md
```

## 3. Install frontend dependencies

```bash
cd frontend
npm install
cd ..
```

## 4. Create configuration

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

The most important setting is `LLM_PROVIDER`. Choose one of the options below:

### Option A: Claude Code CLI (recommended, no API key required)

Prerequisite: Claude Code CLI must be installed and logged in.

Installation (Node.js ≥ 18 required):
```bash
npm install -g @anthropic-ai/claude-code
```

Login once (opens a browser for OAuth authentication):
```bash
claude
```

Verify everything works:
```bash
claude --version
```

Then set in `.env`:
```
LLM_PROVIDER=cli
```

Default model is `claude-opus-4-5`, fixed as a project default in
`src/news_analyser/__init__.py`; override with `CLAUDE_CLI_MODEL` if needed
(provider-specific — doesn't affect other providers).

### Option B: Anthropic API

```
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_MODEL=claude-sonnet-4-6
```

### Option C: OpenAI

```
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o
```

### Option D: Local model via LM Studio

```
LLM_PROVIDER=lm_studio
OPENAI_MODEL=<model-name-in-lm-studio>
```

LM Studio must be running at `http://localhost:1234`.

> **Alternative: Ollama** — also works locally via the `openai` provider, as Ollama offers an OpenAI-compatible API:
> ```env
> LLM_PROVIDER=openai
> OPENAI_API_KEY=ollama
> OPENAI_BASE_URL=http://localhost:11434/v1
> OPENAI_MODEL=llama3.2
> ```
> Download the model first: `ollama pull llama3.2`

### Option E: Gemini via Google AI Studio

```
LLM_PROVIDER=gemini
OPENAI_API_KEY=...  # Google AI Studio API key
```

Gemini is accessed through its OpenAI-compatible endpoint. When Gemini rejects a
request because its quota is exhausted, the RSS watcher records a 24-hour
cooldown in `data/` before trying further feed articles.

Default model is `gemini-2.5-flash`, fixed as a project default in
`src/news_analyser/__init__.py`; override with `GEMINI_MODEL` if needed.

### Option F: Mistral

```
LLM_PROVIDER=mistral
MISTRAL_API_KEY=...  # from console.mistral.ai
```

Also accessed through an OpenAI-compatible endpoint (`https://api.mistral.ai/v1`).
Default model is `mistral-medium-latest`, fixed as a project default in
`src/news_analyser/__init__.py` — `mistral-large-latest` returned
`403 tier_not_allowed` on the free "Experiment" tier when tested; check
`GET /v1/models` with your own key to see what your tier actually unlocks.
The free tier also rate-limits to ~1 request/second and ~500K tokens/minute —
evaluation-only, not for feed/production volume. Override the model with
`MISTRAL_MODEL` if needed.

### Option G: GitHub Copilot CLI

```
LLM_PROVIDER=copilot_cli
```

Requires a GitHub Copilot subscription and the `copilot` CLI installed
(`npm install -g @github/copilot`) and authenticated — either interactively
(`copilot`, then `/login`) or headless via `COPILOT_GITHUB_TOKEN`/`GH_TOKEN`/
`GITHUB_TOKEN` (a Fine-Grained PAT; the practical option for a server, since
`/login` needs a browser).

Uses a project-specific adapter (`src/news_analyser/copilot_cli_adapter.py`),
not the generic OpenAI-compatible pattern the other providers use — the
Copilot CLI is an unofficial-endpoint-free, officially supported agentic
coding tool (not a plain chat-completions API), which needs its own subprocess
handling:
- Tool/shell/file/URL access is locked down via `--available-tools` (no
  argument), since the pipeline sends unvalidated scraped article text as
  model input.
- Each call writes ~64 KB of session state to `~/.copilot/session-state/` with
  no found flag to disable it — the adapter assigns its own `--session-id` per
  call and deletes exactly that directory afterward.

Default model is `gemini-3.8-flash`, fixed as a project default in
`src/news_analyser/__init__.py`; override with `COPILOT_MODEL` (e.g.
`claude-sonnet-5`, `gpt-5.4`, `grok-4.6`, depending on your Copilot plan).

> **Model selection is provider-specific, not global.** Each provider that
> ships with a project default (`gemini`, `mistral`, `cli`, `copilot_cli`) has
> its own override variable (`GEMINI_MODEL`, `MISTRAL_MODEL`,
> `CLAUDE_CLI_MODEL`, `COPILOT_MODEL`) instead of sharing the generic
> `LLM_MODEL`/`OPENAI_MODEL` — this used to bite people switching
> `LLM_PROVIDER`: a model set for one provider silently applied to whichever
> provider was selected next. `LLM_MODEL`/`OPENAI_MODEL` still exist as the
> fallback for providers without a project default (`openai`, `anthropic`,
> `lm_studio`, `copilot`, `m365_copilot` — Options B/C/D), where the model is
> expected to be a per-deployment choice rather than a tested project default.

The CLI doesn't expose a `--list-models` flag — `copilot --model <invalid>`
returns an error but not the valid list; asking the model itself (`copilot -p
"List the exact model IDs selectable via --model"`) worked in practice, and
each candidate can be confirmed by actually passing it to `--model`.

## 5. Start the application

Start the full stack (ChromaDB + backend + frontend) with a single command:

**Linux/macOS:**
```bash
./start.sh
```

**Windows (PowerShell):**
```powershell
.\start.ps1
```

Services are then available at:
- Frontend → http://localhost:4200
- Backend → http://localhost:8000
- ChromaDB → http://localhost:8001

Stop all services with `Ctrl+C`.

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

## 6. First test

```bash
python run.py --url https://www.tagesschau.de/ausland/europa/ukraine-krieg-100.html
```

Expected output:
```
[*] Fetching: https://...
[*] Analyzing (...) 
[+] Stored. Orwell-Index: ...  |  Bernays Score: ...  |  DK-Index: ...
    Techniken: [...]
```

## 7. Statistics report

```bash
python run.py --stats
```

## 8. RSS feed collector (optional)

Single run:
```bash
python run.py --feed
```

Continuous mode (hourly):
```bash
python run.py --feed --auto
```

## 9. Analyse a text file directly

```bash
python run.py --text-file article.txt --domain example.com
```

---

## Common errors

### `OPENAI_API_KEY not set`
→ `.env` file missing or `LLM_PROVIDER` not set. Check step 4.

### `ModuleNotFoundError`
→ Dependencies not installed. Repeat step 2.

### `[E050] Can't find model 'de_core_news_md'`
→ spaCy language model not downloaded. Run: `python -m spacy download de_core_news_md`

### `TypeError: Unable to evaluate type annotation 'str | None'`
→ Python version too old (3.9). Install Python ≥ 3.10 and recreate `.venv` (step 2).

### `could not determine executable to run` (frontend)
→ `npm install` in the `frontend/` directory was not run. Repeat step 3.

### `claude: command not found` (CLIAdapter)
→ Claude Code CLI not installed. Installation: https://claude.ai/code

### ChromaDB warnings on startup (`HF Hub unauthenticated`)
→ Harmless, can be ignored. The embedding model loads correctly regardless.
