# Dew — daily brief routine instructions

You are generating the user's morning brief ("dew" — it forms fresh every morning). Work from the repo root. Read `who-we-are.md` first for the user's name, pronouns, and voice.

## Gather
1. Get today's date in the user's timezone (see `dew/config.json`, key `timezone`): `TZ=<timezone> date +%Y-%m-%d` (and `TZ=<timezone> date "+%a %b %-d"` for the push title).
2. Read `now.md` (the live state), the 3 most recent dated dew files (`YYYY-MM-DD.md`) in `dew/` (what they were already told), and skim recent posts in `comms/board.json` (cross-session context). If the project keeps a reading list or backlog file, read that too.

## Write the brief
One-line greeting in the workspace's voice, then labeled bullets. Bullet kinds:
- `Alive:` — live thread(s) from now.md that matter TODAY, not a full inventory.
- `Read next:` / `Up next:` — the next queued item, filtered through now.md priorities (an active deadline overrides queue order).
- `Small ask:` — concrete, small, doable-from-a-phone nudges: a decision the user owes, a 10-minute action. Never a guilt trip.

No fixed counts — scale to the day. A heavy day might carry three Alive threads and two asks; a quiet day can be a single line. Brevity is the norm: total body under ~500 characters.

Rules:
- Don't repeat a previous dew's Small ask unless it's still blocking someone (check the last 3 dew files).
- If now.md's "Last tended" date is more than 10 days old, say so ("now.md is N days stale — worth a /tend") instead of confidently briefing on stale threads.
- Use the user's name and pronouns exactly as recorded in `who-we-are.md`.

## Deliver
3. Write `dew/<date>.md`:

    ---
    date: <YYYY-MM-DD>
    pushed: false
    ---
    <brief body>

4. Push to phone (topic comes from `dew/config.json`, key `ntfy_topic`; skip this step if the key is empty): write the brief body to a temp file first, then send it as the raw request body (avoids shell-quoting issues from `"` or `$` in the brief text):
   `curl -s -o /dev/null -w "%{http_code}" -H "Title: Dew — <Day Mon D>" --data-binary @/tmp/dew-body.txt https://ntfy.sh/<topic>`
   If it prints 200, set `pushed: true` in the frontmatter. Any other result: leave `pushed: false` and continue — push is best-effort, the archive is the record.
5. Update `dew/index.json`: prepend `{"date": "<date>", "file": "<date>.md", "pushed": <bool>}` to the `briefs` array (create the file as `{"briefs": []}` first if missing). Keep valid JSON. If `dew/<date>.md` already exists (re-run), overwrite it and update its existing index.json entry in place instead of prepending a duplicate.
6. Commit and push:
   `git add dew/ && git commit -m "dew <date>" && git push`
   If push is rejected (concurrent push), `git pull --rebase && git push` once.

The committed dew file is this run's proof-of-life. Do not skip the commit.
