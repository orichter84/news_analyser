# 0005 — Quote Amplification Index as a Second Source for orwell_index

**Date:** 2026-09-06/07 (`e00d07e`) · **Status:** Active

## Context

A taz article scored `orwell_index: 0` despite covering a topic with clear enemy-image
content, while a comparable DW article covering a similarly one-sided topic scored
`0.75`. Investigation traced this to [0001](0001-pass0-group-detection-and-quote-stripping.md):
Pass 1 deliberately excludes quoted material, so an article that builds its enemy
image mainly through *which* extreme quotes it chooses to platform (rather than the
author's own sentences) was invisible to the Orwell Index — even though Pass 2 already
had rules for judging selective quoting (`target_direction`, `manipulation_targets`),
those never fed into `orwell_index`.

**Rejected alternative:** coupling `orwell_index` to the `detected_techniques` count
(a floor like "6+ techniques → orwell_index ≥ 0.6") was proposed and implemented, then
reverted before merging — it broke the intentional orthogonality between Bernays Score
and Orwell Index established in [0003](0003-separate-bernays-and-orwell-metrics.md).
Many small, low-intensity techniques should not force a high extremism score.

## Decision

Add `quote_amplification_index` as a new Pass 2 output — scored on the full original
text, measuring how much the article's *selection* of quoted material amplifies
extreme or one-sided rhetoric without context or rebuttal. Merge:

```
orwell_index = max(orwell_index_structural, quote_amplification_index)
```

Both sub-scores are kept in `framing_target` for transparency and surfaced in the
article detail view.

## Consequences

- An article can now score as extreme purely through its quoting choices, even when
  the author's own sentences are neutral.
- Required a corresponding exception to Pass 2's "quoted material must be excluded
  from all assessments" rule — this one field deliberately looks at quote content.
- See [cato_pattern.md](../proposals/cato_pattern.md) for a related, not-yet-decided
  proposal this investigation led to (cross-article recurrence of the same role,
  independent of quote amplification within a single article).
