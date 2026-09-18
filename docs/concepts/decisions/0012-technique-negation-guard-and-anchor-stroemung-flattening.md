# 0012 — Extend the Negation Guard to Technique Normalization; Fix Anchor politische_stroemung Storage

**Date:** 2026-09-18 · **Status:** Active

## Context

Two new debug notebooks
([`normalization_check.ipynb`](../../../notebooks/normalization_check.ipynb),
[`anchor_store_inspection.ipynb`](../../../notebooks/anchor_store_inspection.ipynb))
surfaced two real bugs, both variations on issues already fixed elsewhere in
[0009](0009-pipeline-hardening-after-gemini-meta-review.md):

1. **`normalize_technique` had the same negation-collapse bug** that
   `normalize_stroemung` was patched against in 0009. Confirmed directly:
   `"anti-Appeal to Fear"` → `"Appeal to Fear"`,
   `"Emotional Manipulation-kritisch"` → `"Emotional Manipulation"`. The guard
   had only ever been added to `stroemung_store.py`; `technique_store.py` used
   the same embedding-similarity approach without it.  `normalize_role`
   (difflib-based, not embeddings) does not share this failure mode — 0 hits
   across 50 generated negation/critical-prefix test cases.
2. **`anchor_store.add_anchor()` stored `politische_stroemung` unflattened.**
   Its type hint said `list[str]`, but `analyzer.py` passes the field through
   exactly as Pass 2 returns it — `list[dict]` with `{label, quote}` under the
   schema `pass2.md` has used since before 0009. `add_anchor()` `json.dumps()`d
   that list as-is, instead of extracting labels first the way
   `db_storage.py`'s `_extract_stroemung_labels()` already does for the
   top-level metadata. Confirmed empirically: `format_anchors_for_prompt()`
   embedded the raw JSON blob — including full quote text — directly into the
   Pass 1 calibration prompt (`Stroemung: [{"label": "antifaschistisch",
   "quote": "Es ist eine Gruppe, die Kinder in Zeltlagern..."}]`) instead of a
   clean label list.

## Decision

- New shared module **`repositories/negation_guard.py`**: extracts the
  marker list and `is_oppositional()` check out of `stroemung_store.py` (which
  now imports it) so `technique_store.normalize_technique()` can reuse the
  identical guard instead of duplicating it — this is the second store to need
  it, past the threshold where copy-pasting the marker list risks drift.
- **`technique_store.normalize_technique()`** now skips semantic matching for
  oppositional input, same as `normalize_stroemung`.
- **`anchor_store.add_anchor()`** flattens `politische_stroemung` via
  `db_storage._extract_stroemung_labels()` before storing.
- **`anchor_store.get_similar_anchors()`** also flattens on *read*, not just
  relying on the write-path fix — the 31 anchors already stored in the local
  dev DB predate this fix and are still in the broken dict-blob format;
  without a read-side fallback, retrieving one of them would raise
  `TypeError` inside `get_similar_anchors()` and take down Pass 1 entirely for
  any article whose RAG query happens to surface one. Verified against the
  existing local anchor collection: old anchors now render as clean labels
  (`Stroemung: sozialdemokratisch, grün`) with no migration needed — the fix
  is retroactive on read.

## Consequences

- Pass 1's dynamic calibration references now show clean labels instead of
  raw JSON, for both old and new anchors.
- No data migration was run against the existing anchor collection — the
  read-path fix makes one unnecessary. A fresh deployment's collection starts
  clean from the write-path fix.
- Regression coverage: `tests/test_negation_guard.py` (pure logic, no
  ChromaDB dependency). `normalize_technique`/`normalize_stroemung`/
  `add_anchor`/`get_similar_anchors` themselves remain outside the fast unit
  suite (need a live ChromaDB + embedding model) — verified manually instead,
  same as noted for `normalize_technique`/`normalize_role` in
  [`prompting_patterns.md`](../../reference/prompting_patterns.md).
