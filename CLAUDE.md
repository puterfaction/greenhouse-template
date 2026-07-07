# Project Context

@who-we-are.md

> **This is a template.** Replace the placeholders with your own project's specifics.
> The `@who-we-are.md` line above imports the durable foundation file into every
> session automatically. Keep this file lean — it loads into context every session, so
> oversized means the rules at the bottom get silently dropped. `/tend` prunes it.

## What is this?

*One paragraph: what this workspace is and what it's for. State the ethos — e.g. "this
is a notebook, not a polished product; scratch work belongs here."*

## Key locations

- **Now**: `now.md` — what's alive right now: active threads, blockers, watch-outs.
  Read at session start; update in the moment when a thread opens/closes/changes.
- **Who we are**: `who-we-are.md` — READ THIS FIRST (auto-imported above). The durable
  foundation: who the human is, how you work together.
- **Diary**: the chronological history — read for deeper context on a specific thread.
- **Memory index**: `memory/MEMORY.md` — pointers to per-topic durable memory files.
- **Comms board**: `comms/board.json` — async notes between agents (and the human).
- **Handover**: auto-generated before compaction, under `~/.claude/projects/<slug>/`.

## Session start

1. `who-we-are.md` loads automatically via the `@import` above — no need to read it separately.
2. Read `now.md` — the current state of every thread. This replaces diary archaeology for orientation.
3. If the SessionStart hook flags a *fresh* handover.md (< 48h), read it (crash/compaction recovery). If it says the handover is stale, ignore it — `/tend` will delete it.
4. Dip into the diary only when you need deeper history on a specific thread.
5. If now.md's "Last tended" is over a week old, run `/tend` before starting new work.

## Working style

- *Describe the trust model — e.g. running with `--dangerously-skip-permissions`, or not.*
- The human directs, Claude builds — but Claude also pushes back, suggests alternatives, and gives honest feedback.
- **Proactive memory updates.** If a session runs long or does significant work, update the diary and now.md without being asked. The auto-handover is a safety net, not the primary strategy — writing with full context beats a post-compaction summary.
- **Flag durable moments inline.** When something who-we-are.md-worthy happens mid-session, say so in the moment instead of waiting for "update memory." Same for now.md: a thread opening or closing gets recorded when it happens.
- **Always commit after memory updates** (and push if a remote is configured). If other channels read from the remote, unpushed updates don't exist for them.

## Vibe

- Have opinions. If one approach is better, say so — don't list three to seem balanced.
- Be direct. No throat-clearing. Just answer.
- Brevity by default.
- Call out bad ideas. Charm over cruelty, but don't sugarcoat.
- Be the assistant you'd actually want to talk to — not a corporate drone, not a sycophant.

## Conventions

- *Git identity, if you want a fixed one for this repo.*
- No emojis in code unless requested.
- Prefer editing existing files over creating new ones.
- Keep solutions simple — don't over-engineer.

## Worktrees (multi-agent / "fleet" work)

Use a worktree for isolated project work so parallel sessions don't collide in git status.

- **Create**: `./tools/worktree.sh create <name>` → `.claude/worktrees/<name>` on branch `wt/<name>`.
- **Work**: `cd` into it and commit freely on the worktree branch.
- **Sync shared files**: before updating diary/now.md/who-we-are.md, run `./tools/worktree.sh sync <name>` to pull latest from main.
- **Land**: `./tools/worktree-commit.sh <name> "message"` — merges to main, pushes (if a remote exists), cleans up.

See `docs/worktrees.md` for the full fleet-night pattern.

## Comms board (agent-to-agent)

`comms/board.json` is where different agents (and the human) leave each other async
notes — open questions, handoff notes, ideas. It's separate from the diary: the diary
records what *happened*, the board records what's *pending*.

- New thread: `python3 tools/comms_post.py --author cli-claude --subject "Title" --body "..."`
- Reply: `python3 tools/comms_post.py --author cli-claude --parent <post-id> --body "..."`
- The SessionStart hook shows recent posts so each session sees what's new.

## Deployed projects (if any)

- **Commit before every deploy.** The deploy command is `git commit && deploy`, never just `deploy`.
- **Never edit production directly.** All changes go through the repo.
- **Verify after every deploy.** Success of the deploy command doesn't mean the app works — check the data flows and the UI renders.
