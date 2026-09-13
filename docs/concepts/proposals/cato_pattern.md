# Cato Pattern — Concept

## Core Idea

Detect when an outlet repeatedly assigns the same narrative role (most notably
**Feind**/enemy, but symmetrically also **Held**/hero) to the same entity
across articles whose topic area (`themenbereich`) has nothing to do with
that entity — i.e. the role is inserted regardless of subject, rather than
being relevant reporting on that specific topic.

This is a **cross-article, corpus-level** signal. It cannot be measured from
a single article's `orwell_index` or `bernays_score`, both of which are
deliberately scoped to one article at a time. A single brief aside is, by
design, not supposed to move a single article's score much (see the
"Indirect enemy-image rule" and its proportionality clause in
[`pass1.md`](../../../src/news_analyser/prompts/system/pass1.md)) — but the same
aside, repeated across many otherwise unrelated articles, is itself a
distinct manipulation pattern that the per-article indicators are not meant
to catch.

**Named after** Cato the Elder's *"Ceterum censeo Carthaginem esse
delendam"* ("Furthermore, I consider that Carthage must be destroyed") —
reportedly appended to unrelated Senate speeches on entirely different
topics, making it perhaps the oldest documented example of this exact
pattern: inserting a fixed antagonist into discourse regardless of subject.

---

## Motivating Example

Manual comparison of two articles (2026-09, see project notes):

| | DW — "Digitale Datenkraken" | taz — Ryuichi Sakamoto exhibition review |
|---|---|---|
| Topic | Big Tech data collection (`Technologie`) | Art exhibition (`Kultur`) |
| Enemy image | Central, developed across the whole article, partly via an amplified expert quote | One brief aside: *"Angesichts der reaktionären gesellschaftspolitischen Umwälzungen in Deutschland…"* |
| `orwell_index` (single article) | 0.7 (correctly high — sustained, central framing) | 0.2–0.4 (correctly low — one isolated clause, per the proportionality rule) |
| The actual concern | — | The *same* enemy reference reportedly recurs across nearly every taz article checked, regardless of topic, including topics as unrelated as an art review |

Both per-article scores are arguably correct in isolation. The manipulation
DW's single article performs is concentrated and visible within that one
piece. The manipulation the taz pattern (if confirmed at scale) performs is
distributed — individually invisible, cumulatively significant. Fixing the
per-article prompt further would not surface this; it requires aggregating
across the corpus.

---

## Data Already Available

No new extraction is needed. Every stored article already carries:

- `manipulation_targets[].entity` — free-text entity name (Pass 2)
- `manipulation_targets[].rolle` — one of `Sündenbock | Opfer | Held | Feind | Bedrohung | Autorität | Nutznießer | Versager | Täter | Sonstiges`
- `themenbereich` — one of `Politik | Außenpolitik | Wirtschaft | Gesellschaft | Justiz | Gesundheit | Klima | Kultur | Technologie | Sonstiges`
- `domain`

See [`reference.md`](../../reference/reference.md) for the full schema.

---

## Mechanism

1. **Group** `manipulation_targets` by `(domain, entity, rolle)`.
2. **Count** the number of *distinct* `themenbereich` values in which that
   `(entity, rolle)` pair occurs for that domain.
3. **Rank** descending by distinct-topic count — the widest topic spread
   surfaces first. A pair confined to one or two topically-adjacent
   categories (e.g. `Feind` only within `Politik`/`Außenpolitik`) is
   unremarkable; a pair spanning `Politik`, `Kultur`, `Gesundheit`, and
   `Wirtschaft` is the pattern this concept targets.
4. **Symmetric by design:** the same mechanism applies to both negative
   roles (`Feind`, `Bedrohung`, `Sündenbock`) and positive roles (`Held`,
   `Autorität`, `Nutznießer`) — a persistent hero narrative inserted across
   unrelated topics is the same phenomenon as a persistent enemy narrative,
   just the other valence. This mirrors the direction-neutral design already
   used for the Orwell-Index and DK-Index (see
   [`analyse_architektur.md`](../../reference/analyse_architektur.md)).

### Entity Normalisation Problem

Grouping on the raw `entity` string works for named, consistently-phrased
entities (`AfD`, `USA`, a specific politician's name). It breaks down for
**abstract or collective concepts that get phrased differently across
articles** — e.g. a recurring `Held` framing for "linke Zivilgesellschaft"
in one article, "linksautonome Zentren" in another, "selbstverwaltete
Freiräume" in a third. Grouped on the raw string, each phrasing individually
stays below any visibility threshold even though the underlying pattern is
strong.

This is the same normalisation problem `_DEPENDENCY_ENTITIES` already solves
in `stats.py` for geopolitical/party entities (multiple keyword phrasings →
one canonical bucket, see [`publisher_profiling.md`](../../reference/publisher_profiling.md)
Feature 2). The proposed fix follows the same pattern:

- A curated, hand-maintained keyword-bucket dict (e.g.
  `_ROLE_ENTITY_BUCKETS`), mapping a canonical concept label to a list of
  phrasings that should be treated as the same entity for this analysis.
  Named entities not matched by any bucket keep using their raw string.
- **Trade-off:** simple, transparent, consistent with the existing
  publisher-profiling mechanism — but requires manual curation and will miss
  phrasings not yet added to the list. Curating the initial bucket list is
  domain knowledge, not something derivable from the code.
- **Future upgrade path:** semantic similarity clustering (the same
  approach already used for technique normalisation in
  `technique_store.py`, cosine similarity against a threshold) would catch
  novel phrasings automatically, at the cost of transparency and added
  infrastructure. Not needed for a first version.

---

## Proposed Output

```json
{
  "domain": "taz.de",
  "entries": [
    {
      "entity": "linke Zivilgesellschaft",
      "rolle": "Held",
      "distinct_themenbereiche": 6,
      "themenbereiche": ["Politik", "Kultur", "Gesundheit", "Wirtschaft", "Justiz", "Sonstiges"],
      "artikel_count": 14
    },
    {
      "entity": "AfD",
      "rolle": "Feind",
      "distinct_themenbereiche": 2,
      "themenbereiche": ["Politik", "Außenpolitik"],
      "artikel_count": 22
    }
  ]
}
```

Backend: new function `cato_pattern(df)` in `src/news_analyser/stats.py`,
exposed via a new `GET /stats/cato` route in `backend/routers/stats.py`
(pattern matches `GET /stats/publisher`).

Frontend: a new section in `stats-publisher.component` (entity/bucket, role,
topic-spread count, topic chips), since this is conceptually an extension of
the existing per-publisher profiling view rather than a standalone page.

---

## Open Questions / ToDo

- [ ] Curate the initial `_ROLE_ENTITY_BUCKETS` keyword list — needs
      domain-specific input on how each outlet's recurring narrative roles
      are typically phrased (starting point: "linke Zivilgesellschaft",
      "selbstverwaltete Orte"/"Freiräume" for the taz case)
- [ ] Decide a minimum-visibility threshold (e.g. minimum article count or
      minimum distinct-topic count before an entry is surfaced) to avoid
      noise from low-volume entities
- [ ] Implement `cato_pattern()` in `stats.py`
- [ ] Add `GET /stats/cato` route
- [ ] Add frontend section to `stats-publisher.component` + model/service updates
- [ ] Document the new endpoint in [`reference.md`](../../reference/reference.md) and
      [`web_architecture.md`](../../reference/web_architecture.md) once implemented
- [ ] Evaluate whether semantic normalisation (vs. keyword buckets) becomes
      necessary once real data shows how much phrasing variance exists
