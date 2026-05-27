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

### 3. Umgebungsvariablen konfigurieren

```bash
cp .env.example .env
# .env mit einem Editor öffnen und API-Key eintragen
```

Mindestens `LLM_PROVIDER` setzen. Je nach Provider wird zusätzlich ein API-Key benötigt — `cli` und `lm_studio` funktionieren ohne. Alle Optionen sind in `.env.example` dokumentiert.

### 4. Frontend (optional)

```bash
cd frontend
npm install
```

---

## Starten

Backend und Frontend laufen parallel — am besten zwei separate Terminals im Projektverzeichnis öffnen.

### Terminal 1 — Backend (Port 8000)

```bash
cd backend
uvicorn main:app --reload
```

### Terminal 2 — Frontend (Port 4200)

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
| `cli` | — | Claude Code CLI (kein API-Key erforderlich) |
| `lm_studio` | — | LM Studio lokaler Server |
| `copilot` | `GITHUB_TOKEN` | GitHub Copilot |
| `m365_copilot` | `M365_COPILOT_ACCESS_TOKEN` | Microsoft 365 Copilot |

### Claude Code CLI (`cli`)

Der `cli`-Provider nutzt die lokal installierte [Claude Code CLI](https://claude.ai/code) als Subprocess — kein separater API-Key nötig, die Authentifizierung läuft über den CLI-Login.

**Installation (Node.js 18+ erforderlich):**

```bash
npm install -g @anthropic-ai/claude-code
```

**Anmelden:**

```bash
claude login
```

Ein Browser-Fenster öffnet sich zur Authentifizierung mit dem Anthropic-Account. Nach dem Login kann die CLI direkt verwendet werden.

**`.env` konfigurieren:**

```env
LLM_PROVIDER=cli
```

### LM Studio (`lm_studio`)

[LM Studio](https://lmstudio.ai) ermöglicht den Betrieb lokaler Sprachmodelle ohne Cloud-Anbindung — kein API-Key erforderlich.

**Installation:**

1. LM Studio von [lmstudio.ai](https://lmstudio.ai) herunterladen und installieren
2. Im Tab **Discover** ein Modell herunterladen (empfohlen: Mistral 7B Q8 oder Llama 3 8B Q8)
3. Im Tab **Local Server** das Modell laden und den Server starten — läuft standardmäßig auf Port 1234

**`.env` konfigurieren:**

```env
LLM_PROVIDER=lm_studio
```

Das aktive Modell wird in LM Studio selbst festgelegt — `OPENAI_MODEL` hat keinen Effekt. Die `OPENAI_BASE_URL` muss ebenfalls nicht gesetzt werden, der Connector verwendet automatisch `http://localhost:1234/v1`.

> **Alternative: Ollama** — funktioniert ebenfalls lokal über den `openai`-Provider, da Ollama eine OpenAI-kompatible API anbietet:
> ```env
> LLM_PROVIDER=openai
> OPENAI_API_KEY=ollama
> OPENAI_BASE_URL=http://localhost:11434/v1
> OPENAI_MODEL=llama3.2
> ```
> Modell vorher herunterladen: `ollama pull llama3.2`

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
├── config/                  Nutzer-Konfiguration (committed, kein Secret)
│   ├── feeds.txt            RSS-Feed-URLs (eine pro Zeile, # für Kommentare)
│   └── rerun_urls.txt       URLs für manuelle Wiederholung (--file)
├── requirements.txt         Analyse-Pipeline-Dependencies
├── requirements-api.txt     Backend-Dependencies (FastAPI etc.)
└── .env.example             Konfigurationsvorlage (Secrets + Provider-Auswahl)
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
