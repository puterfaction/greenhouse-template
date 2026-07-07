#!/usr/bin/env python3
"""Memory-system health check.

Mechanical staleness detection for the memory layers. Run standalone or via /tend.
Reports, never fixes — the /tend skill (or a human) decides what to do.

Paths are derived from this file's location, so the repo can live anywhere.
The handover file lives outside the repo, in Claude Code's per-project transcript
directory; override its location with GREENHOUSE_HANDOVER_DIR if your setup differs.
"""
import json
import os
import re
import subprocess
import sys
import time
from datetime import date

# Repo root = the directory containing tools/
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def project_slug(root):
    """Claude Code names each project's transcript dir after its absolute path,
    with '/' and '_' replaced by '-'. Reproduce that to find the handover file."""
    return root.replace("/", "-").replace("_", "-")


HANDOVER_DIR = os.environ.get("GREENHOUSE_HANDOVER_DIR") or os.path.expanduser(
    f"~/.claude/projects/{project_slug(ROOT)}"
)
HANDOVER = os.path.join(HANDOVER_DIR, "handover.md")

OK, WARN = "  ✅", "  ⚠️ "
warnings = 0


def say(ok, msg):
    global warnings
    if not ok:
        warnings += 1
    print((OK if ok else WARN) + " " + msg)


def age_days(path):
    if not os.path.exists(path):
        return None
    return (time.time() - os.path.getmtime(path)) / 86400


def git(*args, cwd=ROOT):
    try:
        return subprocess.run(
            ["git", *args], cwd=cwd, capture_output=True, text=True, timeout=15
        ).stdout.strip()
    except Exception:
        return ""


def main():
    os.chdir(ROOT)
    print("Memory health check — " + date.today().isoformat())

    # -- now.md ------------------------------------------------------------
    now_path = os.path.join(ROOT, "now.md")
    if not os.path.exists(now_path):
        say(False, "now.md missing — no 'what's alive' layer")
    else:
        text = open(now_path).read()
        m = re.search(r"Last tended: (\d{4}-\d{2}-\d{2})", text)
        if m:
            tended = date.fromisoformat(m.group(1))
            days = (date.today() - tended).days
            say(days <= 10, f"now.md last tended {days}d ago ({m.group(1)})")
        else:
            say(False, "now.md has no 'Last tended:' date line")

    # -- handover ----------------------------------------------------------
    h_age = age_days(HANDOVER)
    if h_age is None:
        say(True, "no handover.md (clean — it should only exist right after a compaction/crash)")
    elif h_age > 2:
        say(False, f"handover.md is {h_age:.0f}d old — stale, already digested; delete it")
    else:
        say(True, f"handover.md is fresh ({h_age * 24:.0f}h old)")

    # -- durable file (who-we-are-style) -----------------------------------
    for f, limit in (("CLAUDE.md", 250), ("who-we-are.md", 250)):
        p = os.path.join(ROOT, f)
        if os.path.exists(p):
            n = len(open(p).readlines())
            say(n <= limit, f"{f}: {n} lines (soft limit {limit})" +
                ("" if n <= limit else " — prune, don't just append"))

    # -- memory index ------------------------------------------------------
    mem_path = os.path.join(ROOT, "memory", "MEMORY.md")
    if os.path.exists(mem_path):
        n = len(open(mem_path).readlines())
        say(n <= 300, f"MEMORY.md: {n} lines (soft limit 300)")

    # -- worktree dormancy ---------------------------------------------------
    refs = git("for-each-ref", "refs/heads/wt/", "--format=%(refname:short) %(committerdate:unix)")
    for line in refs.splitlines():
        if not line.strip():
            continue
        branch, ts = line.rsplit(" ", 1)
        idle = (time.time() - int(ts)) / 86400
        say(idle <= 14, f"worktree {branch}: last commit {idle:.0f}d ago" +
            ("" if idle <= 14 else " — dormant; land it, or confirm it's parked"))

    # -- uncommitted drift in main tree -------------------------------------
    porcelain = git("status", "--porcelain")
    memory_re = re.compile(r"(memory/|diary/)|who-we-are\.md|now\.md")
    drift = [l for l in porcelain.splitlines() if l.strip() and not memory_re.search(l)]
    if drift:
        say(False, f"{len(drift)} non-memory files uncommitted in main tree "
            "(work leaking outside worktrees/commits):")
        for l in drift[:12]:
            print("       " + l)
        if len(drift) > 12:
            print(f"       ... and {len(drift) - 12} more")
    else:
        say(True, "main tree clean of non-memory drift")

    print()
    if warnings:
        print(f"{warnings} warning(s). /tend should fix or flag each one.")
    else:
        print("All healthy.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
