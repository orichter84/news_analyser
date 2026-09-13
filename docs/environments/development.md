# Development Environment — Not Yet Created

**Status:** Does not exist yet. Placeholder for a planned addition.

## Background

There are currently only two environments in practice: [local](local.md) (individual,
ad-hoc use on a developer's own machine — what this whole project has been developed
and tested against so far) and [server](server.md) (the running production instance,
which today is set up the same way as local).

A proper development environment — distinct from both "one-off local testing" and
"the production server" — does not exist yet. For completeness (and because a
colleague raised the point that the project's setup should be transparently
traceable, see the [decisions log](../concepts/README.md)), it should be created.

## Open Questions

- What should distinguish "development" from "local"? Candidates: a shared/staging
  ChromaDB instance with realistic test data, a separate `.env` profile, or a
  dedicated deployment that mirrors the server without touching production data
- Should development run against a subset or snapshot of production data, or stay
  fully synthetic?
- Does this need its own feed-grabber instance, or is on-demand analysis (`--url`,
  `--text-file`) sufficient for a dev environment?

## ToDo

- [ ] Decide what "development" means for this project (see open questions above)
- [ ] Set it up
- [ ] Replace this placeholder with the actual environment documentation
