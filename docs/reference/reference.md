# Technical Reference

This document covers the analysis output schema, indicators, paywall detection and the techniques database.

For architecture and design decisions see [analyse_architektur.md](analyse_architektur.md).  
For API endpoints and frontend structure see [web_architecture.md](web_architecture.md).  
For the general prompting techniques behind `pass1.md`/`pass2.md` see [prompting_patterns.md](prompting_patterns.md).

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
  "pass1_word_count": 720,
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
    "quote_amplification_explanation": "1-2 sentences naming which quote(s) drive the score, in German, or null below 0.3",
    "dunning_kruger_index": 0.35,
    "dunning_kruger_explanation": "1-2 sentence justification of the score, in German",
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

**Grounding & normalization applied between the passes and storage** (`analyzer.py`):
- `detected_techniques` — quotes are verified against the quote-stripped Pass 1 text (`_validate_quote_grounding`); unverifiable instances are dropped. Technique names are then mapped onto the canonical list (`normalize_technique`), and instances that became identical `(technique, quote)` pairs only after that mapping are collapsed (`_dedupe_techniques`) so a passage isn't double-counted under two raw labels that normalize to the same technique.
- `manipulation_targets` — `rolle`/`direction` without a verifiable supporting quote are cleared (`_validate_manipulation_target_grounding`); an entity with neither field grounded is dropped entirely.
- `politische_stroemung` — labels are mapped onto the canonical taxonomy (`normalize_stroemung`, semantic match; labels built from a negation/critical marker like "anti-"/"-kritisch" are deliberately left unmapped rather than risking a match to the concept they oppose). A label's `quote` is nulled if it can't be found in the original article text (`_validate_stroemung_grounding`) — the label itself is kept even without a verified quote, since the classification reflects the whole article rather than one sentence.
- `dunning_kruger_index` has no quote-grounding — it ships with a qualitative `dunning_kruger_explanation` instead (see Indicators below), not a verbatim excerpt requirement.
- `quote_amplification_index` also has no code-level grounding: `quote_amplification_explanation` is a prompt instruction (required above 0.3), not a value `analyzer.py` validates or uses to cap the score.

**Differences in the HTTP API:**
- `politische_stroemung` is flattened to a plain list of label strings (`["konservativ", "nationalpopulistisch"]`) for `GET /articles` and `GET /search`. **`GET /articles/{id}` (detail) preserves the `{label, quote}` objects** from the stored `analysis_json` so the per-label quote evidence is available to the frontend.
- `bernays_score` is **not** part of this pipeline output at all. It is computed afterwards, when the result is stored: `len(detected_techniques) / pass1_word_count * 1000` (see `src/news_analyser/repositories/db_storage.py`) — normalized against the length of the quote-stripped text Pass 1 actually saw, not the full article's `word_count` (records stored before `pass1_word_count` existed fall back to `word_count`). It appears as a top-level field on the stored record and in the API responses.

---

## Indicators

| Indicator | Range | Description |
|---|---|---|
| `orwell_index` | 0.0 – 1.0 | Rhetorical extremism. 0 = factual, 1 = highly manipulative. `max(orwell_index_structural, quote_amplification_index)` — see below |
| `orwell_index_structural` | 0.0 – 1.0 | Pass 1 sub-score: the author's own rhetorical voice, on anonymised/quote-stripped text |
| `quote_amplification_index` | 0.0 – 1.0 | Pass 2 sub-score: how much the article's quote *selection* amplifies extreme or one-sided rhetoric, on the full original text |
| `quote_amplification_explanation` | Free text (German) | Nested inside `framing_target`. Required (per the prompt) above 0.3: names the specific quote(s) driving the score. No code-level grounding check — a prompt instruction, not an enforced constraint |
| `bernays_score` | 0.0 – ∞ | Manipulation techniques per 1000 words of the quote-stripped Pass 1 text (`pass1_word_count`) — computed downstream at storage time, not part of the LLM output itself (see below) |
| `dunning_kruger_index` | 0.0 – 1.0 | How confidently a text is written without being backed by sources, subjunctive mood or qualifications |
| `dunning_kruger_explanation` | Free text (German) | Nested inside `framing_target`. 1-2 sentence qualitative justification for the DK score — no quote-grounding requirement, since overconfidence is often a property of the article's overall tone rather than one sentence |
| `politische_stroemung` | Labels + quote | Ideological classification (multiple possible), normalized onto a canonical taxonomy (`liberal`, `konservativ`, `sozialdemokratisch`, `sozialistisch`, `nationalistisch`, `grün`, … — see `src/news_analyser/data/stroemungen.json`; the LLM may still coin new labels the taxonomy doesn't cover). Each label carries a supporting verbatim quote in the pipeline output, nulled if unverifiable against the source text; flattened to plain labels only in the list/search HTTP API, preserved in the detail endpoint |
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
