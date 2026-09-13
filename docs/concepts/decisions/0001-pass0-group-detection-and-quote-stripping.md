# 0001 — Pass 0 Group Detection + Quote Stripping for a Group-Blind Pass 1

**Date:** 2026-06 (iterative, see `group_detector.py` introduced 2026-06-04,
refined through 2026-07-09) · **Status:** Active

## Context

Early testing showed the LLM's own training bias leaking into the extremism/technique
analysis: identical rhetorical patterns scored differently depending on which group was
mentioned. Prompt-engineering alone ("please be unbiased") did not reliably fix this —
see [bias-validation.md](../validation/bias-validation.md) for the symmetry tests that
demonstrated the problem.

Separately, a sachlich reported article was mis-scored as manipulative because Pass 1
picked up an extreme quote from a third party (e.g. an interviewee) and attributed the
rhetoric to the article itself.

## Decision

- **Pass 0**: an LLM pass identifies explicit human-group identifiers in the original
  text before any scoring happens.
- **Anonymisation**: spaCy NER (persons, organisations) plus the Pass-0 group terms are
  replaced with neutral placeholders (`Akteur_A`, `Status_X`, …) before Pass 1 sees the
  text — removing the bias structurally rather than suppressing it by instruction.
- **Quote stripping**: direct quoted speech is mechanically removed from Pass 1's input
  (replaced with `[…]`), so Pass 1 only ever judges the author's own voice. Selective
  quoting bias is judged separately, in Pass 2, on the full original text.

## Consequences

- Pass 1 is model-independent by construction — the bias is excluded before the LLM
  call, not suppressed by asking nicely.
- This creates a structural gap: extremity that only exists in *which* quotes an
  article chooses to platform is invisible to Pass 1. See
  [0005](0005-quote-amplification-index.md) for how that gap was later addressed.
- The DK-Index is deliberately measured in Pass 2, on the *original* (non-anonymised)
  text — see [analyse_architektur.md](../../reference/analyse_architektur.md) for why
  that pass doesn't need the same anonymisation protection.
