#!/usr/bin/env python3
"""Show recent comms board posts. Called by the SessionStart hook so each new
session sees what the other agents left pending."""
import json
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

board_path = Path(__file__).parent.parent / "comms" / "board.json"
if not board_path.exists():
    sys.exit(0)

board = json.loads(board_path.read_text())
posts = board.get("posts", [])
if not posts:
    sys.exit(0)

# Show posts from last 7 days
cutoff = datetime.now(timezone.utc) - timedelta(days=7)
recent = []
for p in posts:
    try:
        ts = datetime.fromisoformat(p["timestamp"])
        if ts > cutoff:
            recent.append(p)
    except (ValueError, KeyError):
        continue

if not recent:
    sys.exit(0)

# Build a readable summary
print("📬 Recent comms board posts (last 7 days):")
print("---")
for p in recent[-5:]:  # Show last 5 at most
    author = p.get("author", "unknown")
    subject = p.get("subject", "")
    body = p.get("body", "")
    ts = p.get("timestamp", "")[:10]
    parent = p.get("parent_id")

    prefix = "  ↳ " if parent else ""
    header = f"{prefix}[{author}] {ts}"
    if subject:
        header += f" — {subject}"

    # Truncate body to first 100 chars
    body_preview = body.replace("\n", " ")[:100]
    if len(body) > 100:
        body_preview += "..."

    print(f"{header}")
    print(f"  {body_preview}")
    print()

print("Read full board: comms/board.json | Post: python3 tools/comms_post.py")
print("---")
