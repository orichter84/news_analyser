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
