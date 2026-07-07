# The hooks

Hooks are shell commands Claude Code runs automatically at lifecycle events. They live in
`.claude/settings.json`. This kit ships three, and they're what make the memory system
*run itself* instead of depending on you remembering to maintain it.

All three use `$CLAUDE_PROJECT_DIR` — the absolute path to the repo root, which Claude
Code sets for every hook — so nothing is hardcoded to a particular machine. The handover
file lives in Claude Code's per-project transcript directory, `~/.claude/projects/<slug>/`,
where `<slug>` is the repo's absolute path with `/` and `_` replaced by `-`; the hooks
recompute that slug on the fly.

## SessionStart — orient the new session

Runs when a session starts (and, with the `compact` matcher, right after a compaction).

- Reminds you to read `now.md` first.
- Checks `handover.md`: if it's fresh (< 48h) it points you at it; if it's stale it tells
  you to ignore it (a leftover from a previous crash, already digested).
- Lists any active worktrees so you can see parallel work.
- Prints recent comms-board posts via `tools/comms_check.py`.

The `compact`-matcher variant does one extra thing: it prints the whole handover inline,
because a just-compacted session has lost its working memory and needs the summary
injected directly.

## Stop — persist memory on the way out

Runs when the session ends. If any memory file changed (`who-we-are.md`, `now.md`,
`memory/`, `diary/`), it commits them and pushes if a remote is configured. This is the
safety net that means an interrupted session doesn't lose its memory updates — but it's a
net, not the plan. Writing to the diary *with full context during* the session beats a
terse auto-commit at the end.

## PreCompact — write the handover before context is lost

Runs just before Claude Code compacts the context window. It calls
`tools/auto_handover.py`, which:

1. Finds the current session transcript (the newest `.jsonl` in the project dir).
2. Extracts the human/assistant text (skipping tool noise).
3. Trims to the most recent ~40k characters.
4. Pipes that (plus who-we-are.md and the latest diary entry, if present) to `claude -p`
   with a prompt that asks for a specific, file-level handover.
5. Writes the result to `handover.md`.

If the summarization call fails, it falls back to saving the last ten raw messages so
there's always *something* for the next context to read.

## Adapting them

- **The auto-commit identity.** The Stop hook and `comms_post.py` commit with whatever git
  identity the repo is configured with (or `GIT_AUTHOR_NAME`/`GIT_AUTHOR_EMAIL` if set). Set
  `git config user.name` / `user.email` in the repo if you want a fixed one.
- **What counts as a "memory file."** The Stop hook's grep pattern decides which paths get
  auto-committed. Edit it if your durable files live elsewhere.
- **The `claude` binary.** `auto_handover.py` finds `claude` on `PATH`, falling back to
  `~/.local/bin/claude`. Adjust if yours lives somewhere else.

## Scheduling the weekly hygiene pass

The mechanical half of `/tend` can run on a timer so a fresh report is always waiting.

**macOS (launchd):**

```
./tools/install_tend_hygiene.sh
```

This fills the repo path into `tools/tend-hygiene.plist.template` and loads a launchd
agent that runs `tools/tend_hygiene.py` every Saturday at 9am, writing a dated report to
`tend-reports/`.

**Linux (cron):** add a line like this to `crontab -e` (adjust the path):

```
0 9 * * 6  cd /path/to/repo && /usr/bin/python3 tools/tend_hygiene.py >> tend-reports/cron.log 2>&1
```
