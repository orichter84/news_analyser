# Setup-Anleitung

## 1. Repository klonen

```bash
git clone https://github.com/orichter84/news_analyser.git
cd news_analyser
```

## 2. Abhängigkeiten installieren

```bash
python -m pip install -r requirements.txt
```

## 3. Konfiguration anlegen

`.env`-Datei im Projektroot erstellen (nicht im Repository enthalten):

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

## 4. Erster Test

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

## 5. Statistik-Report

```bash
python run.py --stats
```

## 6. RSS-Feed-Collector (optional)

Einmaliger Lauf:
```bash
python run.py --feed
```

Dauerbetrieb (stündlich):
```bash
python run.py --feed --auto
```

## 7. Textdatei direkt analysieren

```bash
python run.py --text-file artikel.txt --domain beispiel.de
```

---

## Häufige Fehler

### `OPENAI_API_KEY not set`
→ `.env`-Datei fehlt oder `LLM_PROVIDER` ist nicht gesetzt. Schritt 3 prüfen.

### `ModuleNotFoundError`
→ Abhängigkeiten nicht installiert. Schritt 2 wiederholen.

### `claude: command not found` (bei CLIConnector)
→ Claude Code CLI nicht installiert. Installation: https://claude.ai/code

### ChromaDB-Warnungen beim Start (`HF Hub unauthenticated`)
→ Harmlos, kann ignoriert werden. Das Embedding-Modell lädt trotzdem korrekt.
