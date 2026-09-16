# Prompting Patterns: Lessons from `pass1.md`/`pass2.md`

This document distills the general, model-agnostic prompting techniques embedded in
`src/news_analyser/prompts/system/pass1.md` and `pass2.md`, isolated from the
project-specific decisions that produced them. Each pattern names why it was
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
**Mechanism:** interview format, survey/poll articles, pure-summary articles, and news-wire terse style each get their own named carve-out rather than one abstract rule expected to transfer across genres.
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

## Where prompting hits its limit

Not every failure mode is a prompting problem. The `normalize_stroemung` negation-collapse bug ([0009](../concepts/decisions/0009-pipeline-hardening-after-gemini-meta-review.md): `antifeministisch` → `feministisch` at cosine distance 0.18) lives in the embedding-similarity normalization layer, which no LLM ever sees or influences — no amount of prompt engineering in `pass1.md`/`pass2.md` could have prevented or fixed it. That distinction — is the failure in what the model is asked to judge, or in code that runs before/after the model — is itself worth checking first when a new instability shows up.

## A meta-pattern: symmetry/comparison testing as the diagnostic method

Nearly every finding above came from the same methodology, not from reading the prompt and guessing: run the **identical** input through multiple models (or the same model repeatedly), diff the outputs, and only then hypothesise a cause. [bias-validation.md](../concepts/validation/bias-validation.md)'s group-substitution tests and [0008](../concepts/decisions/0008-gemini-orwell-index-recalibration.md)'s repeated-run variance table are both this same method applied to different axes (group identity vs. run-to-run stability). [0010](../concepts/decisions/0010-quote-amplification-grounding-and-debug-run-history.md)'s debug-run archive exists specifically so this method stays available going forward instead of losing its raw data after the next run.

---

## Review note (GPT-5.6 Terra, 2026-09-16)

An external review of this document found three issues, all confirmed against the
code and corrected in place above rather than left as a separate errata list:

1. **F1** described stale placeholder names (`Akteur_A`/`Status_X`) that don't match
   the current anonymizer (`Person-A`/`Org-A`/`Gruppe-A`), and omitted the ideological-
   term normalization step entirely. The stale names also turned out to still be
   present in `pass1.md` itself, not just in this doc — a real inconsistency worth a
   follow-up fix there, not done as part of this correction.
2. **Pattern #1 / F3** used "verify"/"auditable" language that implied more than the
   grounding checks actually establish — they confirm a cited string exists (and isn't
   over-counted), not that its label is the correct one. Scoped explicitly now.
3. **Pattern #10** stated that RAG anchoring "keeps cross-model comparison meaningful"
   as a confirmed effect, when the cited evidence only demonstrates the problem it's
   meant to address, not that the mechanism solves it — reframed as a hypothesis, with
   the dynamic anchors' unvalidated-feedback-loop risk made explicit rather than
   implied only by omission.

The review's overall assessment: the architecture description and code references hold
up; the main weakness was evidence language — several claims generalised from a small
number of runs without clearly separating "observed once" from "reproducibly tested."

**Round 2 (same reviewer, same day):** three further issues, same pattern — precision
of what's actually checked/measured, not architectural errors:

4. **Pattern #1** still bundled all three grounding validators as checking both
   existence and occurrence-count inflation; only `_validate_quote_grounding` (for
   `detected_techniques`) checks the count. `_validate_manipulation_target_grounding`
   and `_validate_stroemung_grounding` only check existence. Scoped per-validator now.
5. **F4** claimed "zero difference between mirrored texts" for the DK-Index
   unconditionally; `bias-validation.md`'s Test 01 shows Claude (CLI) at Δ=-0.07 on
   that specific synthetic test, not 0.00 — only the local models hit exactly zero
   there, though real-article tests 02/03 do show 0.00 for all models tested.
6. **F8** claimed quote_amplification_index and the DK-Index share "the same shape" of
   banded calibration; `pass2.md` only anchors DK's two extremes (HIGH/LOW), with no
   defined middle bands the way Orwell and quote_amplification_index have. Corrected,
   and reframed as a deliberate design difference rather than an inconsistency to
   smooth over (see Round 3 below for a further correction to this same entry).

**Round 3 (same reviewer, same day):** two more precision points, both confirmed:

7. **F8** (again) — the corrected entry still claimed the DK explanation requirement
   "does the calibration work" a middle band would otherwise do. Not technically true:
   `dunning_kruger_explanation` is unvalidated free text — no quote required, nothing
   in `analyzer.py` checks it names an actual pattern rather than just restating the
   score. It can help a human reader, but it's not a code-enforced substitute for a
   defined band.
8. **F3** — "traced back to a specific, existence-checked location in the source text"
   was ambiguous about *which* text. `_validate_quote_grounding` checks
   `detected_techniques` quotes against `pass1_text` (anonymised and quote-stripped),
   not the original article — now stated explicitly, and pattern #1's mechanism
   description was tightened the same way (it runs against a different text than the
   two grounding functions for `manipulation_targets`/`politische_stroemung`, which
   check against the full `article.text`).
