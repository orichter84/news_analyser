# 0004 — Add the Dunning-Kruger Index

**Date:** 2026-05-22 (`cf104a2`, `df0d421`) · **Status:** Active

## Context

Neither the Orwell Index (rhetorical extremism) nor the Bernays Score (technique
density) captures epistemic overconfidence — a text can be calm and technique-light
while still making bold, unsupported, absolute claims. This is a distinct dimension
of manipulative writing worth measuring on its own.

## Decision

Add a third, independent indicator: the Dunning-Kruger Index, measuring the ratio of
definitive claims to their evidential backing (sources, hedges, qualifications),
computed in Pass 2 on the original (non-anonymised) text.

## Consequences

- Confirmed group-blind by construction and by symmetry testing — epistemic
  overconfidence is grammatically/structurally determined, not tied to which group is
  discussed (zero difference between mirrored texts in
  [bias-validation.md](../validation/bias-validation.md)).
- This is why it's the one indicator measured in Pass 2 without needing the Pass 0/1
  anonymisation protection — see
  [0001](0001-pass0-group-detection-and-quote-stripping.md).
