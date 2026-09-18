# Concepts, Validation & Decisions

This is the "how did we get here" area of the documentation — the connective tissue
between motivation, experiment, and implementation that used to live only in Git
commit messages and scattered conversations.

- **[`decisions/`](decisions/)** — one file per significant architectural decision
  (context → decision → consequences → status), in chronological order below. Read
  top to bottom for a narrative of how the analysis pipeline evolved.
- **[`proposals/`](proposals/)** — concept write-ups not yet decided or implemented.
  A proposal graduates into a `decisions/` entry once it's actually built (or
  explicitly rejected) — it doesn't get rewritten in place.
- **[`validation/`](validation/)** — empirical tests and evidence (symmetry tests,
  calibration runs) that motivated or supported a decision. Referenced from the
  relevant decision entries rather than duplicated.

## Timeline

| # | Decision | Date | Status |
|---|---|---|---|
| [0001](decisions/0001-pass0-group-detection-and-quote-stripping.md) | Pass 0 group detection + quote stripping for a group-blind Pass 1 | 2026-06 | Active |
| [0002](decisions/0002-abandon-unified-gender-anonymization.md) | Abandon a unified NER + gender-anonymisation pass | 2026-06-16 | Rejected / superseded |
| [0003](decisions/0003-separate-bernays-and-orwell-metrics.md) | Separate Bernays Score and Orwell Index as independent metrics | 2026-05-22 | Active |
| [0004](decisions/0004-add-dunning-kruger-index.md) | Add the Dunning-Kruger Index | 2026-05-22 | Active |
| [0005](decisions/0005-quote-amplification-index.md) | Quote Amplification Index as a second source for `orwell_index` | 2026-09-06/07 | Active |
| [0006](decisions/0006-indirect-enemy-image-rule.md) | Recognise indirect enemy-image construction in Pass 1 | 2026-09-07/08 | Active |
| [0007](decisions/0007-manipulation-target-grounding.md) | Require grounding for `manipulation_targets` rolle/direction | 2026-09-13 | Active |
| [0008](decisions/0008-gemini-orwell-index-recalibration.md) | Recalibrate Pass 1/2 prompts against Gemini overreacting on orwell_index and technique counts | 2026-09-14/15 | Active |
| [0009](decisions/0009-pipeline-hardening-after-gemini-meta-review.md) | Pipeline hardening: stroemung grounding/normalization, technique dedup, Bernays denominator, DK explanation | 2026-09-15 | Active |
| [0010](decisions/0010-quote-amplification-grounding-and-debug-run-history.md) | Quote Amplification grounding, institutional-motive carve-out, debug run history | 2026-09-16 | Active |
| [0011](decisions/0011-strict-stroemung-grounding.md) | Require a verifiable quote for every non-`neutral` politische_stroemung label | 2026-09-16 | Active |
| [0012](decisions/0012-technique-negation-guard-and-anchor-stroemung-flattening.md) | Extend the negation guard to technique normalization; fix anchor politische_stroemung storage | 2026-09-18 | Active |

Not every historical decision is captured yet — this started 2026-09-13 with a
handful of foundational and recent milestones rather than a full retroactive rewrite
of the Git history. Add a new entry for each future decision that changes how the
pipeline scores or structures its analysis; smaller implementation details don't need
one — the commit message is enough for those.

## Open Proposals

See [`proposals/`](proposals/) for concepts not yet decided:
[fact_check.md](proposals/fact_check.md) ·
[cato_pattern.md](proposals/cato_pattern.md) ·
[konzept_hybrid_technik_erkennung.md](proposals/konzept_hybrid_technik_erkennung.md) ·
[postgres_migration.md](proposals/postgres_migration.md) ·
[project_structure.md](proposals/project_structure.md)
