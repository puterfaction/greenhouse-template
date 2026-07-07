# Now — what's alive

*The single source of "what's open right now." Read this at session start instead of excavating the diary. Update it in the moment when a thread opens, closes, or changes — don't wait to be asked. `/tend` refreshes it and checks its freshness. The diary is history; who-we-are.md is durable truth; this file is the present tense.*

*Last tended: 2026-01-01 (example)*

---

> **How to use this file.** Keep it short — if it grows past a screen or two, you're
> hoarding history that belongs in the diary. Each section below is a heading plus a
> handful of bullets. Delete resolved items; the diary remembers them. The sections
> are ordered by how live something is: **Active** now, **Green-lit** and **Next up**
> soon, **Horizon** someday, **Watch-outs** always. **Recently landed** is a short
> tail of what just shipped, so a new session sees momentum.
>
> Everything below the line is a **fictional worked example** (a recipe-sharing app
> called "Pantry") so you can see the shape. Delete it and write your own.

---

## Active
- **Pantry search rewrite** — swapping the ingredient search from substring match to a
  proper index; branch `wt/search-index`. Half done: index builds, ranking not tuned yet.
  Next: weight title matches above body matches.
- **Mobile layout bug** — recipe cards overflow on screens < 360px. Reproduced, not fixed.

## Green-lit (decided, not started)
- **Public launch of the meal-planner** — it clears the ship checklist (see memory/ship-threshold-example.md).
  Needs a light copy pass, then announce. This is the next thing to ship, not "someday."

## Next up
- **Import from URL** — paste a recipe link, scrape the structured data. Wanted, not scoped.
- **Shopping-list export** — roll a week's recipes into one grocery list.

## Horizon (ambitions being reeled in)
- **Recommendations** — "you cooked X, try Y." Interesting but needs usage data we don't have yet.

## Watch-outs
- The scraper silently returns zero recipes for sites without JSON-LD — log a warning, don't fail quietly.
- Free-tier database sleeps after 5 min idle; first request after that is slow. Known, not a bug.

## Recently landed
- 2026-01-01 — set up the three-tier memory system and the /tend metabolism.
