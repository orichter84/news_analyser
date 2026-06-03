# Setup-Anleitung

## Voraussetzungen

- **Python ≥ 3.10** (empfohlen: 3.12) — Python 3.9 wird nicht unterstützt
- **Node.js ≥ 18** — für Angular Frontend und Claude Code CLI

## 1. Repository klonen

```bash
git clone https://github.com/orichter84/news_analyser.git
cd news_analyser
```

## 2. Python-Umgebung einrichten

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-api.txt
```

## 3. Frontend-Abhängigkeiten installieren

```bash
cd frontend
npm install
cd ..
```

## 4. Konfiguration anlegen

`.env`-Datei im Projektroot erstellen (nicht im Repository enthalten):

### Allgemeine Einstellungen (empfohlen)

```
TOKENIZERS_PARALLELISM=false
```

Verhindert einen CPU-Deadlock beim ersten Laden des Embedding-Modells auf macOS.

### Option A: Claude Code CLI (empfohlen, kein API-Key nötig)

```
LLM_PROVIDER=cli
OPENAI_MODEL=claude-sonnet-4-6
```

Voraussetzung: Claude Code CLI muss installiert und eingeloggt sein.

Installation (Node.js ≥18 erforderlich):
```bash
npm install -g @anthropic-ai/claude-code
```

Einmalig einloggen (öffnet Browser zur OAuth-Authentifizierung):
```bash
claude
```

Prüfen ob alles funktioniert:
```bash
claude --version
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

### Option D: Lokales Modell via LM Studio

```
LLM_PROVIDER=lm_studio
OPENAI_MODEL=<modellname-in-lm-studio>
```

LM Studio muss unter `http://localhost:1234` laufen.

## 5. Anwendung starten

Den Full-Stack (ChromaDB + Backend + Frontend) mit einem Befehl starten:

```bash
./start.sh
```

Die Services sind dann erreichbar unter:
- Frontend → http://localhost:4200
- Backend → http://localhost:8000
- ChromaDB → http://localhost:8001

Mit `Ctrl+C` alle Services beenden.

## 6. Erster Test

```bash
python run.py --url https://www.tagesschau.de/ausland/europa/ukraine-krieg-100.html
```

Erwartete Ausgabe:
```
[*] Fetching: https://...
[*] Analyzing (...) 
[+] Stored. Orwell-Index: ...  |  Bernays Score: ...  |  DK-Index: ...
    Techniken: [...]
```

## 7. Statistik-Report

```bash
python run.py --stats
```

## 8. RSS-Feed-Collector (optional)

Einmaliger Lauf:
```bash
python run.py --feed
```

Dauerbetrieb (stündlich):
```bash
python run.py --feed --auto
```

## 9. Textdatei direkt analysieren

```bash
python run.py --text-file artikel.txt --domain beispiel.de
```

---

## Häufige Fehler

### `OPENAI_API_KEY not set`
→ `.env`-Datei fehlt oder `LLM_PROVIDER` ist nicht gesetzt. Schritt 3 prüfen.

### `ModuleNotFoundError`
→ Abhängigkeiten nicht installiert. Schritt 2 wiederholen.

### `TypeError: Unable to evaluate type annotation 'str | None'`
→ Python-Version zu alt (3.9). Python ≥ 3.10 installieren und `.venv` neu anlegen (Schritt 2).

### `could not determine executable to run` (Frontend)
→ `npm install` im `frontend/`-Verzeichnis wurde nicht ausgeführt. Schritt 3 wiederholen.

### `claude: command not found` (bei CLIAdapter)
→ Claude Code CLI nicht installiert. Installation: https://claude.ai/code

### ChromaDB-Warnungen beim Start (`HF Hub unauthenticated`)
→ Harmlos, kann ignoriert werden. Das Embedding-Modell lädt trotzdem korrekt.
