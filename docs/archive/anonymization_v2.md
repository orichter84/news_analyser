# Anonymization v2 — Concept and Status

## Background

The branch `feature/gender_anonymization` was abandoned after testing.
Core problem: a unified LLM pass for NER + group identification was too aggressive
and degraded analysis quality (Bernays Score: 3.92 → 3.26/1000w).

The lessons learned were ported manually into master via `feature/anonymizer-v2`.

---

## What did not work

### Unified LLM Pass 0 (NER + groups)
- LLM misidentifies verbs as group terms: `"weiß"` (= to know) → `Gruppe-X`
- Inflection artifacts: `"deutschen"` → `"Gruppe-Hen Institutionen"`
- Too many placeholders fragment the Pass 1 context, reducing technique detection

### Grammar fixer (LLM)
- Articles with many kinship terms: 2+ minutes runtime
- Unreliable corrections when processing long sentence lists

### Gendered kinship term replacement (Python)
Ported from `feature/gender_anonymization` and later **removed** (2026-06-26).

Reason: Test 06 (bias-validation.md) showed that gender symmetry (Δ technique count = 1)
is achieved by the symmetry rule in the pass 1 prompt alone — without any anonymisation.
The kinship replacement caused context loss (specific names, identity markers needed for
Selective Empathy detection) without providing a measurable symmetry benefit.

Removed components:
- `GENDERED_KINSHIP_TERMS` list in `_normalizations.py`
- Kinship replacement loop in `SpacyStrategy.normalize()`
- `fix_article_agreement()` and `fix_pronouns()` calls in `SpacyStrategy.correct()`
- `_grammar.py` (retained as dead code for reference)

---

## Current architecture (as of 2026-06-26)

### Pipeline: SpacyStrategy

| Step | Method | Purpose |
|---|---|---|
| 1 | `normalize()` | Replace ideological terms (IDEOLOGICAL_TERMS) with neutral equivalents |
| 2 | `ner()` | spaCy NER: replace PER → Person-X, ORG → Org-X |
| 3 | `replace_groups()` | Replace group terms from Pass 0 output → Gruppe-X |
| 4 | `correct()` | No-op (grammar correction removed with kinship terms) |

### Pass 0 (group detection)

LLM-based identification of group identifiers per article. Returns a list of
`{term, type}` objects. Types currently detected:

- `racial` — perceived race or skin colour
- `ethnic_origin` — ethnic or national origin
- `religious` — religious affiliation
- `gender_identity` — non-binary / transgender identities
- `sexual_orientation` — sexual orientation
- `national_origin` — country of origin as group marker

**Not anonymised:** binary gender terms (Männer/Frauen, Jungen/Mädchen).
Rationale: see Test 06 in bias-validation.md — prompt symmetry rule is sufficient.

### Entity blocklist

Common nouns that spaCy incorrectly tags as PER are blocked in `_ENTITY_BLOCKLIST`:
- Political/abstract terms: Faschismus, Demokratie, Partei, …
- Kinship nouns: Sohn, Tochter, Vater, Mutter, Mann, Frau, … (added 2026-06-26
  to prevent false PER-tagging after kinship replacement was removed)

---

## Benchmark

| Date | Version | Technique instances | Bernays Score | Model |
|---|---|---|---|---|
| 2026-05-22 | v0.1 (pre-anonymisation) | 6 | 3.92/1000w | claude-sonnet-4-6 |
| 2026-06-26 | Current (no gender anon, improved prompt) | 15 | ~9.78/1000w | claude-sonnet-4-6 |

Source: taz.de "Männlichkeitsbilder in Schulen" (1535 words)

---

## Symmetry results (summary)

Full results in bias-validation.md.

| Bias type | Without anonymisation | With anonymisation | Verdict |
|---|---|---|---|
| Gender (Männer/Frauen) | Δ = 1 ✅ | — (removed) | Prompt rule sufficient |
| Group/ethnicity (Muslime/Westeuropäer) | Δ = 4 ⚠ | Δ = 0 ✅ | Anonymisation needed |

---

## ToDo

- [x] Port kinship terms from feature branch
- [x] Port article agreement correction
- [x] Port pronoun replacement
- [x] Port debug notebook (`notebooks/anonymizer_debug.ipynb`)
- [x] Restrict Pass 0 to group types only (no binary gender)
- [x] Regression test: benchmark ≥ 6 technique instances — exceeded (15)
- [ ] Curate group word lists as fallback for Pass 0 LLM failures
- [ ] UI progress indicator (pipeline steps): detecting terms → anonymising → analysing
- [ ] Implement `AdaptiveStrategy` with LLM-based `replace_groups()` for high-risk topics
