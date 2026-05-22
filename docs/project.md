# News Analyser

Automatisiertes System zur Erkennung von Manipulations- und Framing-Techniken in Online-Nachrichtenartikeln. Artikel werden per URL oder RSS-Feed eingelesen, von einem LLM-Agenten analysiert und strukturiert in einer lokalen Vektordatenbank gespeichert.

---

## Funktionsweise

```
RSS-Feed / URL
      ↓
  scraper.py        → Reintext-Extraktion (trafilatura + BeautifulSoup)
      ↓
  analyzer.py       → LLM-Agent analysiert Manipulationstechniken
      ↓
  db_storage.py     → Embedding + JSON-Payload → ChromaDB
      ↓
  stats.py          → Aggregierte Auswertung mit pandas
```

Der LLM-Agent gibt ein strukturiertes JSON zurück mit erkannten Techniken (FUD, Framing, Loaded Language, …), einem Bias-Score (−1.0 bis +1.0) und der zentralen Narrative des Artikels.

---

## Projektstruktur

```
news_analyser/
├── run.py                          Einstiegspunkt
├── requirements.txt
├── feeds.txt                       RSS-Feed-URLs (eine pro Zeile)
├── .env.example                    Vorlage für Umgebungsvariablen
│
├── src/news_analyser/
│   ├── main.py                     CLI-Logik
│   ├── scraper.py                  Artikel-Extraktion
│   ├── analyzer.py                 LLM-Analyse
│   ├── db_storage.py               ChromaDB-Persistenz
│   ├── feed.py                     RSS-Collector (manuell & auto)
│   ├── stats.py                    Statistik-Auswertung
│   ├── config.py                   LLMConfig, FeedConfig
│   │
│   ├── prompts/
│   │   └── system/
│   │       └── default.md          Systemprompt des Analyse-Agenten
│   │
│   ├── connectors/                 LLM-Backend-Abstraktion
│   │   ├── base.py                 LLMConnector ABC
│   │   ├── anthropic_connector.py  Anthropic Messages API
│   │   ├── openai_connector.py     OpenAI / Ollama / LM Studio
│   │   ├── cli_connector.py        Claude Code CLI (Subprocess)
│   │   └── M365CopilotConnector.py Microsoft 365 Copilot
│   │
│   └── agents/                     Erweiterungspunkt für weitere Agenten
│
├── data/
│   └── chroma_db/                  Lokale Vektordatenbank (auto-generiert)
├── docs/
├── logs/
└── tests/
```

---

## Installation

```bash
pip install -r requirements.txt
cp .env.example .env
# .env mit API-Key und gewünschtem Provider befüllen
```

---

## Verwendung

### Einzelnen Artikel analysieren
```bash
python run.py --url https://www.spiegel.de/...
```

### Liste von URLs analysieren
```bash
python run.py --file urls.txt
```

### RSS-Feeds manuell abrufen (einmaliger Lauf)
```bash
python run.py --feed
```

### RSS-Feeds im Dauerbetrieb (auto, stündlich)
```bash
python run.py --feed --auto
```

### Intervall überschreiben (alle 30 Minuten)
```bash
python run.py --feed --interval 1800
```

### Statistik-Report ausgeben
```bash
python run.py --stats
python run.py --stats --top 10
```

---

## Konfiguration

Alle Einstellungen werden über Umgebungsvariablen gesetzt (`.env`-Datei).

### LLM

| Variable | Standard | Beschreibung |
|---|---|---|
| `LLM_PROVIDER` | `openai` | `openai`, `anthropic`, `cli`, `lm_studio`, `copilot`, `m365_copilot` |
| `OPENAI_API_KEY` | – | API-Key für OpenAI oder kompatible Endpunkte |
| `ANTHROPIC_API_KEY` | – | API-Key für Anthropic |
| `OPENAI_MODEL` | `gpt-4o` | Modellname (z.B. `claude-sonnet-4-6`) |
| `LLM_TEMPERATURE` | `0.2` | Sampling-Temperatur |
| `LLM_MAX_TOKENS` | `2048` | Max. Tokens in der Antwort |

### Feed

| Variable | Standard | Beschreibung |
|---|---|---|
| `FEED_MODE` | `manual` | `manual` (einmalig) oder `auto` (Dauerbetrieb) |
| `FEED_INTERVAL` | `3600` | Sekunden zwischen Läufen im auto-Modus |
| `FEED_MAX_ARTICLES` | `20` | Max. neue Artikel pro Lauf |
| `FEED_FILE` | `feeds.txt` | Pfad zur Feed-URL-Liste |

### Provider-Beispiele

```bash
# OpenAI
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...

# Anthropic
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_MODEL=claude-sonnet-4-6

# Claude Code CLI (kein API-Key nötig, nutzt bestehende Auth)
LLM_PROVIDER=cli
OPENAI_MODEL=claude-sonnet-4-6

# LM Studio (lokales Modell)
LLM_PROVIDER=lm_studio
# kein API-Key nötig, Modell muss unter http://localhost:1234 laufen
```

---

## Analyse-Output (JSON)

```json
{
  "source_url": "https://...",
  "domain": "spiegel.de",
  "timestamp": "2026-05-22T10:00:00Z",
  "detected_techniques": [
    {
      "technique": "FUD | Framing | Loaded Language | Logical Fallacy | False Balance | Scapegoating | Appeal to Authority | Emotional Manipulation | Omission | Whataboutism | Other",
      "quote": "exaktes Textzitat",
      "explanation": "Präzise Begründung der Wirkung"
    }
  ],
  "framing_target": {
    "main_narrative": "Zentrale Geschichte die der Artikel pusht",
    "target_direction": "Wer/was wird auf- oder abgewertet",
    "intended_sentiment": "Angst | Empörung | Zustimmung | Misstrauen | …",
    "orwell_index": -0.55
  }
}
```

`orwell_index`: −1.0 = stark linksliberal, 0.0 = neutral, +1.0 = stark rechtskonservativ.  
`bernays_score`: Manipulationsintensität = Anzahl Techniken / 1000 Wörter (normalisiert).

---

## Systemprompt anpassen

Der Analyse-Prompt liegt als Markdown-Datei unter `src/news_analyser/prompts/system/default.md` und kann ohne Python-Kenntnisse direkt bearbeitet werden. Änderungen werden beim nächsten Lauf automatisch übernommen.

---

## Statistik-Report

Der Report aggregiert alle gespeicherten Analysen und zeigt:

- **Top N Manipulationstechniken** nach Häufigkeit
- **Bias-Score-Verteilung** (Mittelwert, Median, Streuung, Zählung links/neutral/rechts)
- **Top N Domains** nach Artikel-Anzahl
- **Intendierte Emotionen** nach Häufigkeit
