# 0011 — Require a Verifiable Quote for Every Non-`neutral` politische_stroemung Label

**Date:** 2026-09-16 · **Status:** Active

## Context

[0009](0009-pipeline-hardening-after-gemini-meta-review.md) added
`_validate_stroemung_grounding`, but deliberately kept a label even when its
quote was missing or unverifiable — the reasoning at the time was that a
`politische_stroemung` classification reflects the whole article, not one
exact sentence, so an unevidenced *quote* shouldn't disqualify the
*classification* itself.

Comparing four repeated Qwen3-14B runs of the same article
(`gpt-oss`/local-model testing, see
[`politische_stroemung_pipeline_analysis.md`](../../analyses/politische_stroemung_pipeline_analysis.md)
§5) surfaced the cost of that leniency: `pass2.md` never actually required a
quote for non-`neutral` labels in the first place — only `neutral` had an
explicit `quote: null` allowance, everything else was phrased as a request
("provide... if no single sentence supports it, use the most representative
passage"), not an enforced rule. Nothing in the prompt or the validator
stopped the model from asserting `sozialdemokratisch` or `faschistisch` with
`quote: null` and having that survive untouched.

## Decision

- **`pass2.md`:** new *"Grounding rule (strictly enforced)"* under Politische
  Strömung — every label except `neutral` must carry a verbatim quote;
  `quote: null` is only valid for `neutral`.
- **`analyzer.py`'s `_validate_stroemung_grounding`:** a non-`neutral` label
  with a missing or unverifiable quote is now dropped entirely, not kept with
  `quote: null`. `neutral` remains exempt, matching the prompt's own
  allowance.

## Consequences

- An article can now end up with fewer `politische_stroemung` labels than the
  model originally proposed, or none beyond `neutral`, if none of its
  non-neutral claims were grounded — consistent with how
  `_validate_manipulation_target_grounding` already drops an entity with no
  surviving evidence, and with `manipulation_targets`' own prompt instruction
  ("If the article contains no such targeted framing anywhere, return an
  empty array").
- **This does not address the instability that motivated it.** Re-running
  the fix against the four already-captured Qwen runs changes nothing —
  every non-`neutral` label in all four already had a real, verifiable quote.
  The observed swing (`neutral` / `konservativ`+`sozialdemokratisch` /
  `neutral` / `sozialdemokratisch`+`neutral`) was the model applying
  different ideological labels to the same or a near-identical passage
  across runs, not an absence of evidence — grounding can only check that a
  quote *exists*, not that the model labels it *consistently*. That gap
  remains open; see the analysis doc for the full writeup.
