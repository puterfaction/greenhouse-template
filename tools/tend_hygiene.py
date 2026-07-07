#!/usr/bin/env python3
"""Automated tend hygiene — the machine half of /tend.

Runs the mechanical hygiene movement non-interactively and writes a dated,
human-readable report to tend-reports/YYYY-MM-DD.md. Report-only: it never
deletes handovers, prunes files, or lands worktrees — anything destructive is
flagged for a human (reflection/decision) or a Claude (consolidation).

Scheduled weekly via a launchd agent (see tools/install_tend_hygiene.sh) or a
cron job, or run by hand. The /tend skill consumes a fresh report instead of
re-running the checks.
"""
import os
import subprocess
import sys
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORTS_DIR = os.path.join(ROOT, "tend-reports")


def main():
    os.makedirs(REPORTS_DIR, exist_ok=True)

    # Reuse the single source of truth for checks. tend_check reports, never fixes.
    proc = subprocess.run(
        [sys.executable, os.path.join(ROOT, "tools", "tend_check.py")],
        cwd=ROOT, capture_output=True, text=True, timeout=60,
    )
    output = proc.stdout.rstrip("\n")

    lines = output.splitlines()
    warn_lines = [l.strip() for l in lines if l.lstrip().startswith("⚠️")]
    n = len(warn_lines)

    if n == 0:
        verdict = "healthy — nothing needs attention"
    else:
        verdict = f"{n} item{'s' if n != 1 else ''} need attention"

    today = date.today().isoformat()
    report = [f"# Tend hygiene — {today}", "", f"**Verdict: {verdict}**", ""]

    if warn_lines:
        report.append("## Needs attention")
        report.append("")
        for l in warn_lines:
            report.append(f"- {l.lstrip('⚠️ ').strip()}")
        report.append("")
        report.append(
            "_Report-only: nothing above was auto-fixed. Deleting handovers, "
            "pruning oversized files, and landing/parking worktrees are human "
            "or Claude decisions — handle them in the weekly `/tend` session._"
        )
        report.append("")

    report.append("## Full check output")
    report.append("")
    report.append("```")
    report.append(output)
    report.append("```")
    report.append("")

    report_path = os.path.join(REPORTS_DIR, f"{today}.md")
    with open(report_path, "w") as f:
        f.write("\n".join(report))

    print(f"Verdict: {verdict}")
    print(f"Report: {report_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
