# 0006 — Recognise Indirect Enemy-Image Construction in Pass 1

**Date:** 2026-09-07/08 (`22296bb`) · **Status:** Active

## Context

Comparing two articles after [0005](0005-quote-amplification-index.md) still showed a
gap: a DW piece built an explicit enemy image ("Group X = enemy") and correctly scored
0.7, while a taz piece built the *same kind* of enemy image indirectly, through an
attribution chain ("Group B has property C, therefore enemy") compressed into a single
aside in an otherwise unrelated article — and scored 0. This wasn't a quoting issue
(see 0005); it was the author's own voice, just structured indirectly rather than
stated directly. Pass 1 only recognised the direct form.

## Decision

Add an explicit rule to `pass1.md` so the indirect/associative pattern counts too,
including when it is a single brief clause, the antagonist is referred to only by
category rather than by name, or the text assumes the reader already knows who is
meant without introducing them.

A proportionality clause keeps a single isolated instance in the 0.2–0.4 range rather
than jumping to the 0.7+ band reserved for sustained, developed enemy narratives — a
one-sentence aside in an art review should not score like an entire article devoted to
the topic.

## Consequences

- Verified against the motivating taz article: score moved from 0 to 0.4 (test run via
  the `cli`/Claude adapter), landing at the top of the predicted range rather than
  jumping to DW's level.
- Whether the *same* enemy reference recurring across many otherwise-unrelated taz
  articles is itself a distinguishable manipulation pattern is a separate,
  corpus-level question — not something a single article's score should try to
  capture. See [cato_pattern.md](../proposals/cato_pattern.md) (not yet implemented).
