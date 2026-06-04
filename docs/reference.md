# Technical Reference

This document covers the analysis output schema, indicators, paywall detection and the techniques database.

For architecture and design decisions see [analyse_architektur.md](analyse_architektur.md).  
For API endpoints and frontend structure see [web_architecture.md](web_architecture.md).

---

## Analysis Output (JSON)

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
    "dunning_kruger_index": 0.35
  },
  "politische_stroemung": ["konservativ", "nationalpopulistisch"],
  "themenbereich": "Politik",
  "manipulation_targets": [
    {
      "entity": "Bundesregierung",
      "direction": "negativ",
      "direction_quote": "exact quote supporting reader attitude, or null",
      "rolle": "Täter",
      "rolle_quote": "exact quote supporting the narrative function, or null"
    }
  ]
}
```

---

## Indicators

| Indicator | Range | Description |
|---|---|---|
| `orwell_index` | 0.0 – 1.0 | Rhetorical extremism. 0 = factual, 1 = highly manipulative |
| `bernays_score` | 0.0 – ∞ | Manipulation techniques per 1000 words |
| `dunning_kruger_index` | 0.0 – 1.0 | How confidently a text is written without being backed by sources, subjunctive mood or qualifications |
| `politische_stroemung` | Labels | Ideological classification (multiple possible): `liberal`, `konservativ`, `sozialdemokratisch`, `sozialistisch`, `nationalistisch`, `grün`, etc. |
| `themenbereich` | Category | Thematic classification: Politik, Wirtschaft, Technologie, … |
| `manipulation_targets` | List | Entities with direction (positiv/negativ/neutral), role (Sündenbock, Opfer, Held, Feind, Bedrohung, Autorität, Nutznießer, Versager, Täter, Sonstiges) and optional quote evidence |

For the design rationale behind these indicators see [analyse_architektur.md](analyse_architektur.md).

---

## Paywall Detection

Two-stage:
1. **HTML markers** — Piano/TinyPass script URLs (`cdn.tinypass.com`), CSS classes (`paywall`, `piano`, `c-piano`, `spplus`, `z-paywall`, `faz-premium`, etc.)
2. **Word count fallback** — Articles with < 150 words are flagged as paywall teasers

Paywalled articles are neither analysed nor stored.

---

## Techniques Database

19 documented manipulation techniques are defined in `src/news_analyser/data/techniques.json` and automatically seeded into ChromaDB (`techniques` collection) on first start. The collection lives in `data/` and is not pushed to the repository — the source data in `techniques.json` is versioned and enables automatic restoration.

During analysis, LLM free-text output is semantically mapped to canonical names (cosine similarity, threshold 0.35). New techniques can be added by extending `techniques.json`.

Categories: **Emotional** (Appeal to Fear, Bandwagon, Appeal to Emotion), **Logical** (Ad Hominem, Straw Man, False Dichotomy, Slippery Slope, Cherry Picking), **Rhetorical** (Loaded Language, Whataboutism, Euphemismus, Dysphemismus, Appeal to Authority, Presuppositional Framing), **Structural** (Framing, Agenda Setting, False Balance, Scapegoating, Repetition).
