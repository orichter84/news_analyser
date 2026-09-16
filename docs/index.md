# Documentation Index

Full documentation for the News Analyser project, organised by category. Start here.

## Environments

How to run the project in each of its environments.

- [`environments/local.md`](environments/local.md) — local setup, installation, LLM provider configuration, troubleshooting
- [`environments/development.md`](environments/development.md) — planned, does not exist yet
- [`environments/server.md`](environments/server.md) — current production setup (snapshot, expected to change)

## Reference

How the system currently works, kept in sync with the implementation.

- [`reference/reference.md`](reference/reference.md) — analysis output schema, indicators, paywall detection, techniques database
- [`reference/analyse_architektur.md`](reference/analyse_architektur.md) — indicator design rationale, Pass 0–2 pipeline
- [`reference/web_architecture.md`](reference/web_architecture.md) — backend/frontend architecture, API endpoints
- [`reference/publisher_profiling.md`](reference/publisher_profiling.md) — cross-article publisher analysis
- [`reference/prompting_patterns.md`](reference/prompting_patterns.md) — general prompting techniques in `pass1.md`/`pass2.md`, with model attribution

## Concepts, Validation & Decisions

The "how did we get here" narrative — motivation, experiments, and the decisions they
led to. See [`concepts/README.md`](concepts/README.md) for the full timeline.

- [`concepts/decisions/`](concepts/decisions/) — chronological architecture decisions
- [`concepts/proposals/`](concepts/proposals/) — concepts not yet decided or implemented
- [`concepts/validation/`](concepts/validation/) — empirical tests and evidence

## Planning

- [`planning/todo.md`](planning/todo.md) — roadmap: implemented vs. open features
- [`planning/auswertungen.md`](planning/auswertungen.md) — catalogue of possible future analyses

## Analyses

- [`analyses/bernays_score_pipeline_analysis.md`](analyses/bernays_score_pipeline_analysis.md) — Stufenweise Untersuchung der Bernays-Score-Berechnung und Zitatvalidierung
- [`analyses/orwell_index_pipeline_analysis.md`](analyses/orwell_index_pipeline_analysis.md) — Stufenweise Untersuchung der Orwell-Index-Bestimmung und Signalfusion
- [`analyses/dunning_kruger_index_pipeline_analysis.md`](analyses/dunning_kruger_index_pipeline_analysis.md) — Stufenweise Untersuchung des Dunning-Kruger Index und epistemischer Begründungspflicht
- [`analyses/politische_stroemung_pipeline_analysis.md`](analyses/politische_stroemung_pipeline_analysis.md) — Stufenweise Untersuchung der Politischen Strömung, Label-Taxonomie und Belegprüfung
- [`analyses/meta_validierung_gemini_analysen.md`](analyses/meta_validierung_gemini_analysen.md) — Claude-Meta-Validierung der vier Gemini-Indikator-Analysen
- [`analyses/vorschlag_pipeline_haertung_todo.md`](analyses/vorschlag_pipeline_haertung_todo.md) — Strukturierter Maßnahmenplan und ToDo-Liste zur Pipeline-Härtung
- [`analyses/sampling_konfiguration_und_lauf_varianz.md`](analyses/sampling_konfiguration_und_lauf_varianz.md) — Temperature und JSON-Mode als bisher unbeachtete Stellschrauben, eingeordnet gegen die Lauf-zu-Lauf-Varianz aus ADR 0010

## Archive

- [`archive/`](archive/) — abandoned approaches, kept for historical record
