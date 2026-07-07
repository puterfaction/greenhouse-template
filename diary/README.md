# The diary — what happened

This is the chronological layer: one entry per significant session, append-only. The
diary is where history lives so that `now.md` doesn't have to hoard it — resolved
threads get *deleted* from now.md precisely because the diary remembers them.

## Conventions

- **One file per entry**, named `YYYY-MM-DD.md` (add a suffix like
  `YYYY-MM-DD-topic.md` if a day has multiple entries).
- **Write it before the session ends**, not after. An entry written with full context
  beats a reconstruction from a compacted transcript every time. If a session runs
  long, update the diary mid-session — the PreCompact handover is a safety net, not
  the primary strategy.
- **Include the agent's perspective, not just a task log.** What surprised it, what it
  would do differently, what it noticed about the work or the collaboration. This is
  the design decision that makes the diary worth reading: a log says *what* happened,
  a perspective says *what it was like* — and the next session inherits judgment, not
  just facts.
- **The diary is shared.** Both the human and the agent write here. It reads best when
  it's a record of a collaboration, not a changelog.
- **Don't read the whole diary at session start.** That's what now.md is for. Dip into
  the diary only when you need deeper history on a specific thread.

The `/tend` pass digests recent entries: durable truths get promoted up to
`memory/` or `who-we-are.md`, and the entries themselves stay put as the permanent
record.

The file `2026-01-02-example.md` is a **fictional worked example** (continuing the
"Pantry" storyline from `now.md`) so you can see the shape. Delete it and write your
own.
