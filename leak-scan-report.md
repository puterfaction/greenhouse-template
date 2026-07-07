# Leak scan report

**Date:** 2026-07-07
**Scope:** the entire starter-kit working tree, excluding `.git/`.
**Result:** clean. No private content found in any shipped file.

## Method

Every file was grepped case-insensitively for the sensitive-token categories below. The
scan was run against the whole tree, and re-run after writing the `MANIFEST.md` and this
report so the review artifacts were checked too — literal private identifiers are kept out
of both documents on purpose, so the review paperwork is itself safe to publish.

## Token categories scanned — all clean

| Category | Result |
| --- | --- |
| Owner's current + former first names | no hits |
| Partner / close-friend names | no hits |
| Social-media handles | no hits |
| Username / home-directory login | no hits |
| Employer names | no hits |
| Absolute personal paths (home directory, private repo directory name) | no hits |
| Email addresses (regex `\S+@\S+\.\S+`) | no hits |
| Credential/token script names | no hits |
| Always-on voice-capture pendant / mic references | no hits |
| Personal application-project names | no hits |
| Bio terms (medical, networking, identity) | no hits |

## Notes on near-misses

- **The three-letter substring of the pendant's name** matched only occurrences *inside the
  word "been"* (e.g. "has been given", "been in daily use"). No reference to the device or
  its data exists in the tree. Verified by re-running the scan and filtering out "been",
  which left zero hits.
- **A home-directory path** appears only transiently at *runtime* (e.g. `tend_hygiene.py`
  prints the absolute path of the report it just wrote). No shipped file contains a
  hardcoded personal path; scripts derive their root from the file's own location or
  `$CLAUDE_PROJECT_DIR`, and the launchd plist is a template with `__REPO__` placeholders
  filled in at install time.
- **`greenhouse`** appears intentionally: the kit is published as the "Greenhouse Starter
  Kit," and the launchd label is `com.greenhouse.tend-hygiene`. This is the project's own
  public name, not private content.

## Fixes applied during sanitization

- Replaced all hardcoded personal absolute paths with file-relative or
  `$CLAUDE_PROJECT_DIR`-relative resolution.
- Genericized the handover-generator prompt and transcript labels (personal name → `HUMAN`).
- Changed the comms-board author enum from a personal name to `human`.
- Removed the hardcoded personal git identity from the post script and the Stop hook.
- Dropped the project-specific PreToolUse associative-memory hook entirely.
- Replaced the real durable/now/index files and per-topic memories with templates and
  fictional examples.
- Kept literal private identifiers out of `MANIFEST.md` and this report so the review
  artifacts are themselves safe to publish.

## Addendum — dew addition (2026-07-07)

New files (`dew/routine-prompt.md`, `dew/config.example.json`, `dew/2026-01-03-example.md`,
`dew/index.json`, `docs/dew.md`) plus README/MANIFEST updates scanned before push:
owner names/handles (current and former), the private ntfy topic name, routine/trigger IDs,
personal paths, project domains, relationship names, and email — **no hits**. The example
brief is fictional (Pantry storyline); the config ships with an empty topic.

## Addendum — subconscious addition (2026-07-07)

New files (`tools/subconscious.py`, `tools/subconscious_hook.py`, `docs/subconscious.md`)
plus README/MANIFEST/.gitignore updates scanned before push, independently by the
reviewing session (not the porting agent): owner names/handles, personal paths, the
private repo directory name, chat-corpus references, personal project names, topic
names/IDs — **no hits**. Socket/PID/log paths are hashed from the repo root at runtime
(no literal project name). Live-verified end-to-end against the kit's own fictional
Pantry corpus before publishing: on-topic queries surface the fictional entries,
off-topic queries surface nothing, and the runtime index artifact is gitignored.
