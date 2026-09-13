# Server Environment — Current State

**Status:** Documented as-is, expected to change. The server setup is not yet in a
final state — treat this as a snapshot, not a stable reference. Update this file
whenever the actual setup changes rather than letting it drift.

## Current Setup

The production server runs the same stack as [local](local.md) — there is currently
no separate deployment process, containerisation, or process supervisor beyond what
`start.sh` already does. ChromaDB, backend and frontend are started the same way as
in local development.

The RSS feed grabber runs continuously in `--feed --auto` mode (see
[local.md](local.md#8-rss-feed-collector-optional)), which is the main practical
difference from a local dev session — locally the feed grabber is usually run
on-demand or not at all, on the server it runs unattended.

## Monitoring

The `/system` page (see
[web_architecture.md](../reference/web_architecture.md#system-status-system)) gives a
live view of backend/ChromaDB/feed-grabber health and tails the log files under
`logs/` (`app`, `chroma`, `backend`, `frontend`). This is currently the only
monitoring in place — there is no external alerting.

## Known Gaps

- No process supervisor (systemd, pm2, or similar) — if a process dies outside of
  what `/system` polls for, nothing restarts it automatically
- No documented deployment/update procedure (how a new commit gets onto the server)
- ChromaDB crashed unexpectedly on 2026-08-27 with no clear root cause identified;
  see [postgres_migration.md](../concepts/proposals/postgres_migration.md) for the
  (currently undecided) discussion of whether that motivates replacing ChromaDB
- No backup/restore procedure documented for `data/chroma_db`

## ToDo

- [ ] Decide on and document a real deployment/restart procedure
- [ ] Add process supervision so crashed services (esp. ChromaDB, per the known
      2026-08-27 incident) restart automatically
- [ ] Document backup strategy for `data/chroma_db`
- [ ] Revisit this document once the server setup work mentioned in
      [decisions](../concepts/README.md) is done — this is explicitly a snapshot of
      an interim state, not a target architecture
