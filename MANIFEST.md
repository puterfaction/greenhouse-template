# Manifest

This kit is the **sanitized, reusable design** of a personal agent-memory workspace. It
contains templates, scripts, and documentation — **no personal content**. Everything was
rewritten or genericized from the private source; nothing was copied verbatim that carried
identity, relationships, or data.

Built in a fresh git repository with **no shared history** with the source (a `git init`
from scratch — the source's history contains all the private content, so it was never
touched). **No remote is configured and nothing has been pushed.** Publishing is a manual
step left to the owner.

## Files included

### Top level
| File | Why |
| --- | --- |
| `README.md` | The portfolio piece: what the system is, the philosophy, the layers, how to adopt it. |
| `LICENSE` | MIT. |
| `MANIFEST.md` | This file. |
| `leak-scan-report.md` | The results of the private-content scan. |
| `CLAUDE.md` | Project-instructions **template** — structure and conventions with placeholders, personal content removed. |
| `now.md` | "What's alive" **template**: explanatory header, section skeleton, plus a *fictional* recipe-app worked example. |
| `who-we-are.md` | Durable-foundation **skeleton**: section prompts describing what belongs, no real person. |
| `.gitignore` | Ignores OS/Python cruft, worktree contents, local settings, runtime logs. |

### memory/
| File | Why |
| --- | --- |
| `memory/MEMORY.md` | Index-of-durable-memory **template** (one line per file), with standing section stubs. |
| `memory/example-project.md` | Example `project`-type memory (fictional "Pantry" app). |
| `memory/ship-threshold-example.md` | Example `feedback`-type memory showing the Why/How-to-apply shape. |

### diary/
| File | Why |
| --- | --- |
| `diary/README.md` | The diary layer's conventions: entry format, agent's-perspective rule, when to write. |
| `diary/2026-01-02-example.md` | *Fictional* example entry (continues the "Pantry" storyline from now.md). |

### comms/
| File | Why |
| --- | --- |
| `comms/board.json` | **Empty** threaded board — one generic seed post, no real content. |

### dew/
| File | Why |
| --- | --- |
| `dew/routine-prompt.md` | The daily morning-brief instructions ("dew"), genericized from the private source: reads who-we-are.md for name/pronouns/voice, timezone and ntfy topic from config — no personal content. |
| `dew/config.example.json` | Empty-topic config template; users copy to `dew/config.json`. |
| `dew/2026-01-03-example.md` | *Fictional* example brief (continues the "Pantry" storyline). |
| `dew/index.json` | Manifest seeded with the fictional example's entry only. |

### .claude/
| File | Why |
| --- | --- |
| `.claude/settings.json` | The three hooks (SessionStart / Stop / PreCompact), wired with `$CLAUDE_PROJECT_DIR`; no hardcoded paths, no project-specific logic. |
| `.claude/skills/tend/SKILL.md` | The `/tend` metabolism skill, genericized (no names, no Greenhouse-specific project references). |

### tools/
| File | Why |
| --- | --- |
| `tools/tend_check.py` | Memory-layer health check. ROOT derived from file location; handover path derived or env-overridable. |
| `tools/tend_hygiene.py` | Runs the check, writes a dated report. ROOT derived from file location. |
| `tools/install_tend_hygiene.sh` | Installs the weekly launchd agent; computes repo path, fills the plist template. |
| `tools/tend-hygiene.plist.template` | launchd timer with `__REPO__`/`__PYTHON__` placeholders (no hardcoded user paths). |
| `tools/auto_handover.py` | PreCompact handover generator. Paths from `CLAUDE_PROJECT_DIR` or file location; prompt genericized (HUMAN/CLAUDE, no names). |
| `tools/worktree.sh` | Create/list/sync/remove worktrees. Dead `status.sh` reference removed. |
| `tools/worktree-commit.sh` | Land a worktree to main; push made conditional on a remote existing. |
| `tools/comms_post.py` | Post to the board. Author enum changed from a personal name to `human`; hardcoded git identity removed; push conditional on remote. |
| `tools/comms_check.py` | Print recent board posts for SessionStart. Genericized. |
| `tools/subconscious.py` | Optional associative-memory daemon (v2 add-on, 2026-07-07). Socket/PID/log paths hashed from repo root instead of a literal project name; sources are `diary/*.md` + `memory/*.md` + `now.md` + `who-we-are.md` (the private chat-corpus source was removed entirely); adds an `--index` command (adapted from `diary_search.py`'s `build_index()`) so the daemon loads a precomputed index instead of embedding on every start. |
| `tools/subconscious_hook.py` | Its PreToolUse hook client. Same repo-hashed socket path; the private per-user surfacing log was dropped (it wrote to a hardcoded personal transcript path with no equivalent in this kit). |

### docs/
| File | Why |
| --- | --- |
| `docs/architecture.md` | The layered-memory rationale, in depth. |
| `docs/hooks.md` | What each hook does; how to adapt; scheduling the hygiene pass. |
| `docs/worktrees.md` | The multi-agent "fleet" workflow. |
| `docs/comms-board.md` | The agent-to-agent board pattern. |
| `docs/dew.md` | The morning brief: setup (ntfy + three runner options), voice customization, production design notes. No personal content; the private topic name is not reproduced. |
| `docs/subconscious.md` | The optional daemon: what it is, install, `--index`/`--start`/`--reload` commands, the PreToolUse hook block, threshold-tuning guidance. |

### tend-reports/
| File | Why |
| --- | --- |
| `tend-reports/.gitkeep` | Keeps the (otherwise empty) reports directory. Generated reports are runtime artifacts, not shipped. |

## Excluded (verified absent)

Scanned the whole output tree case-insensitively; every category below returned **no
hits** (see `leak-scan-report.md`):

- [x] **Diary** — no real diary entries or content. A `diary/` skeleton (conventions README
  + one *fictional* example entry) was added by owner decision 2026-07-07; nothing in it
  derives from the private diary.
- [x] **who-we-are.md real content** — shipped as a skeleton; the owner's name, pronouns-as-bio,
  relationships, career, and mental-health content are all absent.
- [x] **Names & handles** — the owner's current and former first names, partner/close-friend
  names, and social-media handles were all scanned for and returned no hits. (Literal names
  are deliberately not reproduced here so this manifest is itself clean to publish.)
- [x] **Chat corpus** — no semantic-search scripts, conversation embeddings, exported
  chat/message corpora, or voice-profile data.
- [x] **Always-on voice-capture pendant / mic** — no pendant data, transcripts, or the
  associated transcript-memory project. (The only matches for that three-letter substring in
  the tree are inside the word "been".)
- [x] **Comms content** — board shipped empty (one generic seed post).
- [x] **Credentials/tokens** — no Twitter/token refresh scripts, exported tweet data,
  cookies, `.env`, credential-writing server code, API keys, or any email address.
- [x] **Personal project data** — none of the owner's personal application projects or their
  data (web apps, scrapers, an essay draft, game prototypes, and similar).
- [x] **Real MEMORY.md / handover.md** — shipped as templates/examples only.
- [x] **Personal absolute paths** — no personal home-directory path or the private repo's
  directory name in any shipped file; paths are derived at runtime from the file's own
  location or `$CLAUDE_PROJECT_DIR`.
- [x] **Subconscious daemon** — ~~the private PreToolUse `subconscious` hook and its scripts
  were deliberately left out (project-specific, out of scope)~~ — RESOLVED 2026-07-07
  (owner's call): a **generalized v2** now ships (`tools/subconscious.py`,
  `tools/subconscious_hook.py`, `docs/subconscious.md`) as an opt-in add-on. Scanned for
  owner names, personal paths, chat-corpus references, and personal project names — none
  found (see grep output in the port report).

## Judgment calls (flagged for the owner)

1. **Diary shipped as a skeleton.** ~~Originally concept-only~~ — RESOLVED 2026-07-07
   (owner's call): the diary is essential to the memory system, so a `diary/` starter now
   ships — a conventions README plus one fictional example entry, matching the now.md
   worked example. No real diary content included.
2. **Subconscious daemon: excluded from v1, ~~planned as a v2 optional add-on~~ shipped as
   v2 2026-07-07.** The PreToolUse "subconscious" associative-memory hook was originally
   dropped rather than genericized because it's the most experimental subsystem and needed
   real generalization work (it embedded the owner's memory files directly). Decision
   2026-07-07 (owner's call): a generalized version now ships as an opt-in add-on —
   embedding sources are `diary/*.md` + `memory/*.md` + `now.md` + `who-we-are.md` (the
   private chat-corpus source was removed, not genericized), socket/PID/log paths are
   hashed from the repo root instead of a literal name, and a new `--index` command
   replaces the private version's per-startup re-embedding. See
   [`docs/subconscious.md`](docs/subconscious.md); README's "The subconscious (optional
   add-on)" section links it.
3. **Comms board included.** It generalizes cleanly, so it's in, shipped empty. If you'd
   rather keep the first release focused purely on the memory tiers, it's safe to delete
   `comms/`, `docs/comms-board.md`, the two comms scripts, and the comms line in the
   SessionStart hook.
4. **Author enum `human`.** `comms_post.py` originally had an author value that was the
   owner's name; genericized to `human`. Change the enum if you prefer different channel labels.
5. **Git identity in commits.** Removed the hardcoded personal git identity from the
   scripts; commits now use whatever the repo/user has configured. Decision 2026-07-07:
   the repo's own commits are attributed to the owner's public GitHub identity
   (`puterfaction`) — this is a portfolio artifact, attribution is the point.
