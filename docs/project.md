# News Analyser

Automatisiertes System zur Erkennung von Manipulations- und Framing-Techniken in deutschsprachigen Nachrichtenartikeln. Artikel werden per URL oder RSS-Feed eingelesen, von einem LLM-Agenten in zwei Analysedurchläufen ausgewertet und strukturiert in einer lokalen ChromaDB gespeichert. Eine FastAPI + Angular Web-UI ermöglicht Auswertung und Recherche.

---

## Architektur: Zwei-Pass-Analyse

```
RSS-Feed / URL
      ↓
  scraper.py         → Reintext + Paywall-Erkennung (trafilatura + BeautifulSoup + HTML-Marker)
      ↓
  topic_filter.py    → Keyword-Themenfilter (kein LLM-Call, konfigurierbar)
      ↓
  anonymizer.py      → spaCy NER: Personen/Orte/Org → Platzhalter (Bias-Elimination)
      ↓
  ┌─────────────────────────────────────┐
  │ Pass 1 — anonymisierter Text        │
  │ → Orwell-Index, Bernays-Score       │
  │ → Erkannte Manipulationstechniken   │
  │ (kein Modellbias auf Eigennamen)    │
  └─────────────────────────────────────┘
      ↓
  ┌─────────────────────────────────────┐
  │ Pass 2 — Originaltext               │
  │ → Politische Strömung (Labels)      │
  │ → Dunning-Kruger-Index              │
  │ → Themenbereich                     │
  │ → Manipulation Targets              │
  └─────────────────────────────────────┘
      ↓
  technique_store.py → Semantische Normalisierung der Techniken-Namen
      ↓
  anchor_store.py    → RAG-Anker für zukünftige Analysen speichern
      ↓
  db_storage.py      → Embedding + Metadaten → ChromaDB (articles)
```

**Warum zwei Passes?**
LLMs haben trainingsbedingte Biases gegenüber politischen Akteuren. Pass 1 anonymisiert alle Eigennamen, sodass Orwell-Index und Bernays-Score struktur- statt personenbezogen berechnet werden. Pass 2 nutzt den Originaltext für Einordnungen, bei denen Akteursnamen relevant sind.

---

## Projektstruktur

```
news_analyser/
├── run.py                          Einstiegspunkt CLI
├── requirements.txt                Python-Abhängigkeiten (Analyse-Engine)
├── requirements-api.txt            Python-Abhängigkeiten (FastAPI Backend)
├── feeds.txt                       RSS-Feed-URLs (eine pro Zeile, # = Kommentar)
├── .env.example                    Vorlage für Umgebungsvariablen
│
├── src/news_analyser/
│   ├── main.py                     CLI-Logik (--url, --feed, --stats, --auto)
│   ├── scraper.py                  Artikel-Extraktion + Paywall-Erkennung
│   ├── analyzer.py                 Zwei-Pass LLM-Analyse
│   ├── anonymizer.py               spaCy NER-basierte Anonymisierung
│   ├── keywords.py                 Keyword-Signal (links/rechts/extremism)
│   ├── topic_filter.py             Keyword-Themenvorfilter für RSS
│   ├── anchor_store.py             RAG-Ankerpunkte (ChromaDB: orwell_anchors)
│   ├── technique_store.py          Techniken-DB + semantische Normalisierung
│   ├── db_storage.py               ChromaDB-Persistenz (articles)
│   ├── feed.py                     RSS-Collector
│   ├── stats.py                    Statistik-Auswertung (pandas)
│   ├── config.py                   LLMConfig, FeedConfig
│   │
│   ├── prompts/system/
│   │   ├── pass1.md                Systemprompt Pass 1 (anonymisiert)
│   │   └── pass2.md                Systemprompt Pass 2 (Original)
│   │
│   └── connectors/                 LLM-Backend-Abstraktion
│       ├── base.py                 LLMConnector ABC
│       ├── anthropic_connector.py  Anthropic Messages API
│       ├── openai_connector.py     OpenAI / Ollama / LM Studio
│       ├── cli_connector.py        Claude Code CLI (Subprocess)
│       └── M365CopilotConnector.py Microsoft 365 Copilot
│
├── backend/                        FastAPI REST-API
│   ├── main.py                     App-Instanz, CORS, Router
│   └── routers/
│       ├── articles.py             GET /articles, GET /articles/{id}
│       ├── analyse.py              POST /analyse (BackgroundTask + Job-Polling)
│       ├── stats.py                GET /stats
│       ├── search.py               GET /search (semantische Suche)
│       └── techniques.py           GET /techniques, GET /techniques/{id}
│
├── frontend/                       Angular 17+ Web-UI
│   └── src/app/
│       ├── features/
│       │   ├── dashboard/          KPI-Karten, Top-Techniken, Letzte Artikel
│       │   ├── articles/           Artikel-Liste (Filter) + Detailansicht
│       │   ├── stats/              Statistik-Charts und Domain-Tabelle
│       │   ├── submit/             URL einreichen + Job-Status-Polling
│       │   ├── techniques/         Techniken-Übersicht + Detailseite (/techniques/:id)
│       │   └── knowledge/          "Über dieses Projekt" (Methodik, Indikatoren, Quellen)
│       └── core/
│           ├── models/             TypeScript-Interfaces
│           └── services/           ApiService (HttpClient)
│
└── data/
    └── chroma_db/                  Lokale Vektordatenbank (auto-generiert)
        ├── articles                Analysierte Artikel
        ├── orwell_anchors          RAG-Kalibrierungsanker
        └── techniques              Dokumentierte Manipulationstechniken
```

---

## Installation

```bash
# Analyse-Engine
pip install -r requirements.txt
python -m spacy download de_core_news_md

# FastAPI Backend
pip install -r requirements-api.txt

# Angular Frontend
cd frontend
npm install

# Konfiguration
cp .env.example .env
# .env mit API-Key und Provider befüllen
```

---

## Verwendung

### Web UI starten

```bash
# Terminal 1 — Backend (Port 8000)
cd backend
uvicorn main:app --reload

# Terminal 2 — Frontend (Port 4200)
cd frontend
ng serve
```

### CLI — Einzelnen Artikel analysieren
```bash
python run.py --url https://www.spiegel.de/...
```

### CLI — RSS-Feeds einmalig abrufen
```bash
python run.py --feed
```

### CLI — RSS-Watcher (Dauerbetrieb)
```bash
python run.py --feed --auto
```

### CLI — Statistik-Report
```bash
python run.py --stats
python run.py --stats --top 10
```

---

## Konfiguration (.env)

### LLM

| Variable | Standard | Beschreibung |
|---|---|---|
| `LLM_PROVIDER` | `openai` | `openai`, `anthropic`, `cli`, `lm_studio`, `copilot` |
| `OPENAI_API_KEY` | – | API-Key für OpenAI oder kompatible Endpunkte |
| `ANTHROPIC_API_KEY` | – | API-Key für Anthropic |
| `OPENAI_MODEL` | `gpt-4o` | Modellname |
| `LLM_TEMPERATURE` | `0.2` | Sampling-Temperatur |
| `LLM_MAX_TOKENS` | `2048` | Max. Tokens pro Antwort |

### Feed

| Variable | Standard | Beschreibung |
|---|---|---|
| `FEED_MODE` | `manual` | `manual` (einmalig) oder `auto` (Dauerbetrieb) |
| `FEED_INTERVAL` | `3600` | Sekunden zwischen Läufen im auto-Modus |
| `FEED_MAX_ARTICLES` | `20` | Max. neue Artikel pro Lauf |
| `FEED_TOPICS` | *(siehe unten)* | Erlaubte Themenbereiche, kommagetrennt |

**FEED_TOPICS:** Filtert Artikel vor dem LLM-Call anhand von Keywords (kein API-Kosten).
- Standard: `Politik,Außenpolitik,Wirtschaft,Gesellschaft,Justiz,Technologie`
- Deaktivieren: `FEED_TOPICS=all`
- Verfügbare Werte: `Politik`, `Außenpolitik`, `Wirtschaft`, `Gesellschaft`, `Justiz`, `Gesundheit`, `Klima`, `Kultur`, `Technologie`

---

## Analyse-Output (JSON)

```json
{
  "source_url": "https://...",
  "domain": "spiegel.de",
  "title": "Artikeltitel",
  "author": "Name",
  "published_at": "2026-05-26T10:00:00Z",
  "word_count": 850,
  "detected_techniques": [
    {
      "technique": "Appeal to Fear",
      "quote": "exaktes Textzitat",
      "explanation": "Begründung der Wirkung"
    }
  ],
  "framing_target": {
    "main_narrative": "Zentrale These des Artikels",
    "intended_sentiment": "Angst | Empörung | Zustimmung | …",
    "orwell_index": 0.42,
    "dunning_kruger_index": 0.35
  },
  "politische_stroemung": ["konservativ", "nationalpopulistisch"],
  "themenbereich": "Politik",
  "manipulation_targets": [
    {
      "entity": "Bundesregierung",
      "direction": "negativ",
      "rolle": "Aggressor"
    }
  ]
}
```

### Indikatoren

| Indikator | Bereich | Beschreibung |
|---|---|---|
| `orwell_index` | 0.0 – 1.0 | Rhetorischer Extremismus. 0 = sachlich, 1 = stark manipulativ |
| `bernays_score` | 0.0 – ∞ | Manipulationstechniken pro 1000 Wörter |
| `dunning_kruger_index` | 0.0 – 1.0 | Wie überzeugt ein Text formuliert ist ohne durch Quellen, Konjunktiv oder Einschränkungen gedeckt zu sein |
| `politische_stroemung` | Labels | Ideologische Verortung (mehrere möglich): `liberal`, `konservativ`, `sozialdemokratisch`, `sozialistisch`, `nationalistisch`, `grün`, u.a. |
| `themenbereich` | Kategorie | Thematische Einordnung: Politik, Wirtschaft, Technologie, … |
| `manipulation_targets` | Liste | Entitäten mit Richtung (positiv/negativ/neutral) und Rolle (Opfer, Aggressor, Held, Feind, Sündenbock, …) |

---

## Paywall-Erkennung

Zweistufig:
1. **HTML-Marker** — Piano/TinyPass Script-URLs (`cdn.tinypass.com`), CSS-Klassen (`paywall`, `piano`, `c-piano`, `spplus`, `z-paywall`, `faz-premium`, u.a.)
2. **Wortanzahl-Fallback** — Artikel mit < 150 Wörtern werden als Paywall-Teaser markiert

Paywalled Artikel werden nicht analysiert und nicht gespeichert.

---

## Techniken-Datenbank

19 dokumentierte Manipulationstechniken sind in `technique_store.py` definiert und werden beim ersten Start automatisch in ChromaDB eingespielt (`techniques`-Collection). Die Collection liegt in `data/` und wird nicht ins Repository gepusht — die Quelldaten in `technique_store.py` sind jedoch versioniert und ermöglichen eine automatische Wiederherstellung. Bei der Analyse werden LLM-Freitext-Ausgaben semantisch auf kanonische Namen gemappt (Cosine-Similarity, Schwellenwert 0.35). Neue Techniken können durch Erweiterung von `technique_store.py` hinzugefügt werden.

Kategorien: **Emotional** (Appeal to Fear, Bandwagon, Appeal to Emotion), **Logisch** (Ad Hominem, Straw Man, False Dichotomy, Slippery Slope, Cherry Picking), **Rhetorisch** (Loaded Language, Whataboutism, Euphemismus, Dysphemismus, Appeal to Authority, Presuppositional Framing), **Strukturell** (Framing, Agenda Setting, False Balance, Scapegoating, Repetition).

---

## Lokaler LLM-Betrieb (LM Studio)

```bash
LLM_PROVIDER=lm_studio
# Modell muss unter http://localhost:1234 laufen
# Empfohlen: Mistral 7B Q8 oder Llama 3 8B Q8
```
