# 0002 — Abandon a Unified NER + Gender-Anonymisation Pass

**Date:** 2026-06-16 (`a957ad9`) · **Status:** Rejected / superseded

## Context

The `feature/gender_anonymization` branch attempted to fold group identification and
NER into a single unified LLM pass, additionally anonymising gender in the process.

## Decision

Abandoned after testing: a single combined pass was too aggressive and degraded
analysis quality (Bernays Score dropped from 3.92 to 3.26/1000w on the same test
corpus — the model was over-anonymising and losing signal it needed for technique
detection).

The existing prompt-level symmetry rule (role-reversal test in Pass 1, see
[pass1.md](../../../src/news_analyser/prompts/system/pass1.md)) was judged sufficient
for the gender dimension specifically, without a dedicated anonymisation step.

## Consequences

- Group detection (Pass 0) and NER-based anonymisation stayed as two separate,
  narrower steps rather than one broad pass — see
  [0001](0001-pass0-group-detection-and-quote-stripping.md).
- Full write-up and status kept at
  [`archive/anonymization_v2.md`](../../archive/anonymization_v2.md) for anyone
  revisiting this trade-off later.
