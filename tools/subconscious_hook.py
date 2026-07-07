#!/usr/bin/env python3
"""Thin hook client for the Subconscious daemon.

Reads Claude Code hook JSON from stdin, queries the daemon via a per-repo
Unix socket, and prints relevant memories to stdout (injected into the
agent's context by the PreToolUse hook).

Exits silently (exit 0, no output) if:
- The daemon is not running
- No relevant memories found
- Any error occurs

Designed to be fast (<200ms) — no model loading, just socket I/O. The socket
path is derived from the repo root (see subconscious.py), so this only ever
talks to the daemon for *this* repo, even with several running at once.
"""

import hashlib
import json
import os
import socket
import struct
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
_REPO_HASH = hashlib.md5(str(REPO_ROOT.resolve()).encode()).hexdigest()[:10]
SOCKET_PATH = f"/tmp/subconscious-{_REPO_HASH}.sock"


def send_msg(sock, data):
    payload = json.dumps(data).encode()
    sock.sendall(struct.pack("!I", len(payload)) + payload)


def recv_msg(sock):
    raw_len = sock.recv(4)
    if not raw_len:
        return None
    msg_len = struct.unpack("!I", raw_len)[0]
    data = b""
    while len(data) < msg_len:
        chunk = sock.recv(min(msg_len - len(data), 4096))
        if not chunk:
            return None
        data += chunk
    return json.loads(data)


def main():
    # Bail fast if the daemon isn't running
    if not os.path.exists(SOCKET_PATH):
        return

    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return

    # PreToolUse hook format: {"tool_name": "Read", "tool_input": {"file_path": "..."}}
    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {})

    if tool_name not in ("Read", "Grep", "Bash", "Edit", "Write", "Glob"):
        return

    msg = {"cmd": "query", "tool_name": tool_name, "tool_input": tool_input}

    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(1.0)  # hard timeout — must be fast
        sock.connect(SOCKET_PATH)
        send_msg(sock, msg)
        resp = recv_msg(sock)
        sock.close()
    except (socket.error, OSError):
        return

    if not resp or not resp.get("memories"):
        return

    memories = resp["memories"]
    lines = ["<subconscious>"]
    for m in memories:
        lines.append(f"[{m['label']}] (relevance: {m['score']})")
        lines.append(m["preview"])
        lines.append("")
    lines.append("</subconscious>")

    print("\n".join(lines))


if __name__ == "__main__":
    main()
