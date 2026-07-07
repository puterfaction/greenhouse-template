# The subconscious (optional add-on)

An experimental PreToolUse hook that surfaces memories associatively,
mid-session, without being asked — the way something you wrote weeks ago
nags at the back of your mind while you're doing something unrelated, and
then turns out to be relevant.

It's separate from the tiered memory system (`now.md`, `diary/`, `memory/`,
`who-we-are.md`), which you read *deliberately* at session start. This is
*ambient*: every time the agent reads a file, greps, runs a shell command, or
edits/writes, a small daemon checks whether anything in your memory files is
semantically close to what it's looking at, and whispers it into context if
so.

It's the most experimental piece of this kit. Treat it as an add-on you can
turn on when you're curious and rip out if it's not earning its keep — the
core memory system (now.md/diary/memory/who-we-are.md) works completely fine
without it.

## How it works

A background daemon (`tools/subconscious.py`) loads a small local embedding
model (`sentence-transformers/all-MiniLM-L6-v2`) and holds an index of
embedded chunks from `diary/*.md`, `memory/*.md`, `now.md`, and
`who-we-are.md`. A thin hook script (`tools/subconscious_hook.py`), wired to
`PreToolUse`, sends the daemon a bit of context from whatever tool call is
about to run (a file path, a grep pattern, a shell command), and the daemon
returns up to two memories that scored above a similarity threshold —
formatted as a `<subconscious>...</subconscious>` block that gets injected
into the agent's context.

A cooldown (5 minutes per memory) stops the same thing from being whispered
on every single tool call, and a per-query cap (2 memories) keeps it from
flooding context.

Everything stays local — the embedding model runs on your machine, nothing
is sent anywhere.

## Install

```
pip install sentence-transformers numpy
```

First run downloads the model (~90MB) from Hugging Face; after that it's
fully offline. Both `subconscious.py` and `subconscious_hook.py` import
`sentence_transformers`/`numpy` lazily, inside the functions that need them —
so `--status`, `--stop`, and the hook's fast-exit path all work even before
you've installed anything.

## Build the index

Before starting the daemon, build the embeddings index from your memory
files:

```
python3 tools/subconscious.py --index
```

This parses `diary/*.md` (split into `##`-headed sections, like a diary
entry's own subsections), `memory/*.md` (chunked per file), and `now.md` /
`who-we-are.md` (chunked whole-file), embeds anything new or changed, and
writes `tools/subconscious_index.json`. Re-run it any time those files change
significantly — it caches embeddings by content hash, so it only re-embeds
what actually changed.

## Commands

```
python3 tools/subconscious.py --index      # (re)build the embeddings index
python3 tools/subconscious.py --start       # start the daemon in the background
python3 tools/subconscious.py --stop        # stop it
python3 tools/subconscious.py --status      # check whether it's running
python3 tools/subconscious.py --reload      # daemon re-reads subconscious_index.json
```

`--reload` is cheap — it just re-reads the index file the daemon already has
loaded. It does **not** rebuild the index; run `--index` first if the memory
files changed, then `--reload` to pick it up without restarting the daemon.

## Wiring up the hook

Add a `PreToolUse` entry to `.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Read|Grep|Bash|Edit|Write|Glob",
        "hooks": [
          {
            "type": "command",
            "command": "python3 $CLAUDE_PROJECT_DIR/tools/subconscious_hook.py"
          }
        ]
      }
    ]
  }
}
```

You'll usually also want to start the daemon from `SessionStart`, e.g.
appending `python3 $CLAUDE_PROJECT_DIR/tools/subconscious.py --start` to your
existing SessionStart hook command — see [`docs/hooks.md`](hooks.md) for how
this kit's other hooks are structured.

## Tuning the threshold

`SIMILARITY_THRESHOLD` (default `0.42`) was tuned on the source workspace's
corpus — several hundred diary and memory chunks accumulated over months. A
fresh, small memory set behaves differently:

- **Too few sources / short files** → cosine similarity scores run lower
  across the board; you may see nothing surface. Lower the threshold (try
  0.35) once you have real content in `diary/` and `memory/`.
- **Noisy or repetitive memory files** → more false-positive surfacings.
  Raise the threshold (try 0.5) or prune the underlying files (that's what
  `/tend` is for).

`MAX_MEMORIES_PER_QUERY` (2) and `COOLDOWN_SECONDS` (300) are the other two
knobs — both are plain constants at the top of `subconscious.py`.

## Socket, PID, and log paths

All per-repo: `subconscious.py` hashes the repo's absolute path and uses
`/tmp/subconscious-<hash>.sock`, `.pid`, and `.log`. This means you can run
the daemon for several different repos (e.g. a "Pantry" recipe app and a
side project) at the same time without them colliding — each hook script
recomputes the same hash from its own repo root, so it only ever talks to
its own daemon.

## Is this worth adopting?

Only if you're curious about ambient recall and don't mind the extra moving
part (a background process, a second `pip install`). If the tiered memory
system alone is doing its job — you read `now.md`, dip into the diary when
needed — you don't need this. It's shipped as an opt-in precisely because
it's the subsystem most likely to need retuning per project.
