# 0008 — Recalibrate Pass 1/2 Prompts Against Gemini Overreacting on orwell_index and Technique Counts

**Date:** 2026-09-14/15 · **Status:** Active

## Context

A routine derStandard interview article (Digitaltrainer, 1159 words, a hedged and
measured expert Q&A about children and AI chatbots) scored `orwell_index: 0.75` with
21 entries in `detected_techniques` (Bernays Score 18.12/1000w) when run through the
production pipeline against Gemini. The same article via the `cli`/Claude adapter
produced a materially lower, more plausible score, pointing at provider-specific
overreaction rather than a genuine property of the article — consistent with the
precedent in [0007](0007-manipulation-target-grounding.md), where Gemini was already
observed to apply soft/graduated prompt instructions less conservatively than Claude.

Tracing the actual debug dumps, stored ChromaDB results, and — critically — asking
Gemini itself to introspect on its own reading of the prompts (twice: once on
`pass1.md`/`pass2.md` as a whole, once specifically on the technique-counting
instability) surfaced several concrete, compounding root causes rather than one bug:

1. The interview Q&A format (`Name: answer text`) bypasses the mechanical
   quote-stripping from [0001](0001-pass0-group-detection-and-quote-stripping.md),
   which only recognises „…"/»…«/"…-marked quotes — the interviewee's own words were
   silently credited to "the article's" rhetorical voice.
2. The indirect-enemy-image rule from [0006](0006-indirect-enemy-image-rule.md) had
   no counterweight against ordinary causal/institutional criticism ("Tech-Konzerne
   haben wirtschaftliche Interessen") — Gemini's own words: *"Ich interpretiere jede
   kritische Ursachenzuschreibung als Beginn einer attribution chain."*
3. `quote_amplification_index` (Pass 2, [0005](0005-quote-amplification-index.md))
   had no proportionality guard mirroring Pass 1's, and its "missing rebuttal"
   criterion fired on single-source interviews merely for having only one voice —
   structurally unsatisfiable by that genre.
4. The counting rule's hard "is WRONG and must be avoided" language dominated its
   own softer exception clause whenever the split-vs-merge threshold was ambiguous —
   Gemini's own account: it optimises against being "caught" violating the
   loudly-stated rule when unsure.
5. "Framing" sits in the technique list as a peer of much more specific techniques
   (Loaded Language, Scapegoating, False Dichotomy) even though it is a meta-effect
   nearly all of them already produce — passages were routinely double-counted once
   under a specific technique and again under "Framing" for the same span.
6. Several smaller issues: Dunning-Kruger-Index conflated terse factual news style
   with epistemic overconfidence; `manipulation_targets` gating implied Pass 2 has
   access to Pass 1's technique list (it doesn't — checked in `analyzer.py`); the
   Pass-2 quote_amplification explanation sentence functioned as meta-priming,
   nudging the model to actively hunt for a way to justify a high score.

## Decision

Revise `pass1.md` and `pass2.md` (no code or schema changes) to close each gap:

- **Interview attribution:** both prompts now explicitly instruct the model to treat
  unmarked `Name: answer text` turns the same as mechanically-stripped quotes.
- **Enemy-image proportionality:** added a "not an enemy image" carve-out requiring
  the framing to cast actor *motive/nature* as malicious — not merely to state a
  causal effect — plus a rule that several separate 0.2–0.4 instances don't sum to
  0.7+, and that persuasive/single-source writing isn't "one-sided" by itself.
- **Quote Amplification Index:** added the same proportionality band, and scoped
  "missing rebuttal" to specific accusations against a *named* party, not the mere
  absence of a second voice in an interview.
- **Counting symmetry:** both failure modes (over-merging, over-splitting) are now
  stated as equally wrong, with a same-argument-one-claim clarification and an
  explicit tiebreak ("count it once" when unsure).
- **Framing as meta-category:** new "one technique per passage" rule — pick the most
  specific applicable technique; use "Framing" only when nothing more specific fits;
  merge entries whose quotes overlap instead of reporting both.
- **Anonymisation charity:** placeholders are now explicitly framed as ordinary
  real-world entities, not adversaries in an abstract game — Gemini reported that
  algebraic placeholders read as more hostile than the named entities they replace.
- **Misc:** DK-Index no longer penalises terse factual statements, only
  interpretive/predictive claims stated as certain; `manipulation_targets` gating no
  longer references a technique list Pass 2 doesn't have; the Pass-2 meta-priming
  sentence was cut down to a factual statement of the `max()` merge.

## Consequences

Verified with 6 repeated local runs against Gemini on the motivating article
(`gemini-2.5-flash` via the production adapter, same text, same prompts each time):

| | Before (single run) | After (average of 6 runs) |
|---|---|---|
| `orwell_index` | 0.75 | 0.56 (range 0.55–0.58) |
| `orwell_index_structural` | — | 0.55–0.58 |
| `quote_amplification_index` | — | 0.10–0.60 |
| Bernays Score | 18.12 | 2.8 (range 1.7–3.5, i.e. ~2–4 techniques) |
| Dunning-Kruger-Index | 0.10 | 0.10–0.20 |

Run-to-run variance dropped substantially (technique count previously swung 3→13
between two identical-prompt runs; now stays within 2–4) but has not been reduced to
zero — some residual instability appears inherent to how Gemini samples this kind of
graduated judgment, not fully removable by prompt wording alone.

**Known limitation, not fixed here:** the interview-turn exclusion remains a prompt
instruction, not a mechanical guarantee — Gemini's own introspection confirmed it
doesn't always hold across a full article. A deterministic fix (detecting and
stripping speaker-labelled interview turns the same way direct quotes are already
stripped, before the text reaches the model) would close this properly; deferred as
a separate, larger change rather than folded into this prompt-only pass.

**Method note:** this recalibration was cross-checked three ways — an independent
GPT review of the diff, and two rounds of asking Gemini itself to introspect on its
own reading of the prompts (once broadly, once specifically on the counting
instability) — each surfaced fixes the others didn't. Relying on a single review
angle would have missed several of the issues above.
