# Fact-Check Pass — Concept

## Core Idea

Extract verifiable claims from an article as semantic triples
(Subject – Relation – Object) and cross-check them against external sources.

This adds a factual dimension to the existing scoring:
- **Bernays Score** — manipulation technique density
- **Orwell-Index** — language opacity
- **DK-Index** — confidence/knowledge gap signals
- **Fact Score** *(new)* — ratio of verifiable claims with external support

---

## Pipeline Position

Runs after Pass 1 (technique analysis) as an optional Pass 3:

```
Pass 0 — Term detection (NER)
Pass 1 — Anonymised technique analysis
Pass 2 — Political leaning
Pass 3 — Fact-check (new, optional)
```

---

## Triple Extraction

An LLM pass extracts "flat facts" — the core verifiable claims of the article —
as structured triples:

```json
[
  {"subject": "Entität A", "relation": "tut/ist/hat", "object": "Entität B"}
]
```

**Extraction rules:**
- Only entities central to the information content (persons, organisations, events, figures)
- Relations as concise active verbs
- Causal claims broken into separate verifiable triples
- Output: valid JSON only, no prose

---

## Verification

Each triple is checked against external sources (search API or curated feeds):

| Result | Interpretation |
|---|---|
| Multiple reputable sources confirm | High confidence |
| No sources found | Unverifiable — not necessarily false |
| Sources contradict | Low confidence |

> **Important:** absence of search results is not proof of a false claim.
> Treat it as an *unverifiability signal*, not a falsification.

---

## Fact Score

A soft score based on the verification results — not a binary pass/fail:

```
Fact Score = confirmed_triples / total_triples
```

Unverifiable triples count as neutral (0.5), not as false (0).
The score is shown alongside the other indices, not used to override them.

---

## Integration Notes

- Search API calls add latency — run asynchronously or on demand, not per default
- German-language search quality varies by API; curated news feeds may be more reliable
- The DK-Index already captures confidence signals; Fact Score complements it with
  external grounding rather than duplicating it

---

## ToDo

- [ ] Design Pass 3 prompt for triple extraction (German)
- [ ] Evaluate search API options (Brave, SerpAPI, curated RSS feeds)
- [ ] Define Fact Score formula and weight relative to other indices
- [ ] Add Fact Score to final result output and UI
