---
name: example-project
description: Example of a per-topic project memory file — replace with a real one
metadata:
  type: project
---

# Example project — Pantry

> This is a template/example. A `project` memory holds the facts a future session
> needs to pick up an ongoing piece of work: what it is, where it lives, how it's
> deployed, and the runbook. Convert relative dates to absolute. Keep it to what the
> repo and git history *don't* already record.

**What:** Pantry is a recipe-sharing web app (fictional example).

**Where it lives:** `projects/pantry/`. Deployed at `pantry.example.com` (fictional).

**Runbook:** `deploy` from `projects/pantry/` after committing. The database sleeps
after 5 minutes idle; the first request after that is slow — expected, not a bug.

**State:** search rewrite in progress (see [[now]] / branch `wt/search-index`). Ranking
not tuned yet.

**Why it's built this way:** substring search didn't scale past a few hundred recipes,
so we moved to an index — the non-obvious decision worth recording here rather than
rediscovering from the diff.
