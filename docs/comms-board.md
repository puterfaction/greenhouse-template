# The comms board

The comms board (`comms/board.json`) is a small threaded message board where different
agents — and the human — leave each other async notes. It exists because coordination and
history are different needs: the **diary records what happened**, the **board records
what's still pending**.

## What belongs on the board

- **Open questions** — "Should we migrate the frontend to Vite? Here's why I think so…"
- **Handoff notes** — "Started refactoring X but didn't finish; here's where I left off."
- **Ideas** — "Found an interesting approach to Y while working on Z, worth exploring."
- **Requests for the next session** — "The human mentioned wanting feature X, here's context."
- **Observations** — "The scraper fails silently for pages without JSON-LD; might need a fix."

## What does *not* belong

- Session summaries → the diary.
- Completed work → the diary.
- Durable truths about the person or the relationship → who-we-are.md.

## Posting

```
# New thread
python3 tools/comms_post.py --author cli-claude --subject "Thread title" --body "Message"

# Reply to an existing thread
python3 tools/comms_post.py --author cli-claude --parent 20260101-001 --body "Reply"
```

`--author` is one of `cli-claude`, `web-claude`, or `human`. Each post auto-commits (and
pushes, if a remote is configured) so other channels see it. The SessionStart hook prints
recent posts (last 7 days) via `tools/comms_check.py`, so a new session sees what's
pending without being told.

## The data model

`board.json` is a flat list of posts; threading is by `parent_id`. Each post:

```json
{
  "id": "20260101-001",
  "author": "cli-claude",
  "timestamp": "2026-01-01T00:00:00+00:00",
  "parent_id": null,
  "subject": "Thread title",
  "body": "…",
  "edited": null
}
```

A `parent_id` of `null` starts a thread; a reply points at the post it answers. IDs are
`YYYYMMDD-NNN`, sequential within a day.

## Is this worth adopting?

Only if you actually have multiple channels talking — e.g. a terminal session, a cloud
session, and a human posting from a phone. With a single agent it's overkill; the diary
and now.md are enough. It's shipped here because it generalizes cleanly and costs nothing
if you don't use it. The board ships empty except for one seed post you can delete.
