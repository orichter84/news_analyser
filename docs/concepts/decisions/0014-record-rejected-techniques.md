# 0014 — Record Rejected Techniques as a Reliability Signal

**Date:** 2026-10-09 · **Status:** Active

## Context

Before a technique reported by Pass 1 counts towards the Bernays Score, two checks
run on it. `_validate_quote_grounding` drops instances whose quote is empty, doesn't
occur in the quote-stripped Pass 1 text, or is reported more often than it occurs.
`_dedupe_techniques` then collapses instances that became identical only after
`normalize_technique`. Both checks discarded the dropped instances completely. The
only trace was an INFO log line with a count, and no URL. The raw response in
`data/debug_runs/` also contained them, but that isn't something you can browse.

It is correct that only verified techniques count towards the score. How many get
rejected is still useful information. It indicates how reliable the technique
detection is. A rising rejection rate means the model is inventing or misquoting
passages, and that is a signal that `pass1.md`, or the choice of model, needs work.
None of this was recorded.

## Decision

- Both checks take an optional `rejected` list and add one
  `{technique, quote, reason}` entry for every instance they drop. The reason codes
  are `empty_quote`, `quote_not_found`, `occurrence_exceeded` and `duplicate`.
  Rejected technique names go through `normalize_technique` like the accepted ones,
  so the rejections can be added up per canonical technique.
- `analyze_article` adds a new top-level field to its output:
  `technique_validation = {reported, accepted, rejected[]}`. `reported` is the number
  of instances in the raw Pass 1 response, `accepted` is
  `len(detected_techniques)`, which is the count the Bernays Score uses, and
  `reported = accepted + len(rejected)`.
- `db_storage._flatten_metadata` also stores `techniques_reported` and
  `techniques_rejected` as flat ChromaDB metadata, so they can be filtered and
  aggregated later without parsing `analysis_json`. Records from before this decision
  get `-1`, which means "not recorded" and is distinct from `0` ("nothing rejected").
- The article detail view (`/articles/{url}`) shows on the Bernays Score card how
  many of the reported techniques were verified and how many were rejected, with the
  rejection rate. The rate is highlighted from 30 % upwards. Below the detected
  techniques, a collapsible list shows every rejected instance with its quote and
  the reason in German. Older articles show "Nachprüfung nicht erfasst".

## Consequences

- The Bernays Score itself is unchanged. It still counts only `accepted` instances.
- Only articles analysed after this change have the data. Re-analysing an article
  (`force`) fills it in.
- Not yet covered: the Pass 2 grounding checks (`manipulation_targets`,
  `politische_stroemung`) still drop silently, and there is no aggregated rejection
  rate per provider or model in the statistics pages. The flat
  `techniques_rejected` metadata field is the hook for the latter.
- Regression coverage: `TestRejectedTechniquesAreRecorded` in
  `tests/test_analyzer_json.py`.
