# 0007 — Require Grounding for manipulation_targets Rolle/Direction

**Date:** 2026-09-13 (`38e990c`) · **Status:** Active

## Context

Testing surfaced two related problems in `manipulation_targets`:

1. An entity ("wir"/"we") got `rolle: Opfer` + `direction: negativ` where the
   supporting quote only described a shared negative outcome ("we'll pay higher gas
   prices too"), not an evaluative framing — a situation, not an attitude. The
   existing calibration rules already warned against exactly this confusion, but only
   for the `Opfer` role specifically.
2. Separately, some entities carried a `rolle` or `direction` label with no
   supporting quote at all. Comparing providers: the `cli`/Claude adapter used the
   already-permitted `null` fallback ("no single passage clearly supports it")
   correctly and conservatively; Gemini never appeared to use that fallback, always
   producing *some* quote whether or not it actually fit. Unlike `detected_techniques`,
   `manipulation_targets` had no grounding validation at all.

## Decision

- **Prompt (`pass2.md`):** generalised the grounding requirement to every role, not
  just Opfer — whichever `rolle`/`direction` is assigned, the quote must demonstrate
  actual authorial judgment (blame, praise, mockery), not merely a neutral shared
  circumstance.
- **Code (`analyzer.py`):** new `_validate_manipulation_target_grounding()`, mirroring
  the existing `_validate_quote_grounding()` used for `detected_techniques`. Strips
  `rolle` or `direction` when the corresponding quote is missing or not found in the
  original text; drops the entity entirely only if neither survives.
- **Frontend:** `rolle`/`direction` are now nullable; a badge is only rendered when
  its value survived grounding, instead of always showing regardless of evidence.

## Consequences

- Enforced identically regardless of LLM provider — Gemini's tendency to always
  supply *a* quote no longer bypasses verification.
- Matters beyond the single-article view: unbelegte values would otherwise silently
  skew corpus-level aggregations that read `rolle`/`direction` directly, including
  `publisher_profiles()` and the proposed [Cato Pattern](../proposals/cato_pattern.md).
