# Prompting Patterns: Lessons from `pass1.md`/`pass2.md`

This document distills the general, model-agnostic prompting techniques embedded in
`src/news_analyser/prompts/system/pass1.md` and `pass2.md`, isolated from the
project-specific decisions that produced them. Each pattern names which model's
observed behaviour made it necessary — some are universal defensive engineering,
others exist specifically to correct one model's failure mode. Source: ADRs
[0006](../concepts/decisions/0006-indirect-enemy-image-rule.md)–[0010](../concepts/decisions/0010-quote-amplification-grounding-and-debug-run-history.md)
and [bias-validation.md](../concepts/validation/bias-validation.md).

## Models referenced

| Shorthand | Model | Role in this project |
|---|---|---|
| **Gemini** | `gemini-2.5-flash`, via OpenAI-compatible endpoint (`src/news_analyser/__init__.py`) | Production `LLM_PROVIDER=gemini` adapter. The most-tested provider and the source of most recalibration triggers ([0007](../concepts/decisions/0007-manipulation-target-grounding.md), [0008](../concepts/decisions/0008-gemini-orwell-index-recalibration.md), [0010](../concepts/decisions/0010-quote-amplification-grounding-and-debug-run-history.md)). Note: manual ad-hoc analysis work outside the pipeline (e.g. reviewing this codebase) has used other Gemini versions ("Gemini 3.8") — distinct from the pipeline adapter's pinned `gemini-2.5-flash`. |
| **Claude (CLI)** | `claude-opus-4-5` (default), via the `cli` adapter (`llm_adapter.cli_adapter`, wraps the Claude Code CLI) | Comparison baseline in provider tests — consistently more conservative on graduated/soft instructions than Gemini ([0007](../concepts/decisions/0007-manipulation-target-grounding.md), [0008](../concepts/decisions/0008-gemini-orwell-index-recalibration.md)). |
| **Qwen3-14B** | `qwen/qwen3-14b`, local via LM Studio (MLX, 8-bit, Apple Silicon) | Local-model symmetry testing ([bias-validation.md](../concepts/validation/bias-validation.md)). Source of the original hallucination patterns `_validate_quote_grounding` was built to catch. |
| **GPT-OSS-20B (uncensored)** | `openai-gpt-oss-20b-instruct-heretic-uncensored-hi-mlx`, local via LM Studio | Faster local alternative to Qwen3-14B for unattended feed operation; the non-uncensored base model refuses political content in Pass 2 entirely. |

---

## The patterns

### 1. Grounding-as-verification, not grounding-as-trust
**Mechanism:** require a verbatim quote for a claim, then verify it against the source text in code (`_validate_quote_grounding`, `_validate_manipulation_target_grounding`, `_validate_stroemung_grounding`) and drop/null whatever doesn't check out.
**Model attribution:** originated for **local models** (Qwen3/GPT-OSS) — the `_validate_quote_grounding` docstring names two hallucination patterns "observed with local models": fabricated quotes and inflated occurrence counts. Later found necessary for **Gemini** too, in a different failure mode: [0007](../concepts/decisions/0007-manipulation-target-grounding.md) found Gemini "never appeared to use" the permitted `null` fallback for an ungrounded classification — Claude did, correctly and conservatively. So the same mechanism catches two distinct failure modes from two different model families; neither model's prompt-level self-restraint could be trusted alone.

### 2. Match the evidence format to the nature of the judgment
**Mechanism:** not every score needs a verbatim quote. `dunning_kruger_explanation` ([0009](../concepts/decisions/0009-pipeline-hardening-after-gemini-meta-review.md)) is deliberately a free-text justification, not a quote requirement — epistemic overconfidence is a property of a text's overall tone, and forcing a single-sentence citation would manufacture artificial "evidence." `quote_amplification_explanation` ([0010](../concepts/decisions/0010-quote-amplification-grounding-and-debug-run-history.md)), by contrast, is required to name a specific quote — the judgment is defined as being about a specific piece of quoted material, so a quote requirement is the correct fit there.
**Model attribution:** general design principle, not tied to one model's failure — but the concrete trigger was **Gemini** producing a `quote_amplification_index: 0.7` with zero supporting evidence in the raw output (2026-09-16 manual test), making the blackbox problem visible.

### 3. Mechanical preprocessing over prompted self-restraint
**Mechanism:** `_strip_quoted_material` removes quoted speech from the text *before* it reaches the model for Pass 1, rather than only instructing the model to ignore it.
**Model attribution:** universal — the code comment is explicit: *"every model tested so far violated that rule at least once when asked to self-exclude it."* The one gap this doesn't close (unmarked `Name: Antwort` interview turns) remains a **known limitation across all models** per [0008](../concepts/decisions/0008-gemini-orwell-index-recalibration.md) and [0010](../concepts/decisions/0010-quote-amplification-grounding-and-debug-run-history.md) — still prompt-instruction-only, deliberately deferred rather than rushed.

### 4. Name both failure directions with equal force
**Mechanism:** the Pass 1 counting rule states merging-too-much and splitting-too-much as "equally WRONG," instead of warning against only one direction.
**Model attribution:** specifically diagnosed via **Gemini** self-introspection in [0008](../concepts/decisions/0008-gemini-orwell-index-recalibration.md) — asked to explain its own counting instability, Gemini reported it "optimises against being 'caught' violating the loudly-stated rule when unsure." An asymmetric warning produced an asymmetric overcorrection; this is a model-behavioural finding, not something inferable from the rule text alone.

### 5. Contrastive ❌/✓ pairs over abstract rules
**Mechanism:** throughout `pass2.md` (`rolle`/`direction` calibration, the institutional-motive-criticism carve-out), a wrong example paired with a right one anchors the boundary better than a definition alone.
**Model attribution:** general technique, reinforced by **Gemini** comparison testing in [0007](../concepts/decisions/0007-manipulation-target-grounding.md), where abstract rules alone left room for a conflation Claude didn't make but Gemini did.

### 6. Meta-category as fallback only, never a peer option
**Mechanism:** "Framing" is defined as valid only when no more specific technique applies, and overlapping quotes must be merged into one entry rather than reported under both a specific and the meta label.
**Model attribution:** **Gemini**-specific finding in [0008](../concepts/decisions/0008-gemini-orwell-index-recalibration.md) — "passages were routinely double-counted once under a specific technique and again under 'Framing' for the same span."

### 7. Name genre exceptions explicitly, don't rely on generalisation
**Mechanism:** interview format, survey/poll articles, pure-summary articles, and news-wire terse style each get their own named carve-out rather than one abstract rule expected to transfer across genres.
**Model attribution:** the whole recalibration in [0008](../concepts/decisions/0008-gemini-orwell-index-recalibration.md) was triggered by **Gemini** scoring a routine derStandard interview at `orwell_index: 0.75` where **Claude (CLI)**, given the identical prompt, produced a "materially lower, more plausible score" — the genre-blindness was provider-specific, not inherent to the task.

### 8. Decouple correlated-but-independent fields with wrong-inference examples
**Mechanism:** `rolle` and `direction` are stated as "never inferred from each other," backed by explicit ❌ examples of the wrong inference (e.g. `rolle: Opfer` → `direction: positiv` is flagged as wrong).
**Model attribution:** [0007](../concepts/decisions/0007-manipulation-target-grounding.md), Gemini-vs-Claude comparison — the stated-independence rule alone wasn't sufficient.

### 9. Tie a soft pledge to a hard, checkable consequence
**Mechanism:** *"If you can't name a specific quote, the score can't be above 0.3"* ([0010](../concepts/decisions/0010-quote-amplification-grounding-and-debug-run-history.md)) — converts a request for justification into a decision rule, without code enforcement.
**Model attribution:** untested which model(s) this actually disciplines — added in response to an observed **Gemini** blackbox score, not yet re-run to confirm it changes Gemini's behaviour (see [0010](../concepts/decisions/0010-quote-amplification-grounding-and-debug-run-history.md)'s consequences section: "can only be confirmed by re-running it").

### 10. Concrete calibration anchors, static and dynamic
**Mechanism:** static historical examples (NSDAP/SED/AfD label sets in `pass2.md`) plus dynamic RAG anchors (`anchor_store.py`, k=3 similar prior analyses embedded into the Pass 1 prompt).
**Model attribution:** motivated by a cross-model concern from the original problem statement in [analyse_architektur.md](analyse_architektur.md): *"Model drift: When switching models, calibration shifted without warning."* Confirmed empirically across all four tested models in [bias-validation.md](../concepts/validation/bias-validation.md) — raw scale bands (e.g. "0.4–0.6") land at different absolute severities per model (compare Qwen3's Orwell 1.00 vs. GPT-OSS's 0.80 on the identical synthetic Test 01), so anchoring is what keeps cross-model comparison meaningful at all.

---

## Where prompting hits its limit

Not every failure mode is a prompting problem. The `normalize_stroemung` negation-collapse bug ([0009](../concepts/decisions/0009-pipeline-hardening-after-gemini-meta-review.md): `antifeministisch` → `feministisch` at cosine distance 0.18) lives in the embedding-similarity normalization layer, which no LLM ever sees or influences — no amount of prompt engineering in `pass1.md`/`pass2.md` could have prevented or fixed it. That distinction — is the failure in what the model is asked to judge, or in code that runs before/after the model — is itself worth checking first when a new instability shows up.

## A meta-pattern: symmetry/comparison testing as the diagnostic method

Nearly every finding above came from the same methodology, not from reading the prompt and guessing: run the **identical** input through multiple models (or the same model repeatedly), diff the outputs, and only then hypothesise a cause. [bias-validation.md](../concepts/validation/bias-validation.md)'s group-substitution tests and [0008](../concepts/decisions/0008-gemini-orwell-index-recalibration.md)'s repeated-run variance table are both this same method applied to different axes (group identity vs. run-to-run stability). [0010](../concepts/decisions/0010-quote-amplification-grounding-and-debug-run-history.md)'s debug-run archive exists specifically so this method stays available going forward instead of losing its raw data after the next run.
