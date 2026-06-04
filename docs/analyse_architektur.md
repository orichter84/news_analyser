# Analysis Architecture: Indicators and Stabilisation Concept

## Problem

The Orwell Index was initially estimated exclusively by the LLM and measured two
conceptually distinct things on a single axis: **extremism** and **political direction**.
This led to three weaknesses:

1. **Conceptual error:** An AfD article and an Antifa article received different
   Orwell values even though they can be rhetorically equally extreme.
2. **No intersubjective standard:** The model implicitly defined "neutral" through its training.
3. **Model drift:** When switching models, calibration shifted without warning.

---

## Target Schema: Four Orthogonal Values

| Value | Measures | Type | Scale |
|---|---|---|---|
| **Bernays Score** | Manipulation intensity (techniques / 1000 words) | `float` | 0 → ∞ |
| **Orwell Index** | Extremism / dystopian rhetoric | `float` | 0.0 (factual) → 1.0 (extreme) |
| **Dunning-Kruger Index** | Unsubstantiated certainty / epistemic overconfidence | `float` | 0.0 (qualified) → 1.0 (assertive without evidence) |
| **Political Leaning** | Named ideological tendency/tendencies | `list[str]` | Label(s) |

Each value measures an independent dimension. A text can score high on Bernays Score (many techniques) while scoring low on the Orwell Index (moderate rhetoric). Similarly, a text can have high epistemic overconfidence (DK Index) without being politically extreme. The four values together give a multi-dimensional profile of a text's manipulative character.

### Why the Dunning-Kruger Index is orthogonal

The DK Index captures how confidently a text makes claims without backing them with sources, subjunctive mood, or qualifications — regardless of which group or ideology is the subject. A text that states *"vaccines cause autism"* and one that states *"immigration destroys our culture"* can both score equally high on the DK Index even though they are politically opposite. This group-blindness is by design and confirmed by symmetry tests: DK values show zero difference between mirrored texts on real articles (see [bias-validation](concept/bias-validation.md)).

### Why labels instead of a numerical axis for direction?

A numerical left/right axis fails on historical and modern hybrid phenomena.
The NSDAP combined socialist worker rhetoric with nationalism — on a scale
that would be either misleadingly "neutral" or arbitrarily placed. With labels the
classification is honest: `["sozialistisch", "nationalistisch"]`.

The same applies to modern phenomena:
- BSW: `["sozialistisch", "nationalpopulistisch"]`
- CSU: `["konservativ", "christdemokratisch"]`
- FDP: `["liberal", "marktwirtschaftlich"]`

The LLM is trained for exactly this kind of reasoned classification and delivers
more traceable results than a number between -1.0 and +1.0.

### Example label taxonomy

*liberal, konservativ, christdemokratisch, sozialdemokratisch, grün, sozialistisch,
kommunistisch, nationalistisch, nationalpopulistisch, libertär, faschistisch, anarchistisch*

The list is not exhaustive — the LLM can combine labels and coin new ones as needed.
Multiple labels per article are explicitly encouraged.

---

## Three-Stage Pipeline for Orwell Index Stabilisation

```
Text → [1] Keyword signal     (extremism indicator, 0.0–1.0)
     → [2] Embedding search   (RAG, dynamic calibration anchors)
     → [3] LLM estimation     (detect adversarial framing, final scoring)
```

No single signal is reliable on its own. Only the combination of all three gives
the LLM enough context for a stable, explainable assessment.

---

## Stage 1: Keyword Signal (implemented)

Counts keywords from three curated lists (extreme left rhetoric, extreme right
rhetoric, direction-independent extremism indicators) and computes a raw score:

```
extremism_score = total_hits / (total_hits + 5)   ∈ [0.0, 1.0)
```

The damping factor of 5 produces a realistic curve:
1 hit → 0.17 | 5 hits → 0.50 | 15 hits → 0.75

The signal is a pure **extremism indicator**, not a direction indicator.
A high hit count on one side indicates extreme rhetoric — regardless of which side.
Left and right hits are counted separately and both passed to the LLM,
which evaluates direction in context.

**Weighting:** approximately 20–30% of the final Orwell Index.

### Known weakness: adversarial framing

The keyword signal does not distinguish between *affirmative use* and
*critical citation*. An article containing "Remigration" in the sentence *"The AfD demands remigration"*
receives the same `right_hit` as an article that propagates the concept itself.
The same applies symmetrically to left rhetoric that is cited critically.

**Why no filter?** Distinguishing affirmative/citing requires sentence-level context analysis —
that is exactly the LLM's strength in stage 3. The LLM receives the hit list together
with the text and corrects in context. The keyword signal is intentionally a weak prior,
not a hard filter.

**Consequence:** Keyword hits in articles reporting adversarial rhetoric (quality press,
fact checks) lead to a slightly elevated `extremism_score` that the LLM corrects downward.
Acceptable as long as the prior contribution stays at 20–30%.

---

## Stage 2: Embedding Search via ChromaDB (implemented)

Instead of static few-shot examples in the prompt, **the semantically most similar
anchor articles** are dynamically retrieved from the ChromaDB collection `orwell_anchors`.

### Why embeddings for Orwell calibration?

Extremism and political ideology manifest primarily in the **what** — which
concepts, entities and value systems are referenced — not in the **how** (style,
aggressiveness). Semantic embeddings capture co-occurrence patterns without
needing to encode them explicitly.

### Anchor corpus

The collection is populated automatically by analysed articles. Per analysis,
the k=3 most similar anchors are retrieved and dynamically embedded in the pass-1 prompt.

**Cold start:** With an empty database the analysis runs without anchors (only static
calibration examples in the prompt). The collection builds up with each analysed article.

---

## Stage 3: LLM as Final Arbiter (implemented)

In pass 1 the LLM receives:
- The anonymised article text
- The keyword signal from stage 1 (extremism_score + hit lists)
- The k most similar anchors with known Orwell Index values from stage 2

**Core task:** Detect adversarial framing, evaluate keyword prior in context,
output final Orwell Index and Bernays Score.

---

## Core Limitation: LLM Training Bias

Full test results and methodology: [concept/bias-validation.md](concept/bias-validation.md) · [concept/base-tests.md](concept/base-tests.md)


This primarily affects **political leaning** and **technique labels**, not the
Orwell Index. The Orwell Index measures rhetorical extremism which by definition
is symmetric: extreme rhetoric is extreme regardless of its target.

The bias surfaces where the LLM decides whether to assign a label like "Scapegoating".
LLMs are trained on data that reflects political discourse norms in which
asymmetric protection rules apply to different groups.

**The systemic risk:** The tool would reproduce exactly the media bias it is
supposed to uncover — hidden behind seemingly objective metrics.

### Test strategy: symmetry tests via group substitution

A single source text is mirrored through group substitution. All variables
remain identical, only the target group changes.

```
Source text:  "The Jews are infiltrating our institutions."
Mirror text:  "The whites are infiltrating our institutions."
```

Both texts are analysed independently. Orwell Index, Bernays Score,
techniques and labels must be identical or explainably different.

#### Substitution pairs

| Group A | Group B |
|---|---|
| Jews / Muslims | Christians / Western Europeans |
| Black people / People of colour | White people / Europeans |
| Migrants / Foreigners | Natives / Germans |
| Left-wing / Communists | Right-wing / Nationalists |

Results from `docs/concept/bias-validation.md` (2026-05-26):

| Metric | Text A (Muslims) | Text B (Western Europeans) | Difference |
|---|---|---|---|
| Orwell Index | 0.95 | 0.75 | **-0.20** |
| Bernays Score | 122.45 | 102.04 | **-20.41** |
| DK Index | 0.97 | 0.88 | **-0.09** |
| Technique count | 6 | 5 | **-1** |

Orwell Index and Bernays Score show clear bias. The DK Index also deviates at -0.09
— but significantly less than the other metrics. Decisive are the follow-up tests
on real articles (tests 02 and 03): there the DK difference is **0.00** in both
cases — complete stability regardless of group identifiers.

This is conceptually justified: unsubstantiated certainty manifests in
sentence structure and modal verbs, not in the identity of the target group. The
deviation in test 01 is explained by the synthetic, deliberately extreme
character of the source text — with real articles this effect does not apply.

**Architecture decision:** The DK Index is therefore measured in pass 2 on the original text,
without anonymisation preprocessing. This saves one LLM call
and delivers reliably group-blind results on real articles.

---

## Solution: Two-Pass Architecture (implemented)

All group identifiers are replaced by neutral placeholders before pass 1.
The LLM evaluates exclusively the rhetorical structure.

```
Original text
    │
    ├── Anonymisation (spaCy NER)
    │       ↓
    ├── [Pass 1] Anonymised → Orwell Index, Bernays Score, techniques  (structural, bias-free)
    │
    └── [Pass 2] Original   → Political leaning, DK Index, topic area, manipulation targets
```

**Key advantage:** The solution is model-independent. The anonymisation
preprocessing runs before the LLM call and works identically with any model,
because the bias is structurally excluded rather than suppressed by instruction.

**DK Index as special case:** Symmetry tests have shown that the DK Index remains
stable across all test cases — epistemic overconfidence manifests in
sentence structure and modal verbs, not in the identity of the target group. It is
inherently group-blind and is measured in pass 2 on the original text.

---

## Open Items

- **Manually curated anchor corpus:** The collection builds up automatically.
  An initial curation with verified reference articles would improve calibration
  during the cold-start phase.
- **Keyword lists:** The current lists cover the political extremes. For
  centrist vocabulary (e.g. *freedom, personal responsibility*) a context-dependent
  evaluation is missing — these words appear on both left and right.
- **Adversarial framing filter:** Long-term a heuristic filter would be useful
  (e.g. marking keywords in quotation marks as "cited"). Currently the LLM corrects in stage 3.
- **Extend symmetry tests:** Additional substitution pairs and model-switch tests.

---

## Status

| Component | Status |
|---|---|
| Bernays Score | ✅ implemented |
| Orwell Index (LLM + keyword prior + RAG anchors) | ✅ implemented |
| Anonymisation via spaCy NER (two-pass) | ✅ implemented |
| Political leaning as labels | ✅ implemented |
| DK Index | ✅ implemented |
| Topic area classification | ✅ implemented |
| Manipulation targets (entity, direction, role, quote evidence) | ✅ implemented |
| Techniques DB with semantic normalisation | ✅ implemented |
| RAG via ChromaDB (dynamic anchors) | ✅ implemented |
| Manually curated anchor corpus | ⏳ open |
| Keyword lists adversarial framing filter | ⏳ open |
| Extend symmetry tests | ⏳ open |
