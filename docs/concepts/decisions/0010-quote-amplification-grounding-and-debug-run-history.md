# 0010 — Quote Amplification Grounding, Institutional-Motive Carve-Out, Debug Run History

**Date:** 2026-09-16 · **Status:** Active

## Context

Manually re-running the ADR 0008 motivating article (derStandard "Digitaltrainer"
interview, `gemini-2.5-flash`) four times locally surfaced instability wider than
what ADR 0008 measured after its recalibration:

| | ADR 0008 (6 runs) | This session (4 runs) |
|---|---|---|
| `orwell_index` | 0.55–0.58 | 0.45–0.70 |
| Bernays Score | 1.7–3.5 | 1.79–7.15 |

Since `data/debug_last_run/` is overwritten on every call, only the last of the
four runs could be inspected (`docs/debug_runs/` didn't exist yet). That run
(Orwell 0.70, `orwell_index_structural` 0.65, `quote_amplification_index` 0.70,
Bernays 1.79) showed two separable problems:

1. **`pass1_word_count` (1119) tracked `word_count` (1159) closely** for this
   article — the mechanical quote-stripping barely reduces an interview whose
   turns are unmarked (`Name: Antwort`, the known limitation from
   [0008](0008-gemini-orwell-index-recalibration.md)). So the Bernays swing
   across the four runs is ~100% Pass 1 technique-count sampling noise, not an
   artifact of the [0009](0009-pipeline-hardening-after-gemini-meta-review.md)
   denominator change.
2. **`quote_amplification_index: 0.7` had zero supporting evidence** in the raw
   Pass 2 output — no quote, no explanation, nothing to audit. The most likely
   driver in `manipulation_targets` was `Tech-Konzerne` → `rolle: Bedrohung` on
   the quote *"Sie haben rein wirtschaftliche Interessen. Daten sind Geld."* —
   which is exactly the pattern `pass1.md`'s "What NOT to flag" section already
   protects `detected_techniques` against ("mundane, widely-held concern about
   incentives, not Scapegoating/Victim Framing/Appeal to Fear"), but `pass2.md`
   had no equivalent carve-out for `manipulation_targets`/`quote_amplification_index`.

## Decision

- **`pass2.md` / `analyzer.py` / frontend:** `quote_amplification_index` gets a
  sibling `quote_amplification_explanation` field, required above 0.3 ("if you
  can't name a specific quote, the score can't be above 0.3"). Prompt-only, no
  code-level grounding check or auto-capping — same reasoning as
  `dunning_kruger_explanation` in [0009](0009-pipeline-hardening-after-gemini-meta-review.md):
  visibility first, without introducing a new score-adjustment mechanism that
  could itself misfire.
- **`pass2.md`:** new "Institutional-motive-criticism carve-out" under the
  `manipulation_targets` grounding section, mirroring `pass1.md`'s existing
  one — a single critical remark about an institution's motives/incentives,
  without dehumanising language or a "doing this TO us" narrative, is ordinary
  criticism and doesn't justify a threat-coded `rolle`/`direction` or feed
  `quote_amplification_index`, whether the remark is the author's own or a
  quoted source's. Cross-referenced from the Quote Amplification Index section.
- **`analyzer.py`:** debug dumps now write to both `data/debug_last_run/`
  (unchanged — fixed paths some notebooks depend on) and
  `data/debug_runs/<timestamp>_<domain>/` (new, untouched per-run archive), via
  a `run_id` generated once per `analyze_article()` call.

## Consequences

- Repeated-run investigations like the one that triggered this ADR no longer
  lose their raw data after the next run — every pass's input/output is
  preserved per run under `data/debug_runs/`.
- `quote_amplification_index` scores above 0.3 are now auditable in the UI
  (`article-detail.component.html`), same as `dunning_kruger_index` since
  0009.
- The institutional-motive-criticism carve-out is a prompt-only change; its
  effect on this specific article can only be confirmed by re-running it
  (not done as part of this ADR — the debug-run archive now makes that
  comparison possible going forward).
- Residual Pass 1 technique-count sampling noise (the dominant driver of the
  observed Bernays swing) is unchanged by this ADR — consistent with
  [0008](0008-gemini-orwell-index-recalibration.md)'s conclusion that some
  variance is inherent to how Gemini samples this kind of graduated judgment
  and isn't fully removable by prompt wording alone.
