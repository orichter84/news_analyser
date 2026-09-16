# Prompting Patterns: Lessons from `pass0.md`/`pass1.md`/`pass2.md`

This document distills the general, model-agnostic prompting techniques embedded in
`src/news_analyser/prompts/system/pass0.md`, `pass1.md` and `pass2.md`, isolated from
the project-specific decisions that produced them. Each pattern names why it was
introduced and where it lives, and — where known — which model's observed behaviour
made it necessary. Two eras, covered in order:

- **[Foundational patterns](#foundational-patterns-adrs-00010006)** (ADRs 0001–0006,
  2026-05 to 2026-09-08) — the original indicator design: what the pipeline measures,
  and the structural choices (anonymisation, orthogonal metrics, pass-splitting) that
  make those measurements trustworthy in the first place.
- **[Recalibration-era patterns](#recalibration-era-patterns-adrs-00070010)** (ADRs
  0007–0010, 2026-09-13 to 2026-09-16) — fixes to *how reliably* those measurements
  hold up, triggered by direct Gemini-vs-Claude comparison testing.

Source: ADRs [0001](../concepts/decisions/0001-pass0-group-detection-and-quote-stripping.md)–[0010](../concepts/decisions/0010-quote-amplification-grounding-and-debug-run-history.md)
and [bias-validation.md](../concepts/validation/bias-validation.md).

## Models referenced

| Shorthand | Model | Role in this project |
|---|---|---|
| **Gemini** | `gemini-2.5-flash`, via OpenAI-compatible endpoint (`src/news_analyser/__init__.py`) | Production `LLM_PROVIDER=gemini` adapter. The most-tested provider and the source of most recalibration triggers ([0007](../concepts/decisions/0007-manipulation-target-grounding.md), [0008](../concepts/decisions/0008-gemini-orwell-index-recalibration.md), [0010](../concepts/decisions/0010-quote-amplification-grounding-and-debug-run-history.md)). Note: manual ad-hoc analysis work outside the pipeline (e.g. reviewing this codebase) has used other Gemini versions ("Gemini 3.8") — distinct from the pipeline adapter's pinned `gemini-2.5-flash`. |
| **Claude (CLI)** | `claude-opus-4-5` (default), via the `cli` adapter (`llm_adapter.cli_adapter`, wraps the Claude Code CLI) | Comparison baseline in provider tests — consistently more conservative on graduated/soft instructions than Gemini ([0007](../concepts/decisions/0007-manipulation-target-grounding.md), [0008](../concepts/decisions/0008-gemini-orwell-index-recalibration.md)). |
| **Qwen3-14B** | `qwen/qwen3-14b`, local via LM Studio (MLX, 8-bit, Apple Silicon) | Local-model symmetry testing ([bias-validation.md](../concepts/validation/bias-validation.md)). Source of the original hallucination patterns `_validate_quote_grounding` was built to catch. |
| **GPT-OSS-20B (uncensored)** | `openai-gpt-oss-20b-instruct-heretic-uncensored-hi-mlx`, local via LM Studio | Faster local alternative to Qwen3-14B for unattended feed operation; the non-uncensored base model refuses political content in Pass 2 entirely. |

---

## Foundational patterns (ADRs 0001–0006)

### F0. Let the model identify; let code replace
**Mechanism:** Pass 0 (`pass0.md`, called from `group_detector.py`'s `detect_groups()`)
has exactly one job: return a JSON list of `{"term", "type"}` group identifiers found
in the *original* text. It never touches the text itself — the actual substitution
into `Gruppe-A`/`Gruppe-B` placeholders happens entirely in
`anonymizer/spacy_strategy.py`'s `replace_groups()`, deterministically, from that list.
The module docstring states this as the design intent directly: *"Das LLM identifiziert
nur — das Ersetzen erfolgt deterministisch durch den Anonymizer-Code, nicht durch das
LLM."*
**Why:** fuzzy judgment ("is 'schwarze Jugendliche' a group reference, while plain
'schwarz' the colour is not?") is what an LLM is good at; exact, repeatable, load-
bearing text substitution is exactly the kind of task worth taking out of the model's
hands once the judgment call is made — the same reasoning as F3's "let the model
enumerate, compute the aggregate in code," applied one step earlier in the pipeline.
Splitting identification from replacement also means a Pass 0 mistake fails safe: a
missed group term just isn't anonymised (Pass 1 sees it in clear text, same as any
other imperfect NER catch), rather than corrupting the text with a malformed
replacement.
**Also notable:** `pass0.md` explicitly scopes itself against its two neighbours to
avoid double-handling — *"Do NOT include political party names, ideological labels, or
named individuals — those are handled separately"* (named individuals go through spaCy
NER in the same `anonymizer` pipeline; ideological labels go through the lexical
`normalize()` step, not Pass 0, see the correction to F1 below). And its type taxonomy
(`racial | ethnic_origin | religious | gender_identity | sexual_orientation |
national_origin`) is a closed enum with a contrastive disambiguation example built in —
*"'schwarz' as a colour is NOT a group identifier. 'schwarze Jugendliche' IS"* — the
same minimal-pair technique as pattern #5 below, here used for token-level
classification rather than technique/role calibration.

### F1. Remove the bias structurally, don't ask the model to compensate for it
**Mechanism:** three ordered preprocessing steps run before Pass 1 ever sees the text
(`anonymizer/strategy.py`'s `AnonymizationStrategy.anonymize()`): (1) `normalize()`
rewrites ideologically loaded vocabulary to neutral synonyms in plain text — no
placeholder, just a lexical substitution (`_normalizations.py`'s `IDEOLOGICAL_TERMS`,
e.g. `"antifa"` → `"extremisten"`, `"kommunistisch"` → `"ideologisch"`); (2) `ner()`
replaces spaCy-detected persons/organisations with typed, numbered placeholders
(`Person-A`, `Org-A`, …); (3) `replace_groups()` replaces the Pass-0-detected group
terms with `Gruppe-A`, `Gruppe-B`, ….
**Why:** [0001](../concepts/decisions/0001-pass0-group-detection-and-quote-stripping.md)
is explicit that this was a fallback, not the first attempt: *"Prompt-engineering alone
('please be unbiased') did not reliably fix this"* — the original 2026-05-26 symmetry
test in [bias-validation.md](../concepts/validation/bias-validation.md) showed
identical rhetoric scoring differently depending on which named group was mentioned.
The fix removes the trigger from the model's input entirely rather than trusting an
instruction to neutralise it.
**Model attribution:** cross-model by design and by result — the later repeat tests in
bias-validation.md (Claude CLI, Qwen3-14B, GPT-OSS-20B) all land near 0.00 difference
after this structural fix, confirming it holds regardless of which model runs Pass 1.
**Correction (caught in review by GPT-5.6 Terra, 2026-09-16):** an earlier version of
this entry, and `pass1.md` itself, describe the placeholders as `Akteur_A`/`Status_X`.
That naming doesn't exist anywhere in the current anonymizer — it produces `Person-A`,
`Org-A`, `Gruppe-A`. `pass1.md`'s own example text is stale relative to its
implementation, not just this doc; worth a follow-up fix to `pass1.md` itself (not done
here). The earlier version of this entry also omitted the ideological-term
normalization step entirely — a real gap, not just an imprecision, since it's a third,
distinct mechanism (lexical substitution, no placeholder) alongside the two placeholder
based steps.

### F2. An instructed self-check can replace structural anonymisation — for the *right* axis
**Mechanism:** pass1.md's opening "Critical symmetry rule": mentally swap all
placeholders and re-evaluate identically in both directions; repeated as the prompt's
closing "Final instruction."
**Why:** [0002](../concepts/decisions/0002-abandon-unified-gender-anonymization.md) —
a branch tried extending F1's structural treatment to gender via a unified NER pass,
and it backfired: Bernays Score dropped from 3.92 to 3.26/1000w on the same corpus,
i.e. the model over-anonymised and lost signal it needed for technique detection. The
existing role-reversal instruction turned out to already be *sufficient* for the
gender dimension specifically, without a dedicated structural step. Lesson: F1's
heavyweight treatment isn't the default answer to every bias axis — check whether a
cheaper instructed self-check already covers it before adding structure that can cost
you signal elsewhere.

### F3. Let the model enumerate; compute the aggregate in code
**Mechanism:** `detected_techniques` is a JSON array the model populates one instance
at a time; `bernays_score` itself is never asked of the LLM — it's
`len(detected_techniques) / pass1_word_count * 1000`, computed entirely in
`db_storage.py`.
**Why:** [0003](../concepts/decisions/0003-separate-bernays-and-orwell-metrics.md) —
the original single `bias_score` conflated *how extreme* a text reads (inherently a
graduated, qualitative judgment — well suited to a direct LLM float) with *how many*
manipulation techniques it uses (a plain count — poorly suited to asking the model for
a number directly, since that number becomes unauditable). Letting the model produce a
list of instances that each carry a quote (see "Grounding-as-verification" below) and
computing the density mechanically means every unit that feeds the count can at least
be traced back to a specific, existence-checked location in the text Pass 1 actually
saw — a single requested float never offers that. **Precision, per review feedback
(twice now):** (1) this is auditability, not correctness-verification — grounding
confirms a cited string exists (and isn't over-counted), not that the `technique` label attached to it
is the right one, and not that two overlapping quotes filed under different technique
names aren't really the same rhetorical act double-counted twice (a real, still-open
gap — see the "Substring-Lücke" in
[`bernays_score_pipeline_analysis.md`](../analyses/bernays_score_pipeline_analysis.md));
(2) "the text Pass 1 actually saw" is `pass1_text` — the anonymised *and*
quote-stripped version (`_strip_quoted_material`, `analyzer.py`) — not the original
article. `_validate_quote_grounding` checks the model's quotes against that text, not
against `article.text`.

### F4. Split a conflated concept into independently-scored outputs
**Mechanism:** `orwell_index` (Pass 1) and `dunning_kruger_index` (Pass 2) are scored
as separate fields, never derived from one another.
**Why:** [0004](../concepts/decisions/0004-add-dunning-kruger-index.md) — epistemic
overconfidence is "grammatically/structurally determined, not tied to which group is
discussed," a genuinely different axis from rhetorical extremism. A combined judgment
would hide texts that are calm-but-overconfident or heated-but-well-sourced. Confirmed
group-blind by construction, and largely by measurement, precisely because it doesn't
ride on the anonymisation-sensitive axis at all — but "zero difference" overstates it
(**correction, per review feedback**): [bias-validation.md](../concepts/validation/bias-validation.md)'s
real-article tests (02, 03) show exactly 0.00 DK difference between mirrored texts, and
the local models (Qwen3-14B, GPT-OSS-20B) show 0.00 on the synthetic Test 01 too — but
Claude (CLI) shows a small Δ=-0.07 on that same synthetic Test 01. Accurate claim:
consistently the most stable of the three metrics, not unconditionally zero everywhere.

### F5. Resist re-coupling axes you deliberately split apart
**Mechanism:** none in the current code — this documents a change that was built and
then reverted before merging.
**Why:** [0005](../concepts/decisions/0005-quote-amplification-index.md)'s "Rejected
alternative": a technique-count floor ("6+ techniques → `orwell_index` ≥ 0.6") was
implemented to fix a real gap, then reverted because it broke the orthogonality F3/F4
establish — many small, low-intensity techniques should not force a high extremism
score. Named as its own pattern because the instinct to fix a missing case by directly
coupling two metrics is exactly the kind of shortcut that quietly undoes an earlier
architectural decision; the question to ask first is what *actually* explains the gap
(see F6 for what was built instead).

### F6. When one axis needs two different input scopes, split it across passes
**Mechanism:** `orwell_index_structural` (Pass 1, on the anonymised *and*
quote-stripped text) and `quote_amplification_index` (Pass 2, on the full original
text with quotes intact) are two separately-scored sub-judgments of "how extreme is
this," merged via `orwell_index = max(orwell_index_structural, quote_amplification_index)`.
**Why:** [0005](../concepts/decisions/0005-quote-amplification-index.md) — F1's
quote-stripping (needed to stop Pass 1 crediting/blaming the article for a third
party's words) is exactly what made an article's enemy-imagery-via-selective-quoting
invisible to it: a taz article scored `orwell_index: 0` despite clear enemy-image
content carried entirely through *which* quotes it chose to platform. Rather than
undoing F1's protection, the fix asks the same underlying question twice, with
different input scope, and merges the answers after — each pass stays clean for what
it was designed to see.

### F7. Widen what counts *and* cap how much it counts, in the same change
**Mechanism:** pass1.md's "Indirect enemy-image rule" recognises attribution-chain
framing ("Group X causes/represents Y, Y framed as harmful") even compressed into one
clause or with the antagonist named only by category — immediately paired with:
"Proportion the score to how developed it is... an isolated instance... never 0.7+."
**Why:** [0006](../concepts/decisions/0006-indirect-enemy-image-rule.md) — a taz piece
built the same kind of enemy image as a DW piece that correctly scored 0.7, but did it
indirectly (a single-clause aside in an otherwise unrelated article) and scored 0; Pass
1 only recognised the direct form. Widening recognition without a paired severity cap
would have overcorrected into the opposite failure this fix targets — a throwaway
aside suddenly scoring like a piece built entirely around the antagonism. Verified on
the motivating article: 0 → 0.4, not 0 → 0.7+.

### F8. Anchor a continuous score to named qualitative bands
**Mechanism:** `pass1.md`'s Orwell Index scale — 0.0–0.3 factual/slightly tendentious,
0.4–0.6 clearly emotional/one-sided, 0.7–0.9 strong enemy images, 1.0
apocalyptic/mobilisation. `quote_amplification_index` in `pass2.md` has the same
four-tier shape. **`dunning_kruger_index` does not (correction, per review feedback):**
`pass2.md` only anchors the two extremes — "Score HIGH (→1.0) when..." / "Score LOW
(→0.0) when..." — with no defined middle bands. Worth noting as a real design
difference, not an oversight to fix by analogy. **Further correction, per review
feedback:** an earlier version of this entry additionally claimed the DK explanation
requirement (pattern #2 below) already substitutes for that missing middle-band
calibration. It doesn't, technically — `dunning_kruger_explanation` is unvalidated free
text: no quote is required, and nothing in `analyzer.py` checks that the explanation
actually names a specific textual pattern rather than restating the score in words. It
can improve transparency for whoever reads the result, but it is not a code-enforced
substitute for a defined middle band the way the Orwell/quote-amplification bands are.
**Why:** general technique, present from the original indicator design — an
unanchored "return a float 0.0–1.0" invites arbitrary precision with no shared
reference point across runs. Naming what each region of the scale *means* is also
what F7's and [0008](../concepts/decisions/0008-gemini-orwell-index-recalibration.md)'s
proportionality guards attach to — you can only say "an isolated instance stays in
0.2–0.4" if 0.2–0.4 already means something specific.

**Side-finding, not yet a fix:** one intended weak-signal pattern doesn't actually
appear in the model-facing prompt. `keywords.py`'s module docstring states the
`extremism_score` keyword signal is meant to be treated as *"a weak prior (~20-30%
weight)"* — but that framing exists only as a code comment. `pass1.md` never mentions
`keyword_signal` at all; the model receives the raw number in `pass1_input` with zero
instruction on how much weight to give it. This lines up exactly with the "anchoring
effect" concern raised in the original Gemini `orwell_index_pipeline_analysis.md` (filed
at the time as "plausible but not code-verifiable" in the meta-validation) — there's now
code-level evidence for the risk: the intended dampening was never actually communicated
to the model.

## Recalibration-era patterns (ADRs 0007–0010)

### 1. Grounding-as-verification, not grounding-as-trust
**Mechanism:** require a verbatim quote for a claim, then check it in code before accepting it. The three validators don't all check the same thing, and don't all check against the same text: `_validate_quote_grounding` (`detected_techniques`) runs against `pass1_text` (anonymised, quote-stripped — see F3) and checks both that the string occurs at all *and* that it isn't claimed more times than it actually occurs (`source_text.count(quote)`, `analyzer.py`); `_validate_manipulation_target_grounding` and `_validate_stroemung_grounding` run against the full `article.text` and only check existence (`quote in source_text`) — no occurrence-count inflation check for targets or `politische_stroemung` labels.
**Scope (precision, per review feedback):** this verifies that the cited *string* exists and isn't over-counted — it does not verify that the *label* attached to it (which technique, which role) is the correct one, and it does not catch two different labels citing overlapping-but-distinct quotes for what's really the same rhetorical instance. "Grounded" means existence-checked, not semantically correct.
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
**Mechanism:** interview format, survey/poll articles, and pure-summary articles each get their own named genre carve-out; terse factual reporting gets a general rule instead (not genre-named — "do not score high merely because settled facts are stated tersely and directly," `pass2.md`, applies to any terse factual sentence, not specifically to news-wire/agency text) — each rather than one abstract rule expected to transfer across cases unaided.
**Model attribution:** the whole recalibration in [0008](../concepts/decisions/0008-gemini-orwell-index-recalibration.md) was triggered by **Gemini** scoring a routine derStandard interview at `orwell_index: 0.75` where **Claude (CLI)**, given the identical prompt, produced a "materially lower, more plausible score" — the genre-blindness was provider-specific, not inherent to the task.

### 8. Decouple correlated-but-independent fields with wrong-inference examples
**Mechanism:** `rolle` and `direction` are stated as "never inferred from each other," backed by explicit ❌ examples of the wrong inference (e.g. `rolle: Opfer` → `direction: positiv` is flagged as wrong).
**Model attribution:** [0007](../concepts/decisions/0007-manipulation-target-grounding.md), Gemini-vs-Claude comparison — the stated-independence rule alone wasn't sufficient.

### 9. Tie a soft pledge to a hard, checkable consequence
**Mechanism:** *"If you can't name a specific quote, the score can't be above 0.3"* ([0010](../concepts/decisions/0010-quote-amplification-grounding-and-debug-run-history.md)) — converts a request for justification into a decision rule, without code enforcement.
**Model attribution:** untested which model(s) this actually disciplines — added in response to an observed **Gemini** blackbox score, not yet re-run to confirm it changes Gemini's behaviour (see [0010](../concepts/decisions/0010-quote-amplification-grounding-and-debug-run-history.md)'s consequences section: "can only be confirmed by re-running it").

### 10. Concrete calibration anchors — static (curated) vs. dynamic (unvalidated)
**Mechanism:** two mechanisms of a different character, bundled under one name:
- **Static:** hand-written historical examples (NSDAP/SED/AfD label sets in `pass2.md`)
  — fixed, human-authored, reviewed as part of writing the prompt.
- **Dynamic (RAG):** `anchor_store.py` embeds the k=3 most similar *prior automated
  analyses* into the Pass 1 prompt once the anchor collection holds ≥ `MIN_ANCHORS`
  (5) entries. `add_anchor()` is called unconditionally after every single
  `analyze_article()` run (`analyzer.py`) — there is no quality filter, human review,
  or outlier check before a result becomes a future calibration reference.
**Why (motivation, not a demonstrated fix — correction per review feedback):** the
original problem statement in [analyse_architektur.md](analyse_architektur.md) names
*"Model drift: When switching models, calibration shifted without warning"* as the
motivating concern, and [bias-validation.md](../concepts/validation/bias-validation.md)
does demonstrate the *problem* this is meant to address — the same qualitative band
lands at different absolute severities per model (Qwen3's Orwell 1.00 vs. GPT-OSS's
0.80 on identical synthetic Test 01). **What isn't demonstrated:** that RAG anchoring
actually closes that gap — no test in this repo compares the same input with anchors
on vs. off. Treat "anchoring improves cross-model comparability" as the hypothesis the
mechanism was built to test, not a confirmed effect.
**Known risk, not yet mitigated:** because dynamic anchors are unfiltered past model
judgments, a single over- or under-scored analysis becomes a calibration reference for
future similar articles — a feedback loop that could reinforce miscalibration instead
of correcting it. Already flagged as a code-confirmed mechanism (if not yet an
empirically confirmed *effect*) in
[`meta_validierung_gemini_analysen.md`](../analyses/meta_validierung_gemini_analysen.md)
§5 ("Anker-Feedback-Loop").

---

## Named techniques from the general literature: used, not used, or misapplied

The patterns above are named for what they do in this codebase. Mapped onto vocabulary
from the wider prompting-technique literature, the picture is uneven: some are central
and already covered above, some are used but not yet named as such, some are
deliberately avoided in favour of something related but different, and some aren't used
at all — either by design choice or because the current adapter abstraction doesn't
support them.

### Grounding — used, already covered above
This is the pipeline's dominant technique; see "Grounding-as-verification, not
grounding-as-trust" and its scope note in the recalibration-era section, plus F0/F3
above. Nothing new to add here.

### Chain-of-Thought — not used; silent self-verification instead
No prompt in `pass0.md`/`pass1.md`/`pass2.md` asks the model to reason step by step or
show intermediate reasoning. What exists instead is narrower and produces no visible
trace:
- `pass1.md:6` — *"Before submitting your final analysis, **mentally** perform a
  complete role-reversal test..."*
- `pass1.md:12` — *"Before finalising each entry, **verify silently** that the exact
  string is actually present in the text."*

Both instruct an internal check, explicitly not a written one — consistent with the
output contract being a single clean JSON object with no prose interleaved (CoT's usual
form, a visible reasoning trace before the answer, would break that parsing contract
unless separated out, which nothing here does).

**Native CoT is actively discarded when a model produces it unprompted:**
`_extract_json` (`analyzer.py:61`) strips `<think>...</think>` blocks before parsing —
a Qwen-family model's own extended-thinking output. That reasoning is never logged,
inspected, or used; it's pure overhead removed to get at the JSON underneath.

**Open question, not yet tested:** the `explanation` fields added in
[0009](../concepts/decisions/0009-pipeline-hardening-after-gemini-meta-review.md)/[0010](../concepts/decisions/0010-quote-amplification-grounding-and-debug-run-history.md)
are positioned *after* their score in the JSON schema (`pass2.md:32-35`:
`dunning_kruger_index` then `dunning_kruger_explanation`; `quote_amplification_index`
then `quote_amplification_explanation`). For a model that fills JSON fields in
schema order, this means committing to the number before writing any justification for
it — the explanation becomes post-hoc rationalisation, not reasoning that could inform
the score the way CoT's reason-then-conclude ordering does. Whether reordering the
schema (explanation before score) would change the *score itself*, not just its
legibility, is an untested hypothesis — would need a repeated-run comparison (same
article, both field orders) using the debug-run archive from
[0010](../concepts/decisions/0010-quote-amplification-grounding-and-debug-run-history.md)
before concluding either way.

### Prompt chaining — real, but narrower than "Pass 0/1/2" suggests
The naming implies one linear chain; the actual dependency graph is one true chain plus
one independent branch, merged in code:
- **Pass 0 → Pass 1 is a genuine sequential chain.** `detect_groups()`'s output
  (`group_terms`) is fed into `anonymize()`, whose output becomes Pass 1's input text
  (`analyzer.py`) — Pass 1 cannot run without Pass 0's result shaping it first.
- **Pass 1 and Pass 2 are *not* chained to each other.** `pass2_input` is built from
  `base_meta` and `article.text` alone — it does not read `result1` at all. Both calls
  could run concurrently; they're only combined afterwards, in code
  (`orwell = max(orwell_structural, quote_amplification)`). Calling this a "Pass 1 →
  Pass 2" chain would overstate the actual dependency.
- **Two further chain-like steps exist outside the three named passes:** the RAG anchor
  lookup (`anchor_store.get_similar_anchors()`, a ChromaDB query, not an LLM call)
  splices retrieved text into the Pass 1 prompt *before* that call fires — retrieval-
  augmented generation, strictly speaking, not model-to-model chaining. And
  `normalize_technique`/`normalize_role`/`normalize_stroemung` run an embedding lookup
  *after* Pass 1/2 return, mapping free-text output onto a canonical taxonomy — a
  generate-then-normalize chain step with no LLM call in it at all.

### Role/persona prompting — used in all three passes
Each system prompt opens with an explicit role assignment: `pass0.md:1` — *"You are a
text analysis assistant. Your only task is to identify group identifiers..."*;
`pass1.md:1` — *"You are an expert media analyst specialising in rhetorical analysis,
propaganda studies, and cognitive bias detection."*; `pass2.md:1` — *"You are an expert
media analyst specialising in political science, ideology research, and
epistemology."* Each persona is scoped to that pass's specific task rather than one
generic "expert" framing reused across all three.

### Structured output constraints — instruction-only, not provider-native JSON mode
All three prompts end their format section with "Return ONLY a single, valid JSON
object" (or equivalent). The `llm_adapter` package's `OpenAIAdapter` (used for the
`gemini` provider) supports a `json_mode` config flag that requests the provider's
native `response_format={"type": "json_object"}` constrained-decoding mode — the
`gemini` adapter registration (`src/news_analyser/__init__.py`) does not set it, so it
stays at its default, `False`. Compliance is instruction-only, backstopped by
`_extract_json`'s markdown-fence stripping and `json_repair` fallback
(`analyzer.py`) rather than enforced at the decoding level.

### Sampling temperature — configured, not tuned per pass
`OpenAIAdapter` defaults `temperature` to `0.2`; the `gemini` registration doesn't
override it, so all three passes run at that value. The `cli` adapter (Claude) doesn't
expose temperature as a controllable parameter at all — its own docstring states it
"wird vom CLI nicht unterstützt und ignoriert" (not supported, ignored). Temperature is
not varied per pass or per task in either case.

### Self-consistency (multi-sample + aggregate) — not used
Each pass calls `adapter.generate()` exactly once per article; there is no retry-and-
vote or multi-sample aggregation anywhere in `analyzer.py`.

### Tool use / ReAct — not used, not currently possible
`LLMAdapter.generate()` (`llm_adapter/base.py`) takes a system prompt and input data
and returns text — no function-calling or tool-use parameter exists in the interface.
An agentic tool-use loop isn't a prompt-design choice that was skipped here; it's not
representable in the current adapter abstraction at all.

### Negative/exclusion prompting — a named category alongside contrastive pairs
Distinct from pattern #5's contrastive ❌/✓ pairs (which anchor a boundary with a
matched pair) is a simpler explicit exclusion list: `pass1.md`'s "What NOT to flag"
section (grammatical errors, hedged claims, neutral group mentions, ordinary
institutional criticism) and `pass0.md`'s *"Do NOT include political party names,
ideological labels, or named individuals — those are handled separately."* Both name
what the model should not do, without necessarily pairing it against a positive
example of what it should do instead.

---

## Where prompting hits its limit

Not every failure mode is a prompting problem. The `normalize_stroemung` negation-collapse bug ([0009](../concepts/decisions/0009-pipeline-hardening-after-gemini-meta-review.md): `antifeministisch` → `feministisch` at cosine distance 0.18) lives in the embedding-similarity normalization layer, which no LLM ever sees or influences — no amount of prompt engineering in `pass1.md`/`pass2.md` could have prevented or fixed it. That distinction — is the failure in what the model is asked to judge, or in code that runs before/after the model — is itself worth checking first when a new instability shows up.

## A meta-pattern: symmetry/comparison testing as the diagnostic method

Nearly every finding above came from the same methodology, not from reading the prompt and guessing: run the **identical** input through multiple models (or the same model repeatedly), diff the outputs, and only then hypothesise a cause. [bias-validation.md](../concepts/validation/bias-validation.md)'s group-substitution tests and [0008](../concepts/decisions/0008-gemini-orwell-index-recalibration.md)'s repeated-run variance table are both this same method applied to different axes (group identity vs. run-to-run stability). [0010](../concepts/decisions/0010-quote-amplification-grounding-and-debug-run-history.md)'s debug-run archive exists specifically so this method stays available going forward instead of losing its raw data after the next run.

