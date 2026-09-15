# 0009 — Pipeline Hardening: Grounding, Dedup and Denominator Fixes from the Gemini Meta-Review

**Date:** 2026-09-15 (`704849a`, `20796c7`, `3c99d04`) · **Status:** Active

## Context

Gemini 3.8 produced four pipeline analyses for the core indicators
(`docs/analyses/*_pipeline_analysis.md`). A Claude meta-validation
(`docs/analyses/meta_validierung_gemini_analysen.md`) cross-checked every claim
against the actual code and found a mix of already-mitigated prompt issues (see
[0008](0008-gemini-orwell-index-recalibration.md)), one factual error about the
frontend, and several real, previously undocumented gaps:

1. `backend/routers/articles.py` collapsed a genuine `dunning_kruger_index` of
   `0.0` into `null` via `float(x) or None`, in both the list and detail
   endpoints.
2. The detail endpoint (`get_article()`) read `politische_stroemung`
   `{label, quote}` objects correctly out of `analysis_json`, then immediately
   re-flattened them to plain label strings via a second, unguarded
   `_parse_meta()` call — discarding the quote the frontend already had
   markup to render.
3. `politische_stroemung` had no quote-grounding validation at all (unlike
   `detected_techniques` and `manipulation_targets`), and no normalization of
   free-text labels onto a canonical taxonomy (unlike techniques/roles) —
   `neoliberal`, `wirtschaftsliberal`, `marktwirtschaftlich` etc. would all
   persist as distinct labels, splintering publisher-profile aggregations.
4. `detected_techniques` could double-count a passage when two different
   free-text labels normalized to the same canonical technique
   (`normalize_technique`) — no dedup ran afterwards.
5. `bernays_score` normalized `len(detected_techniques)` — counted on the
   quote-*stripped* Pass 1 text — against `word_count`, the *full* article's
   word count. Quote-heavy articles (interviews) got an artificially deflated
   score.
6. `dunning_kruger_index` had no explanation field, making it an
   unauditable number in the UI.

Gemini and Claude jointly drafted a prioritized fix plan
(`docs/analyses/vorschlag_pipeline_haertung_todo.md`), which this ADR
implements (all of it except item 3.2, deliberately deferred — see below).

## Decision

- **`backend/routers/articles.py`:** a `_dk_index()` helper reads
  `dunning_kruger_index` and only falls back to `None` when the field is
  genuinely absent from stored metadata, not when it's `0.0`. `_parse_meta()`
  takes a `flatten_stroemung` flag; the detail endpoint now passes `False` so
  `{label, quote}` objects survive to the frontend, while the list/search
  endpoints keep flattening to plain strings.
- **`analyzer.py`:**
  - `_validate_stroemung_grounding()` nulls a `politische_stroemung` label's
    `quote` when it can't be found in the source text, but — unlike
    technique/target grounding — keeps the label itself. The classification
    reflects the whole article (the prompt explicitly allows "the most
    representative passage" when no single sentence fits), so an unverified
    *quote* isn't grounds to discard the *label*.
  - `_dedupe_techniques()` collapses `(technique, quote)` pairs that became
    identical only after canonical normalization.
  - `pass1_word_count` (the quote-stripped Pass 1 text's word count) is now
    carried through to the stored record alongside `word_count`.
- **`stroemung_store.py`** (new, mirrors `technique_store.py`/`role_store.py`):
  `normalize_stroemung()` maps free-text labels onto the canonical taxonomy in
  `data/stroemungen.json` via embedding similarity. **Caught during testing:**
  naive semantic matching collapsed negated labels onto the concept they
  oppose (`antifeministisch` → `feministisch` at cosine distance 0.18,
  `islamkritisch` → `islamistisch` at 0.09 — both well inside the 0.35 match
  threshold). A marker-based guard (`anti`, `kritisch`, `gegner`, `feindlich`,
  `skeptisch`, `ablehnend`) skips semantic matching for any label built from
  one of these, at the cost of leaving some genuine synonyms
  (`marktwirtschaftlich`, `linksgrün`) unmapped — an acceptable false negative
  next to the alternative of silently inverting a label's meaning.
- **`db_storage.py`:** `bernays_score` now normalizes against
  `pass1_word_count`, falling back to `word_count` for records stored before
  this field existed.
- **`pass2.md` / frontend:** `dunning_kruger_index` gets a sibling
  `dunning_kruger_explanation` field (no schema break — the score stays a
  flat float) with a 1-2 sentence qualitative justification, shown in the
  article detail view. Deliberately *not* a verbatim-quote requirement:
  epistemic overconfidence is often a property of the article's overall tone,
  not one isolated sentence.

**Deliberately deferred — item 3.2 (mechanical interview-turn detection):**
the `Name: Antwort…` speaker-turn exclusion remains a prompt instruction only
(see [0008](0008-gemini-orwell-index-recalibration.md)'s "known limitation").
A regex-based mechanical strip risks false positives on non-interview
`Word: text` patterns (datelines, timestamps, editorial infixes) that would
silently remove real article text with no way to detect the mistake
afterwards — a materially different risk profile than the other fixes here,
which fail safe (keep the original value) rather than fail silently. Left for
a separate, narrower change.

## Consequences

- `GET /articles/{id}` now returns the `politische_stroemung` quote the
  frontend (`article-detail.component.html`) was already able to render.
- A DK-index of exactly `0.0` (maximal epistemic humility) is no longer
  indistinguishable from "not computed" in the API.
- `bernays_score` for quote-heavy articles (interviews, Q&A pieces) will
  generally read *higher* than before this change, since the denominator
  shrank to the text actually searched for techniques — this is a deliberate
  correction, not drift; historical records keep their old (lower) value
  until re-analysed, since they lack `pass1_word_count`.
- Regression coverage added in `tests/test_analyzer_json.py` for
  `_dedupe_techniques` and `_validate_stroemung_grounding`
  (`normalize_stroemung` itself isn't covered by the fast unit suite, same as
  `normalize_technique`/`normalize_role` — it needs a live embedding model and
  ChromaDB collection; verified manually against a local instance instead).
