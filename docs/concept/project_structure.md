# Project Structure — Ziel-Architektur

## Verzeichnisstruktur

```
news_analyser/
├── .vscode/
│   └── settings.json        VS Code: Python-Interpreter, Go-Path, Extension-Einstellungen
│
├── pipeline/                Python-Pipeline (Kern der Analyse)
│   ├── pyproject.toml       Package-Definition + Versionierung
│   ├── src/
│   │   └── news_analyser/   Analyse-Bibliothek
│   │       ├── agents/      Analyzer (Pass 0/1/2), Group Detector
│   │       ├── anonymizer/  spaCy-basierte Anonymisierung
│   │       ├── repositories/ ChromaDB (Artikel, Anchors, Techniken, Rollen)
│   │       ├── prompts/     System-Prompts (pass0/1/2.md)
│   │       ├── scraper.py
│   │       ├── feed.py
│   │       ├── keywords.py
│   │       ├── stats.py
│   │       └── main.py      CLI-Einstiegspunkt
│   ├── notebooks/           Jupyter-Notebooks (Debugging, Symmetrie-Tests)
│   └── run.py               Runner-Script
│
├── server/                  Go-Backend (Web-API)
│   ├── go.mod
│   ├── go.sum
│   └── main.go
│
├── frontend/                Angular SPA (unverändert)
│   ├── angular.json
│   └── src/
│
├── data/                    Laufzeit-Daten (nicht unter Versionskontrolle)
│   ├── chroma_db/           ChromaDB-Persistenz
│   └── debug_last_run/      Debug-Output des letzten Analyse-Laufs
│
├── docs/                    Dokumentation & Konzepte
├── config/                  Konfigurationsdateien (feeds.txt etc.)
└── .env                     Lokale Umgebungsvariablen (nicht unter Versionskontrolle)
```

## Komponenten & Verantwortlichkeiten

| Komponente | Technologie | Aufgabe |
|---|---|---|
| `pipeline/` | Python + llm-adapter | spaCy, sentence-transformers, LLM-Calls, ChromaDB-Schreibzugriff |
| `server/` | Go | Angular servieren, ChromaDB lesen, Pipeline als Subprocess starten |
| `frontend/` | Angular | SPA — unverändert |
| ChromaDB | Externer HTTP-Server | Von Pipeline und Go-Server gleichzeitig angesprochen |

## Schnittstelle Go ↔ Python

Go startet die Pipeline als Subprocess:

```
python -m news_analyser --url https://... --json
```

Die Pipeline schreibt das Ergebnis als JSON auf stdout und speichert es parallel in ChromaDB. Go liest stdout und kann das Ergebnis direkt an den Client weiterleiten.

## VS Code Integration

VS Code erkennt alle drei Sprachen automatisch anhand ihrer Konfigurations-Dateien:

- `pipeline/pyproject.toml` → Python Extension
- `server/go.mod` → Go Extension
- `frontend/angular.json` → Angular/TypeScript Extension

`.vscode/settings.json` setzt den Python-Interpreter auf das `.venv` in `pipeline/`.

## Migration vom aktuellen Stand

| Heute | Ziel | Aktion |
|---|---|---|
| `src/news_analyser/` | `pipeline/src/news_analyser/` | Verschieben |
| `run.py` (root) | `pipeline/run.py` | Verschieben |
| `notebooks/` | `pipeline/notebooks/` | Verschieben |
| `backend/` (FastAPI) | entfällt | Löschen sobald Go-Server bereit |
| — | `server/` | Neu anlegen |
| `requirements.txt` | `pipeline/pyproject.toml` | Ersetzen |
| `requirements-api.txt` | entfällt | FastAPI-Deps fallen weg |
