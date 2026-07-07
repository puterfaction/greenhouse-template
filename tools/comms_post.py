#!/usr/bin/env python3
"""Post to the comms board directly (no server needed).

The comms board is a threaded message board where different agents (and the
human) leave each other async notes — open questions, handoff notes, ideas.
It is deliberately separate from the diary: the diary records what happened,
the board records what's *pending*.

Usage:
  python3 tools/comms_post.py --author cli-claude --subject "Title" --body "Message"
  python3 tools/comms_post.py --author cli-claude --parent 20260213-001 --body "Reply"

Git identity for the auto-commit is taken from GIT_AUTHOR_NAME / GIT_AUTHOR_EMAIL
if set, otherwise falls back to the repo's configured identity.
"""
import json
import os
import argparse
import subprocess
from pathlib import Path
from datetime import datetime, timezone

BOARD_PATH = Path(__file__).parent.parent / "comms" / "board.json"


def main():
    parser = argparse.ArgumentParser(description="Post to the comms board")
    parser.add_argument("--author", required=True,
                        choices=["cli-claude", "web-claude", "human"])
    parser.add_argument("--subject", default=None, help="Thread subject (required for new threads)")
    parser.add_argument("--body", required=True, help="Post body")
    parser.add_argument("--parent", default=None, help="Parent post ID (for replies)")
    args = parser.parse_args()

    if not args.parent and not args.subject:
        parser.error("--subject is required for new threads")

    board = json.loads(BOARD_PATH.read_text()) if BOARD_PATH.exists() else {"version": 1, "posts": []}

    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    existing_today = [p for p in board["posts"] if p["id"].startswith(today)]
    seq = len(existing_today) + 1
    post_id = f"{today}-{seq:03d}"

    post = {
        "id": post_id,
        "author": args.author,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "parent_id": args.parent,
        "subject": args.subject,
        "body": args.body,
        "edited": None,
    }

    board["posts"].append(post)
    BOARD_PATH.write_text(json.dumps(board, indent=2) + "\n")

    # Auto-commit (and push if a remote is configured).
    repo_dir = BOARD_PATH.parent.parent
    git_env = os.environ.copy()
    subprocess.run(["git", "add", "comms/board.json"], cwd=repo_dir, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", f"Comms: {args.author} posted '{args.subject or 'reply'}'"],
        cwd=repo_dir, capture_output=True, env=git_env,
    )
    has_remote = subprocess.run(
        ["git", "remote", "get-url", "origin"], cwd=repo_dir, capture_output=True
    ).returncode == 0
    if has_remote:
        subprocess.run(["git", "push"], cwd=repo_dir, capture_output=True)

    print(f"Posted {post_id} by {args.author}")
    if args.subject:
        print(f"Thread: {args.subject}")
    print("Committed" + (" and pushed." if has_remote else "."))


if __name__ == "__main__":
    main()
