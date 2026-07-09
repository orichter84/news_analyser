# Konzept-Validierungstests

Testet einzelne Bausteine aus den Konzeptentwürfen in `docs/concept/*.md`, bevor sie in die
Produktionspipeline (`src/news_analyser/`) übernommen werden.

## Konventionen

- Jeder Test bekommt einen eigenen nummerierten Unterordner (`NN_kurzname/`).
- Tests binden Projekt-Code ausschließlich **als Library ein** (`sys.path.insert(..., "src")` +
  Import), verändern aber nie den Produktionscode und laufen nie gegen die Produktions-Ressourcen
  (eigene ChromaDB-Instanz, eigene Testdaten statt der laufenden Pipeline-DB als Ziel).
- Interaktive Exploration → Jupyter-Notebook (siehe `notebooks/symmetry_tests.ipynb` für das
  etablierte Muster). Notebook-Outputs werden von `nbstripout` vor jedem Commit entfernt
  (`.gitattributes`) — Ergebnisse deshalb zusätzlich in einer `results.md` je Testordner
  festhalten, analog zu `docs/concept/bias-validation.md`.
- Lokale, generierte Ressourcen (eigene Chroma-DBs, Caches) gehören ins `.gitignore`, nicht ins
  Repo.

## Tests

| # | Ordner | Frage | Status |
|---|---|---|---|
| 1 | [01_klasse1_semantic_nn](01_klasse1_semantic_nn/) | Trennt Nearest-Neighbor-Suche auf Satzebene Techniken sauber, oder streut das Embedding zu breit (Klasse 1 aus [konzept_hybrid_technik_erkennung.md](../konzept_hybrid_technik_erkennung.md))? | offen |
