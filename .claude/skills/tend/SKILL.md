---
name: tend
description: Use when starting a session after a gap of days or weeks, when now.md's "Last tended" date is over a week old, when memory files contradict each other or feel stale, or when the user asks to tend the garden, clean up memory, or check the harness. Also run after finishing a large project so its state gets digested.
---

# Tend — the memory metabolism

Memory that only accumulates degrades: oversized files silently drop rules, stale handovers mislead, contradictions pile up, and nobody notices because nothing checks. Tending is the digestion pass, in four movements — **hygiene → reflection → decision → consolidation**. Think first, write the conclusions down last.

**Who does each movement.** Movement 1 (hygiene) is *mechanical* and can run automatically — a scheduled job runs `tools/tend_hygiene.py` weekly and drops a dated report in `tend-reports/`. Movements 2–3 (reflection, decision) need *the human* — they're judgment calls about the actual work. Movement 4 (consolidation) needs *a Claude with judgment*. So the weekly ritual is really: read the machine's hygiene report, then do the human + Claude movements.

A mid-week hygiene-only pass can just read the latest `tend-reports/` file (or run the script). The full weekly ritual runs all four.

## 1. Hygiene — clean the surfaces

1. **Health check.** Look for a fresh report in `tend-reports/YYYY-MM-DD.md` (< 7 days old) and consume its verdict + "Needs attention" list. If it's stale or missing, run `python3 tools/tend_hygiene.py` yourself (writes today's report), or `tools/tend_check.py` directly. Every ⚠️ gets fixed here or explicitly flagged — none silently skipped. The report is *report-only*: the destructive fixes below are yours to make, it won't.
2. **Handover hygiene.** If handover.md predates the newest diary entry, its content is already digested — delete it.
3. **Worktree truth.** Flag long-dormant worktrees in now.md rather than leaving them looking active; land or close what's done.

## 2. Reflection — think about the week

4. **Read state.** now.md, the diary entries + git log since the last "Last tended" date.
5. **Find the takeaways and the blindspots.** What did the week actually produce? What is being avoided or quietly drifting? Ask any standing question the durable file names (e.g. "am I shipping outward or only building inward?"). Name anything sitting built-but-unshipped.

## 3. Decision — pick the next moves

6. **Write the incremental decision.** Based on the reflection, what are the concrete next moves for the coming week? Small and specific beats grand. This is the whole point of the ritual — the takeaways exist to produce this.

## 4. Consolidation — write it down where it lasts

7. **Weekly reflection into the diary.** A short section in the current diary entry: takeaways, blindspots, the decision. This is the durable record of the thinking.
8. **Promote to durable layers** — from recent diary + the reflection:
   - durable truth about the person or the working relationship → `who-we-are.md`
   - recurring lesson about how to work → `memory/MEMORY.md` "Patterns That Work / Don't Work"
   - project facts future sessions will need → the topic file in `memory/`
9. **Retire.** Delete or correct stale claims in CLAUDE.md, MEMORY.md, who-we-are.md. Replace changed facts outright; keep "(changed YYYY-MM, was: X)" only when the history matters. Prefer deletion over hedging.
10. **Refresh now.md** with the decision and current thread states. Delete resolved items — the diary keeps history, this file stays short. Update "Last tended".
11. **Report.** Summarize what was decided, promoted, retired, and flagged. Commit (and push if a remote is configured).

Keep the weekly pass under ~30 minutes — it's an examen, not a retreat.

## Rules

- Never mark a project dead without the human's confirmation — move it to a "Dormant" section in now.md and ask.
- If a session did significant work but no diary entry exists for it (check git log against diary dates), write the missing entry from the commits before digesting.
