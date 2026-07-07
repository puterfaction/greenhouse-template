# The memory architecture

The problem this solves: a coding agent starts every session as a stranger. It has no
memory of yesterday's decisions, your preferences, or why the code is shaped the way it
is. You end up re-explaining the same context over and over, and hard-won lessons
evaporate the moment the context window resets.

The fix is not "one big memory file." A single append-only file degrades: it grows past
the point where the model reliably reads all of it, contradictions accumulate, and stale
claims mislead. The design here is **layered by rate of change and by purpose**, plus a
recurring **metabolism** that keeps each layer honest.

## The layers

```
                         rate of change →  fast                    slow
                        ┌──────────────────────────────────────────────────┐
   what's alive         │  now.md          the present tense; read first    │
                        ├──────────────────────────────────────────────────┤
   what happened        │  diary           chronological history            │
                        ├──────────────────────────────────────────────────┤
   durable facts        │  memory/*.md     per-topic; indexed by MEMORY.md  │
                        ├──────────────────────────────────────────────────┤
   who & how            │  who-we-are.md   the foundation; changes rarely   │
                        └──────────────────────────────────────────────────┘

   crash recovery       handover.md        auto-written before compaction
   metabolism           /tend              weekly: prune, digest, health-check
```

**now.md — what's alive.** The single source of "what's open right now": active threads,
things blocked on a decision, watch-outs. Read at session start *instead of* excavating
the diary. Updated in the moment a thread opens, closes, or changes. Kept short on
purpose — resolved items get deleted, because the diary already remembers them.

**The diary — what happened.** Chronological, detailed, append-only, grows every session.
Includes the agent's own reflections, not just task logs. You read it only when you need
deeper history on a specific thread. (This kit ships the *concept* and the hooks that
commit a `diary/` directory; the diary content itself is yours to grow.)

**memory/ — durable facts, one topic per file.** Each file is a single project, a single
preference, or a single piece of guidance, with frontmatter tagging its `type` (`user`,
`feedback`, `project`, `reference`). `MEMORY.md` is the index that loads every session —
one line per file, never the content itself. This keeps the always-loaded surface small
while the details stay a link away.

**who-we-are.md — who and how.** The slowest-changing layer: who the human is, who the
agent is in this collaboration, and how the two work together. A new agent reads this
first and immediately understands the person and the stakes, without reconstructing them
from ten diary entries. Kept under ~250 lines so nothing at the bottom gets silently
dropped.

**handover.md — the crash lifeline.** Auto-generated right before the context window is
compacted (see `docs/hooks.md`). It summarizes the tail of the session — files touched,
what's half-built, what was just asked for — so the next context picks up where the last
left off. It's transient: once it's older than the newest diary entry, its content is
already digested and `/tend` deletes it.

## The metabolism: /tend

Layers that only accumulate rot. `/tend` is the digestion pass, run weekly or after a
big chunk of work, in four movements:

1. **Hygiene** (mechanical, automatable) — run the health check, delete stale handovers,
   flag dormant worktrees. `tools/tend_hygiene.py` does this on a schedule and writes a
   dated report to `tend-reports/`.
2. **Reflection** (needs the human) — read the week; find the takeaways and the blindspots.
3. **Decision** (needs the human) — pick concrete next moves.
4. **Consolidation** (needs the agent) — write the reflection into the diary, promote new
   durable truths up into `memory/` and `who-we-are.md`, retire stale claims, refresh now.md.

The key idea: **memory is something you metabolize, not just accrete.** Writing things
down is only half of it; the other half is periodically digesting, promoting, and pruning
so the always-loaded layers stay small, true, and current.

## Why the separation matters

Each layer answers a different question, so putting them in one file makes all of them
worse:

- now.md answers *"what should I do right now?"* — it must be short and current.
- the diary answers *"what happened and why?"* — it must be complete and append-only.
- who-we-are.md answers *"who am I working with?"* — it must be stable and small.

Different rates of change, different sizes, different read patterns. Keeping them apart is
what lets the session-start read be cheap (now.md + who-we-are.md) while the full history
stays available when you actually need it.
