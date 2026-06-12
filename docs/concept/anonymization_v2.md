# Anonymization v2 — Concept and Roadmap

## Background

The branch `feature/gender_anonymization` was abandoned after testing.
Core problem: a unified LLM pass for NER + group identification was too aggressive
and degraded analysis quality (Bernays Score: 3.92 → 3.26/1000w).

### Benchmark Reference (taz Männlichkeit article)

| Version | Technique instances | Bernays Score |
|---|---|---|
| Gemini gender-swap (ideal) | 7 | — |
| Master (current) | 6 | 3.92/1000w |
| feature/gender_anonymization | 5 | 3.26/1000w |

---

## What did not work

### Unified LLM Pass 0 (NER + groups)
- LLM misidentifies verbs as group terms: `"weiß"` (= to know) → `Gruppe-X`
- Inflection artifacts: `"deutschen"` → `"Gruppe-Hen Institutionen"`
- Too many placeholders fragment the Pass 1 context, reducing technique detection

### Grammar fixer (LLM)
- Articles with many kinship terms: 2+ minutes runtime
- Unreliable corrections when processing long sentence lists

---

## What worked (to be ported)

These components from the feature branch are complete and tested:

### Python kinship term replacement
Neutralises gendered family terms without loss of meaning:
- `Sohn/Töchter` → `Kind/Kinder`
- `Vater/Mutter` → `Elternteil/Elternteile`
- `Mann/Frau` → `Erwachsener/Erwachsene`
- `Bruder/Schwester` → `Geschwister`
- Full list in `anonymizer.py` `GENDERED_KINSHIP_TERMS`

### Python article agreement correction
Deterministically fixes grammatical gender after kinship replacement:
- `der/einen/meinen Kind` → `das/ein/mein Kind`
- `die/eine/meine Kind` → `das/ein/mein Kind`
- `einen tollen Erwachsener` → `einen tollen Erwachsenen`

### Python pronoun replacement
In sentences containing `Person-X` placeholders:
- `er/ihn/ihm` → `sie/sie/ihr`
- `sein/seine/seinen/seinem` → `ihr/ihre/ihren/ihrem`

---

## New approach (v2)

### Principle: curated lists > LLM for group identification

| Layer | Method | Purpose |
|---|---|---|
| NER (PER/ORG/LOC) | LLM Pass 0 | Named entities — LLM remains reliable here |
| Groups | Curated lists | No LLM, no risk of verb misidentification |
| Kinship terms | Python (GENDERED_KINSHIP_TERMS) | Deterministic, fast |
| Grammar fix | Python (articles + pronouns) | No LLM pass needed |

### Group detection without LLM
Instead of LLM: word lists similar to `IDEOLOGICAL_TERMS`, split by category:
- Racial / ethnic terms
- Gender role terms (Jungs, Mädchen etc.)
- Religious designations

---

## Fallback: Adaptive Strategy

If the curated-list approach does not reach the benchmark (≥ 6 technique instances),
the `replace_groups()` step can be escalated to an LLM selectively.

### Trigger: topic-based detection

Topic keywords are checked on the raw text before anonymization — no extra LLM call needed.

```python
_LLM_TOPICS: set[str] = {
    "feminismus", "feministische", "gender", "männlichkeit",
    "rassismus", "migration", "islamophobie",
}

def _needs_llm(text: str) -> bool:
    text_lower = text.lower()
    return any(topic in text_lower for topic in _LLM_TOPICS)
```

### Why not use Bernays Score / Orwell-Index as trigger?

These indicators are produced by Pass 1 — after anonymization has already run.
They cannot influence the current article's strategy. Possible use: trigger a
**second pass** with LLM strategy if the first result looks suspicious.

### Architecture

`AdaptiveStrategy` wraps `SpacyStrategy` and `LLMStrategy`. Only `replace_groups()`
is escalated — `normalize()`, `ner()`, and `correct()` always use the spaCy path.

```
AdaptiveStrategy
  ├── normalize()       → SpacyStrategy (always)
  ├── ner()             → SpacyStrategy (always)
  ├── replace_groups()  → SpacyStrategy / LLMStrategy (topic-dependent)
  └── correct()         → SpacyStrategy (always)
```

---

## ToDo

- [ ] Port kinship terms from feature branch (`GENDERED_KINSHIP_TERMS`)
- [ ] Port article agreement correction (`_fix_article_agreement`)
- [ ] Port pronoun replacement (`_replace_pronouns`)
- [ ] Restrict Pass 0 prompt to NER (PER/ORG/LOC) only — remove group detection
- [ ] Curate group word lists (racial, gender_role, religious etc.)
- [ ] Port debug notebook (`notebooks/ner_debug.ipynb`)
- [ ] UI progress indicator (pipeline steps): detecting terms → anonymising → analysing
- [ ] Regression test: benchmark ≥ 6 technique instances on taz Männlichkeit article
