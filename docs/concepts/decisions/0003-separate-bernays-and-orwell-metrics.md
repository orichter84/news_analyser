# 0003 — Separate Bernays Score and Orwell Index as Independent Metrics

**Date:** 2026-05-22 (`91d140f`, `0e5ba7c`) · **Status:** Active

## Context

The original single "bias_score" conflated two different things: how rhetorically
extreme a text is, and how densely it uses manipulation techniques. A text can be
calm in tone but technique-dense (many small nudges), or intensely emotional with few
distinct techniques — collapsing both into one number hid that distinction.

## Decision

Split into two orthogonal, independently-computed metrics:

- **Orwell Index** — rhetorical extremism strength (LLM judgment, direction-neutral)
- **Bernays Score** — `detected_techniques.length / word_count * 1000` (a mechanical
  density calculation, not an LLM judgment)

Renamed from the original `bias_score` naming to make the two-dimensional nature
explicit rather than implying a single "bias" scalar.

## Consequences

- A text can legitimately score high on one and low on the other — this is
  intentional, not a bug (see
  [analyse_architektur.md](../../reference/analyse_architektur.md)).
- This orthogonality was later a reason to *reject* a proposed fix that would have
  coupled `orwell_index` to the `detected_techniques` count (tried and reverted
  2026-09, see the Quote Amplification Index work in
  [0005](0005-quote-amplification-index.md) for what was built instead).
