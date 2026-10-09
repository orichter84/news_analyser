# 0013 — Reject Incomplete Analyses Instead of Repairing or Degrading Them

**Date:** 2026-10-09 · **Status:** Active

## Context

An analysis that stopped part-way could still end up stored as a normal result.
There were three ways this could happen:

1. **Truncated output (Gemini/Mistral).** `llm_adapter.OpenAIAdapter` only logs a
   warning when `finish_reason != "stop"`, for example `"length"` once
   `max_tokens` (8192) is reached, or `"content_filter"`. It then returns the cut-off
   text anyway. `_extract_json` passes text that fails `json.loads` to `json_repair`,
   which closes open strings, arrays and objects. The result is a *valid but
   incomplete* dict. Missing fields then fell back to defaults without any error:
   `orwell_index_structural` 0.0, `dunning_kruger_index` 0.0,
   `politische_stroemung` `["neutral"]`, `themenbereich` `"Sonstiges"`, and a
   `detected_techniques` list cut off part-way. This skewed result was stored in
   SQLite **and** added as a ChromaDB anchor, where it could act as a calibration
   reference for later Pass 1 calls.
2. **Truncated output (`cli`/`copilot_cli`).** These adapters have no
   `finish_reason`. A cut-off stdout went through the same `json_repair` path.
3. **Pass 0 failure.** `detect_groups()` returned `[]` on any adapter error,
   unparseable response or non-list response. The analysis then continued with spaCy
   NER only. Pass 1 therefore ran on text whose group anonymisation was incomplete
   ([0001](0001-pass0-group-detection-and-quote-stripping.md)), and the result was
   stored as if nothing had gone wrong. The same applied to a truncated Pass 0 list
   that `json_repair` closed.

Quota errors (`GeminiQuotaExceededError`) and Pass 1/2 adapter exceptions already
aborted cleanly, with nothing stored and no anchor added.

## Decision

The rule is that an analysis that stopped part-way is never stored, whatever the
reason. An analysis whose steps all completed is stored as before.

- **`StrictOpenAIAdapter`** (`src/news_analyser/strict_openai_adapter.py`), a
  project-local subclass of `llm_adapter.OpenAIAdapter`, is now registered for
  `gemini` and `mistral`. It raises `LLMGenerationError` for any `finish_reason`
  other than `"stop"`/`None`, and for empty content.
- **`_extract_json`** no longer hands text to `json_repair` when that text, after
  fence and thinking-token stripping, doesn't end in `}` or `]`. Truncated output
  always ends mid-structure, so it is rejected. Genuine formatting slips such as a
  trailing comma still get repaired. This is the only truncation signal available
  for `cli`/`copilot_cli`.
- **`detect_groups()`** now aborts instead of returning `[]` on any failure: an adapter
  error, unparseable or truncated output, or a non-list response. A genuine empty
  list (`[]`) still means "no groups found" and the analysis continues.
- **`AnalysisAbortedError(stage, reason)`** (`agents/errors.py`) replaces the old
  "log something, return `None`" convention. Every failure in Pass 0, 1 or 2 raises
  it with the pass name and the concrete reason. `analyze_article` now either returns
  a complete result or raises; it never returns `None`. It logs each abort exactly
  once, at ERROR level, with the URL:
  `Analyse abgebrochen, nichts gespeichert — <url> — Pass 1: Antwort unvollständig
  (finish_reason='length', max_tokens=8192).` Before, the log showed an error line
  without URL and sometimes without pass, followed by a misleading
  `Analysis failed – no JSON returned.`
  `GeminiQuotaExceededError` stays separate because it triggers the feed cooldown.

## Consequences

- Callers catch `AnalysisAbortedError` and skip `store_result`: `main.run`, which the
  feed loop also uses, `run_text_file`, and the web API job. `add_anchor` is only
  reached once all passes have succeeded. The API job now reports the reason in its
  status message (`Analyse abgebrochen (Pass 2: …) – nichts gespeichert.`). Before,
  it showed only `Analyse fehlgeschlagen`. Other unexpected errors in the API job are
  now logged with URL and traceback (`news_analyser.api.analyse`). Before, they
  were not logged at all.
- The `notebooks/symmetry_tests.ipynb` notebook and
  `docs/concepts/validation/run_symmetry_tests.py` were adjusted from the old
  `None` check to catching the exception.
- In feed mode, a failed article is not in the DB, so the next cycle picks it up again
  as new. This is a natural retry. An article that hits `max_tokens` every time will
  be retried every cycle. If that shows up in the logs (`finish_reason='length'`), the
  fix is to raise `max_tokens` in `__init__.py` rather than to loosen this rule.
- Pass 0 is now a hard dependency. Pass 0 timeouts on the `cli` adapter were observed
  historically (see [bias-validation.md](../validation/bias-validation.md)), and they
  now abort the article instead of degrading it.
- The fix lives in this project rather than in `llm-adapter` (v0.4.2), so it takes
  effect without a library release. Moving the strict behaviour upstream, for example
  as a config flag, would let the subclass go.
- Regression coverage: `tests/test_strict_openai_adapter.py`, and the new truncation
  cases in `tests/test_analyzer_json.py` and `tests/test_group_detector.py`, and
  `tests/test_analysis_abort.py` for stage/reason propagation and the log line.
