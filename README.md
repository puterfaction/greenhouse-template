# Greenhouse Starter Kit

A memory system for coding agents that don't remember you.

Every session with a coding agent starts cold. It doesn't recall yesterday's decisions,
your preferences, or *why* the code is shaped the way it is — so you re-explain the same
context on a loop, and the lessons you paid for evaporate when the context window resets.

This kit is a small, opinionated infrastructure that fixes that. It's not a framework or a
dependency — it's a set of templates, scripts, and hooks you drop into a repo so a
stateless agent can show up and *know* the project: what's live right now, what happened
before, what's durably true, and how you like to work.

It's the sanitized, reusable design extracted from a personal workspace called "the
Greenhouse," where it's been in daily use across hundreds of sessions.

## The core idea: metabolize, don't accrete

The naive approach — one big memory file the agent appends to — fails predictably. The
file grows past the point where the model reliably reads all of it, contradictions pile
up, and stale claims quietly mislead. Nothing checks it, so nobody notices.

The design here does two things differently:

1. **Layer by rate of change and purpose.** What's-alive-right-now, what-happened,
   durable-facts, and who-you-are are *different needs* with different sizes and read
   patterns. Splitting them keeps the always-loaded surface small and current while the
   full history stays one link away.

2. **Metabolize on a schedule.** Writing things down is only half the job. A recurring
   digestion pass (`/tend`) prunes what's resolved, promotes new durable truths up to the
   slow layers, retires stale claims, and health-checks every file. **Memory is something
   you digest, not just something you accumulate.**

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

- **`now.md`** — the single source of "what's open right now." Read at session start
  *instead of* excavating history. Kept short; resolved items get deleted.
- **the diary** — chronological, append-only history, including the agent's own
  reflections. Read only for deeper context on a thread.
- **`memory/`** — durable facts, one topic per file (`type: user | feedback | project |
  reference`), indexed by `MEMORY.md`. The index loads every session; the details stay a
  link away.
- **`who-we-are.md`** — the slowest-changing layer: who the human is, who the agent is
  here, and how you work together. Read first, kept small.
- **`handover.md`** — auto-generated right before the context window compacts, so the next
  context picks up mid-thought instead of cold.

See [`docs/architecture.md`](docs/architecture.md) for the full rationale.

## What's in the box

```
CLAUDE.md                     Project instructions template (imports who-we-are.md)
now.md                        "What's alive" template + a fictional worked example
who-we-are.md                 Durable-foundation skeleton to fill in
diary/
  README.md                   The diary layer: conventions for the what-happened tier
  2026-01-02-example.md       Fictional example entry (delete it, write your own)
memory/
  MEMORY.md                   Index of the durable memory files (loads each session)
  example-project.md          Example per-topic project memory
  ship-threshold-example.md   Example "how to work with me" feedback memory
comms/board.json              Empty threaded agent-to-agent message board
.claude/
  settings.json               The three hooks, wired up
  skills/tend/SKILL.md         The /tend metabolism skill
tools/
  tend_check.py               Health check across every memory layer (reports, never fixes)
  tend_hygiene.py             Runs the check, writes a dated report to tend-reports/
  install_tend_hygiene.sh     Installs the weekly launchd agent (macOS)
  tend-hygiene.plist.template Timer definition (paths filled in at install)
  auto_handover.py            PreCompact handover generator
  worktree.sh                 Create/list/sync/remove git worktrees
  worktree-commit.sh          Land a worktree's work back to main
  comms_post.py               Post to the comms board
  comms_check.py              Print recent board posts (used by SessionStart)
docs/
  architecture.md             Why the layers, in depth
  hooks.md                    What each hook does and how to adapt it
  worktrees.md                The multi-agent "fleet" workflow
  comms-board.md              The agent-to-agent board pattern
```

## The automation

Three [Claude Code hooks](docs/hooks.md) make the system run itself instead of relying on
you to maintain it:

- **SessionStart** orients each new session (read now.md, handover freshness, active
  worktrees, recent board posts).
- **PreCompact** writes a specific, file-level `handover.md` before the context window is
  compacted — the lifeline across a reset.
- **Stop** commits (and optionally pushes) any changed memory files on the way out, so an
  interrupted session doesn't lose its updates.

The mechanical half of `/tend` can run on a weekly timer (launchd on macOS, cron on Linux)
so a fresh health report is always waiting.

## Adopting it

1. **Copy the files into your repo.** Everything here is drop-in; there's nothing to
   install and no dependency beyond Python 3, git, and Claude Code.
2. **Fill in the two durable files.** Rewrite `who-we-are.md` for your actual context and
   trim `CLAUDE.md`'s placeholders. These are the foundation — spend real time here.
3. **Start `now.md` and the diary.** Delete the fictional examples (in `now.md` and
   `diary/`), write your real active threads, and write a first diary entry at the end
   of your next real session.
4. **Point the hooks at yourself.** `.claude/settings.json` uses `$CLAUDE_PROJECT_DIR`, so
   it's portable as-is; skim [`docs/hooks.md`](docs/hooks.md) if you want to change what
   counts as a memory file or the git identity.
5. **Schedule the hygiene pass** (optional): `./tools/install_tend_hygiene.sh` on macOS, or
   the cron line in [`docs/hooks.md`](docs/hooks.md) on Linux.
6. **Run `/tend` weekly** (or after any big chunk of work) to keep the layers honest.

The multi-agent worktree workflow and the comms board are optional extras — adopt them
only if you run several sessions at once or across several channels. See
[`docs/worktrees.md`](docs/worktrees.md) and [`docs/comms-board.md`](docs/comms-board.md).

## Design principles, condensed

- **Continuity across stateless sessions is infrastructure, not vibes.** Build the files
  and the automation; don't rely on remembering to update memory by hand.
- **Separate what's-alive from what-happened from who-you-are.** Different rates of change
  want different files.
- **Small always-loaded surface, deep history on demand.** now.md + who-we-are.md + an
  index are cheap to read every session; the diary and per-topic files are there when
  needed.
- **Prune as a first-class action.** An append-only memory silently drops its own rules.
  Deletion and promotion are the point of `/tend`.
- **Let the tooling report but leave the judgment to people.** The health check flags; a
  human reflects and decides; an agent consolidates.

## Not in v1

The private source also runs an experimental **"subconscious" daemon** — a PreToolUse
hook that embeds the memory files and surfaces associatively related memories
mid-session, unprompted. It's deliberately left out of this kit (it's the most
experimental subsystem and needs real generalization work). Planned as an optional
add-on in a later version.

## License

MIT — see [LICENSE](LICENSE).
