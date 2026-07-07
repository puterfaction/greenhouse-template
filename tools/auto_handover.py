#!/usr/bin/env python3
"""Auto-handover: generates a session summary before context compaction.

Called by the PreCompact hook. Reads the current session transcript, extracts
the recent conversation, pipes it to `claude -p` for summarization, and saves
the result as handover.md for the next session to read.

Paths are derived from CLAUDE_PROJECT_DIR (set by Claude Code in hooks) when
available, otherwise from this file's location. The transcript/handover
directory is Claude Code's per-project folder under ~/.claude/projects/.
"""

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Repo root: prefer the env var Claude Code sets in hooks, else derive it.
REPO_DIR = Path(os.environ.get("CLAUDE_PROJECT_DIR",
                               Path(__file__).resolve().parent.parent))


def project_slug(root: Path) -> str:
    """Claude Code names each project's transcript dir after its absolute path,
    with '/' and '_' replaced by '-'."""
    return str(root).replace("/", "-").replace("_", "-")


PROJECT_DIR = Path(
    os.environ.get("GREENHOUSE_HANDOVER_DIR")
    or Path.home() / ".claude" / "projects" / project_slug(REPO_DIR)
)
HANDOVER_FILE = PROJECT_DIR / "handover.md"
CLAUDE_BIN = shutil.which("claude") or str(Path.home() / ".local" / "bin" / "claude")

# How much transcript to send (characters of extracted text)
MAX_CONTEXT_CHARS = 40000


def load_durable_context():
    """Read who-we-are.md for relationship/project context, if present."""
    path = REPO_DIR / "who-we-are.md"
    if path.exists():
        return path.read_text()
    return None


def load_recent_diary():
    """Read today's diary markdown, or the most recent entry, if a diary exists."""
    diary_dir = REPO_DIR / "diary"
    index_path = diary_dir / "index.json"
    if not index_path.exists():
        return None

    with open(index_path) as f:
        index = json.load(f)
    if not index:
        return None

    today = datetime.now().strftime("%Y-%m-%d")
    for item in index:
        if item.get("date") == today:
            md_path = diary_dir / f"{today}.md"
            if md_path.exists():
                return f"[Diary entry {today}]\n{md_path.read_text()}"

    last = index[-1]
    md_path = diary_dir / f"{last['date']}.md"
    if md_path.exists():
        return f"[Diary entry {last['date']}]\n{md_path.read_text()}"
    return None


def find_current_transcript():
    """Find the most recently modified session transcript."""
    jsonl_files = sorted(PROJECT_DIR.glob("*.jsonl"),
                         key=lambda f: f.stat().st_mtime, reverse=True)
    return jsonl_files[0] if jsonl_files else None


def extract_conversation(transcript_path):
    """Extract human/assistant message text from a JSONL transcript."""
    messages = []
    with open(transcript_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            msg = entry.get("message", {})
            role = msg.get("role")
            if role not in ("user", "assistant"):
                continue

            content = msg.get("content", "")
            real_text = []
            has_text = False
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict):
                        if block.get("type") == "text":
                            t = block.get("text", "").strip()
                            if t:
                                real_text.append(t)
                                has_text = True
                        # tool_use / tool_result blocks are skipped
                    elif isinstance(block, str) and block.strip():
                        real_text.append(block.strip())
                        has_text = True
            elif isinstance(content, str) and content.strip():
                real_text.append(content.strip())
                has_text = True

            if has_text:
                messages.append({"role": role, "text": "\n".join(real_text)})

    return messages


def trim_to_recent(messages, max_chars):
    """Take the most recent messages that fit within max_chars."""
    result = []
    total = 0
    for msg in reversed(messages):
        msg_len = len(msg["text"]) + 20
        if total + msg_len > max_chars:
            break
        result.insert(0, msg)
        total += msg_len
    return result


def format_for_summary(messages):
    lines = []
    for msg in messages:
        prefix = "HUMAN:" if msg["role"] == "user" else "CLAUDE:"
        text = msg["text"][:3000] + "..." if len(msg["text"]) > 3000 else msg["text"]
        lines.append(f"{prefix} {text}")
    return "\n\n".join(lines)


SUMMARY_PROMPT = """You are reading the tail end of a Claude Code session. Context is about to be compacted and this handover is the lifeline for the next session.

You may have been given:
1. who-we-are.md — the durable "who you're working with / what matters" doc
2. Recent diary entries — what's been happening lately
3. The session transcript — what happened this session

Generate a detailed handover. Do NOT be vague or meta ("we were working on stuff"). Be specific: name files, describe what's half-built, note what the user asked for.

## Required sections:

### Orientation
- Tell the next session: "Read who-we-are.md and now.md first — they have the current context."
- Briefly note where we are in the work (what phase, what just shipped).

### What we built this session
- Specific files created or modified, with paths
- What each change does (one line each)

### What's in progress
- Anything half-built or just discussed but not started
- Be specific: what was the last thing the user asked for?

### What the user wants next
- Pending requests, in their words where possible

### Gotchas
- Anything broken, flaky, or surprising
- Technical context the next session needs (e.g., "server runs on localhost:8000")

### Vibe
- Was the user frustrated? excited? winding down? One sentence.

Write as bullet notes. Aim for 300-600 words — enough to be useful, not a wall.

"""


def generate_handover(transcript_text, durable=None, diary_context=None):
    prompt = SUMMARY_PROMPT
    if durable:
        prompt += "WHO-WE-ARE.MD:\n" + durable[:4000] + "\n\n"
    if diary_context:
        prompt += "RECENT DIARY ENTRIES:\n" + diary_context[:6000] + "\n\n"
    prompt += "TRANSCRIPT:\n" + transcript_text

    try:
        result = subprocess.run(
            [CLAUDE_BIN, "-p", prompt],
            capture_output=True, text=True, timeout=60, cwd=str(REPO_DIR),
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


def save_handover(summary):
    header = f"# Session Handover\n_Auto-generated {datetime.now().strftime('%Y-%m-%d %H:%M')}_\n\n"
    PROJECT_DIR.mkdir(parents=True, exist_ok=True)
    HANDOVER_FILE.write_text(header + summary + "\n")


def main():
    transcript_path = find_current_transcript()
    if not transcript_path:
        print("No transcript found, skipping handover.")
        return

    messages = extract_conversation(transcript_path)
    if len(messages) < 5:
        print("Too few messages for handover, skipping.")
        return

    recent = trim_to_recent(messages, MAX_CONTEXT_CHARS)
    transcript_text = format_for_summary(recent)

    summary = generate_handover(transcript_text, load_durable_context(), load_recent_diary())
    if summary:
        save_handover(summary)
        print(f"Handover saved to {HANDOVER_FILE}")
    else:
        # Fallback: save raw recent context as an emergency handover.
        fallback = "# Emergency Handover (auto-summary failed)\n\nLast few messages from session:\n\n"
        for msg in recent[-10:]:
            prefix = "HUMAN:" if msg["role"] == "user" else "CLAUDE:"
            fallback += f"**{prefix}** {msg['text'][:500]}\n\n"
        PROJECT_DIR.mkdir(parents=True, exist_ok=True)
        HANDOVER_FILE.write_text(fallback)
        print(f"Fallback handover saved to {HANDOVER_FILE}")


if __name__ == "__main__":
    main()
