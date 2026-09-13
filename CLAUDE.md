# Working Rules for Claude Code

## Documentation

All project documentation lives under `docs/`, organised by category — see
[`docs/index.md`](docs/index.md) for the full index. Keep it up to date as part of
the change itself, not as a follow-up:

- **Architectural decisions** — anything that changes how the pipeline scores or
  structures its output (indicator computation, prompt logic, validation behaviour):
  add a new entry to `docs/concepts/decisions/` (see existing entries for the
  template: Context → Decision → Consequences → Status) and list it in the timeline
  table in `docs/concepts/README.md`. Small implementation details don't need one —
  the commit message is enough.
- **New concept proposals** (not yet decided or implemented) go in
  `docs/concepts/proposals/`. Once a proposal is actually implemented or rejected, it
  graduates into a `docs/concepts/decisions/` entry — don't rewrite the proposal file
  in place to make it look like it always described the final state.
- **Reference docs** (`docs/reference/*.md`) must describe the system as it
  currently exists, not as it was designed or is planned to become. If a change makes
  any part of `reference.md`, `analyse_architektur.md`, `web_architecture.md`, or
  `publisher_profiling.md` inaccurate, update it in the same piece of work.
- **`docs/environments/server.md`** is an explicit snapshot of an interim setup, not
  a target architecture — update it whenever the actual server setup changes, rather
  than letting it drift.
- **New top-level docs or categories** need a link added in `docs/index.md`.
