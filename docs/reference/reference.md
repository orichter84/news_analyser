# Technical Reference

This document covers the analysis output schema, indicators, paywall detection and the techniques database.

For architecture and design decisions see [analyse_architektur.md](analyse_architektur.md).  
For API endpoints and frontend structure see [web_architecture.md](web_architecture.md).

---

## Analysis Output (JSON)

This is the raw output of `analyze_article()` (`src/news_analyser/agents/analyzer.py`) — what gets stored in ChromaDB. The list/detail HTTP API (`backend/routers/articles.py`, `search.py`) reshapes some fields for the frontend; see the note after the example.

```json
{
  "source_url": "https://...",
  "domain": "spiegel.de",
  "title": "Article title",
  "author": "Name",
  "published_at": "2026-05-26T10:00:00Z",
  "word_count": 850,
  "detected_techniques": [
    {
      "technique": "Appeal to Fear",
      "quote": "exact text quote",
      "explanation": "explanation of the effect"
    }
  ],
  "framing_target": {
    "main_narrative": "Central thesis of the article",
    "intended_sentiment": "Fear | Outrage | Approval | …",
    "orwell_index": 0.42,
    "orwell_index_structural": 0.2,
    "quote_amplification_index": 0.42,
    "dunning_kruger_index": 0.35,
    "target_direction": "who or what is elevated (+) or denigrated (-) and how, in German"
  },
  "politische_stroemung": [
    {"label": "konservativ", "quote": "exact quote supporting this label, or null"},
    {"label": "nationalpopulistisch", "quote": "exact quote supporting this label, or null"}
  ],
  "themenbereich": "Politik",
  "manipulation_targets": [
    {
      "entity": "Bundesregierung",
      "direction": "negativ",
      "direction_quote": "exact quote supporting reader attitude, or null",
      "rolle": "Täter",
      "rolle_quote": "exact quote supporting the narrative function, or null"
    }
  ],
  "llm_provider": "anthropic",
  "llm_model": "claude-..."
}
```

**`orwell_index` is a merge of two independent signals**, computed in `analyzer.py` after both passes finish:
- `orwell_index_structural` — Pass 1's own assessment, on the anonymised, quote-stripped text (the author's own voice only)
- `quote_amplification_index` — Pass 2's assessment of how much the article's *selection* of quoted material amplifies extreme or one-sided rhetoric, on the full original text
- `orwell_index = max(orwell_index_structural, quote_amplification_index)` — an article can score as extreme through its quoting choices alone, even if the author's own sentences are neutral

**Differences in the HTTP API:**
- `politische_stroemung` is flattened to a plain list of label strings (`["konservativ", "nationalpopulistisch"]`) for `GET /articles`, `GET /articles/{id}` and `GET /search` — the per-label `quote` evidence shown above is only present in the stored/pipeline record, not in the API response.
- `bernays_score` is **not** part of this pipeline output at all. It is computed afterwards, when the result is stored (`len(detected_techniques) / word_count * 1000`, see `src/news_analyser/repositories/db_storage.py:70-72`), and only then appears as a top-level field on the stored record and in the API responses.

---

## Indicators

| Indicator | Range | Description |
|---|---|---|
| `orwell_index` | 0.0 – 1.0 | Rhetorical extremism. 0 = factual, 1 = highly manipulative. `max(orwell_index_structural, quote_amplification_index)` — see below |
| `orwell_index_structural` | 0.0 – 1.0 | Pass 1 sub-score: the author's own rhetorical voice, on anonymised/quote-stripped text |
| `quote_amplification_index` | 0.0 – 1.0 | Pass 2 sub-score: how much the article's quote *selection* amplifies extreme or one-sided rhetoric, on the full original text |
| `bernays_score` | 0.0 – ∞ | Manipulation techniques per 1000 words — computed downstream at storage time, not part of the LLM output itself (see below) |
| `dunning_kruger_index` | 0.0 – 1.0 | How confidently a text is written without being backed by sources, subjunctive mood or qualifications |
| `politische_stroemung` | Labels + quote | Ideological classification (multiple possible): `liberal`, `konservativ`, `sozialdemokratisch`, `sozialistisch`, `nationalistisch`, `grün`, etc. Each label carries a supporting verbatim quote in the pipeline output (flattened to plain labels in the HTTP API) |
| `target_direction` | Free text (German) | Nested inside `framing_target`. One-sentence summary of who/what the article elevates or denigrates and how |
| `themenbereich` | Category | Thematic classification: Politik, Wirtschaft, Technologie, … |
| `manipulation_targets` | List | Entities with direction (positiv/negativ/neutral), role (Sündenbock, Opfer, Held, Feind, Bedrohung, Autorität, Nutznießer, Versager, Täter, Sonstiges) and optional quote evidence |

For the design rationale behind these indicators see [analyse_architektur.md](analyse_architektur.md).

---

## Paywall Detection

Two-stage:
1. **HTML markers** — Piano/TinyPass script URLs (`cdn.tinypass.com`), CSS classes and IDs (`paywall`, `spplus`, `z-paywall`, `faz-premium`, etc.)
2. **Word count fallback** — Articles with < 150 words are flagged as paywall teasers

Paywalled articles are neither analysed nor stored.

---

## Techniques Database

28 documented manipulation techniques are defined in `src/news_analyser/data/techniques.json`. They are **not** seeded at application startup — `_ensure_seeded()` (`src/news_analyser/repositories/technique_store.py:52`) runs lazily on the first call to `normalize_technique()` or `get_all_techniques()`, populating the ChromaDB `techniques` collection at that point. The collection lives in `data/` and is not pushed to the repository — the source data in `techniques.json` is versioned and enables automatic restoration.

During analysis, LLM free-text output is semantically mapped to canonical names (cosine similarity, threshold 0.35). Only 18 of the 28 techniques are offered to the LLM as explicit options in the Pass 1 prompt (those flagged `"prompt": true` in `techniques.json`); the remaining 10 — including "Appeal to Fear", the example used above — are reachable only via semantic normalization of the LLM's free-text output. New techniques can be added by extending `techniques.json`.

Categories:
- **Emotional** (5): Appeal to Fear, Emotional Manipulation, Bandwagon, Appeal to Emotion, Halo Effect
- **Structural** (9): Selective Empathy, Omission, Scapegoating, Victim Framing, Agenda Setting, Framing, False Balance, Repetition, Anchoring
- **Rhetorical** (7): Whataboutism, Loaded Language, Euphemismus, Dysphemismus, Appeal to Authority, Presuppositional Framing, Exaggeration
- **Logical** (7): Cherry Picking, False Dichotomy, Ad Hominem, Straw Man, Slippery Slope, False Cause, Overgeneralization
