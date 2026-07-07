#!/usr/bin/env python3
"""Subconscious — an optional associative-memory daemon.

Runs as a background daemon with an embedding model loaded in memory. A
PreToolUse hook (`subconscious_hook.py`) queries it via a Unix socket on every
Read/Grep/Bash/Edit/Write/Glob call, and relevant memory/diary snippets get
surfaced into context — the same way something half-remembered nags at you
mid-task without being asked for.

This is deliberately separate from the tiered memory system (now.md, diary/,
memory/): those are read *deliberately* at session start. This is *ambient* —
it looks for connections you didn't go looking for.

Sources indexed: `diary/*.md`, `memory/*.md`, `now.md`, `who-we-are.md`.

Usage:
    python3 tools/subconscious.py --index      # (re)build the embeddings index
    python3 tools/subconscious.py --start       # start daemon in background
    python3 tools/subconscious.py --stop        # stop daemon
    python3 tools/subconscious.py --status      # check if running
    python3 tools/subconscious.py --reload      # daemon re-reads the index file
    python3 tools/subconscious.py --query       # query from stdin (JSON)
    echo '{"context":"search ranking"}' | python3 tools/subconscious.py --query

Requires `sentence-transformers` and `numpy` (not installed by default — see
docs/subconscious.md). All imports of those are lazy, so `--status`, `--stop`,
etc. work even if they aren't installed.
"""

import hashlib
import json
import os
import re
import signal
import socket
import struct
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
DIARY_DIR = REPO_ROOT / "diary"
MEMORY_DIR = REPO_ROOT / "memory"
WHO_WE_ARE = REPO_ROOT / "who-we-are.md"
NOW_MD = REPO_ROOT / "now.md"
INDEX_FILE = TOOLS_DIR / "subconscious_index.json"

# Per-repo socket/pid/log paths so multiple repos running this daemon don't
# collide in /tmp.
_REPO_HASH = hashlib.md5(str(REPO_ROOT.resolve()).encode()).hexdigest()[:10]
SOCKET_PATH = f"/tmp/subconscious-{_REPO_HASH}.sock"
PID_FILE = f"/tmp/subconscious-{_REPO_HASH}.pid"
LOG_FILE = f"/tmp/subconscious-{_REPO_HASH}.log"

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# Tuned on the original source corpus (a few hundred diary/memory entries).
# If your memory files are large or noisy, raise this — a lower threshold
# surfaces more but noisier connections.
SIMILARITY_THRESHOLD = 0.42
MAX_MEMORIES_PER_QUERY = 2
COOLDOWN_SECONDS = 300  # don't repeat the same memory within this window

# State
_model = None
_all_entries = []  # list of {"source", "title", "date", "text", "hash"}
_embeddings_matrix = None  # numpy array, aligned with _all_entries
_recently_surfaced = {}  # hash -> timestamp of last surfacing


def get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        print("Loading embedding model...", file=sys.stderr, flush=True)
        _model = SentenceTransformer(MODEL_NAME)
        print("Model loaded.", file=sys.stderr, flush=True)
    return _model


def chunk_text(text, max_chars=500, overlap=100):
    """Split text into overlapping chunks for embedding."""
    if len(text) <= max_chars:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = start + max_chars
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk)
        start = end - overlap
    return chunks


# ── Parsing sources into chunk entries ──

def parse_diary_entries():
    """Split each diary/*.md file into ## sections, one entry per section."""
    entries = []
    if not DIARY_DIR.exists():
        return entries

    for md_path in sorted(DIARY_DIR.glob("*.md")):
        if md_path.name.lower() == "readme.md":
            continue
        date = md_path.stem[:10]
        text = md_path.read_text(encoding="utf-8")

        for block in re.split(r"\n---\n", text):
            block = block.strip()
            if not block:
                continue

            title_match = re.match(r"^# (.+)", block)
            entry_title = title_match.group(1).strip() if title_match else md_path.stem

            sections = re.split(r"(^## .+$)", block, flags=re.MULTILINE)
            current_heading = None
            section_chunks = []
            for part in sections:
                h2_match = re.match(r"^## (.+)$", part.strip())
                if h2_match:
                    current_heading = h2_match.group(1).strip()
                elif current_heading:
                    plain = part.strip()
                    if plain and len(plain) > 20:
                        section_chunks.append((current_heading, plain))

            if section_chunks:
                for heading, text_content in section_chunks:
                    entries.append({
                        "source": "diary",
                        "title": f"{entry_title} > {heading}",
                        "date": date,
                        "text": text_content,
                        "hash": hashlib.md5(text_content.encode()).hexdigest(),
                    })
            else:
                entries.append({
                    "source": "diary",
                    "title": entry_title,
                    "date": date,
                    "text": block,
                    "hash": hashlib.md5(block.encode()).hexdigest(),
                })

    return entries


def parse_memory_entries():
    """Chunk each memory/*.md file (skip the index, MEMORY.md, itself)."""
    entries = []
    if not MEMORY_DIR.exists():
        return entries

    for md_path in sorted(MEMORY_DIR.glob("*.md")):
        if md_path.name == "MEMORY.md":
            continue
        text = md_path.read_text(encoding="utf-8")
        for chunk in chunk_text(text, max_chars=600, overlap=100):
            entries.append({
                "source": "memory",
                "title": md_path.stem,
                "date": "",
                "text": chunk,
                "hash": hashlib.md5(chunk.encode()).hexdigest(),
            })

    return entries


def parse_singleton_files():
    """Chunk who-we-are.md and now.md — the always-loaded durable layers."""
    entries = []
    for fpath, label in [(WHO_WE_ARE, "who-we-are"), (NOW_MD, "now")]:
        if not fpath.exists():
            continue
        text = fpath.read_text(encoding="utf-8")
        for chunk in chunk_text(text, max_chars=600, overlap=100):
            entries.append({
                "source": label,
                "title": label,
                "date": "",
                "text": chunk,
                "hash": hashlib.md5(chunk.encode()).hexdigest(),
            })
    return entries


# ── Index build (CLI, needs the model) / load (daemon, no model needed) ──

def build_index():
    """Parse all sources and compute embeddings for new/changed chunks,
    reusing cached embeddings by content hash. Writes INDEX_FILE."""
    entries = parse_diary_entries() + parse_memory_entries() + parse_singleton_files()
    if not entries:
        print("No sources found (diary/, memory/, now.md, who-we-are.md all empty or missing).",
              file=sys.stderr)
        json.dump({"entries": [], "embeddings": []}, open(INDEX_FILE, "w"))
        return

    existing = {"entries": [], "embeddings": []}
    if INDEX_FILE.exists():
        existing = json.loads(INDEX_FILE.read_text())
    existing_map = {
        e.get("hash"): existing["embeddings"][i]
        for i, e in enumerate(existing.get("entries", []))
        if e.get("hash") and i < len(existing.get("embeddings", []))
    }

    new_texts, new_indices, embeddings = [], [], []
    for i, entry in enumerate(entries):
        cached = existing_map.get(entry["hash"])
        if cached:
            embeddings.append(cached)
        else:
            new_texts.append(entry["text"])
            new_indices.append(i)
            embeddings.append(None)

    if new_texts:
        print(f"Computing embeddings for {len(new_texts)} new/changed chunks...", file=sys.stderr)
        model = get_model()
        new_embeddings = model.encode(new_texts, show_progress_bar=False)
        for idx, emb in zip(new_indices, new_embeddings):
            embeddings[idx] = emb.tolist()
    else:
        print("All chunks already indexed.", file=sys.stderr)

    INDEX_FILE.write_text(json.dumps({"entries": entries, "embeddings": embeddings}))
    print(f"Index: {len(entries)} chunks, {len(new_texts)} newly embedded -> {INDEX_FILE}",
          file=sys.stderr)


def load_index_from_disk():
    """Load the precomputed index (fast — no model needed)."""
    global _all_entries, _embeddings_matrix
    import numpy as np

    if not INDEX_FILE.exists():
        print(f"No index at {INDEX_FILE} — run: python3 tools/subconscious.py --index",
              file=sys.stderr, flush=True)
        _all_entries = []
        _embeddings_matrix = np.array([])
        return

    idx = json.loads(INDEX_FILE.read_text())
    entries = idx.get("entries", [])
    embeddings = idx.get("embeddings", [])
    kept_entries, kept_embeddings = [], []
    for e, emb in zip(entries, embeddings):
        if emb:
            kept_entries.append(e)
            kept_embeddings.append(emb)

    _all_entries = kept_entries
    _embeddings_matrix = np.array(kept_embeddings) if kept_embeddings else np.array([])
    print(f"Loaded {len(_all_entries)} indexed chunks.", file=sys.stderr, flush=True)


def extract_query(data):
    """Build a search query from tool context."""
    if "context" in data:
        return data["context"]

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})

    # Generic filesystem noise to drop from paths — never a literal project
    # or username, always derived so this works in any clone of the repo.
    noise_parts = {"Users", "home", REPO_ROOT.name, Path.home().name, ""}

    def meaningful_parts(path_str, n):
        parts = [p for p in Path(path_str).parts if p not in noise_parts]
        return " ".join(parts[-n:]) if parts else ""

    if tool_name == "Read":
        return meaningful_parts(tool_input.get("file_path", ""), 3)

    elif tool_name == "Grep":
        pattern = tool_input.get("pattern", "")
        path = meaningful_parts(tool_input.get("path", ""), 2)
        return f"{pattern} {path}"

    elif tool_name == "Bash":
        cmd = tool_input.get("command", "")
        noise = ["ls", "pwd", "cd", "echo", "git status", "git log", "git diff", "git add", "git commit", "git push"]
        if any(cmd.strip().startswith(n) for n in noise):
            return ""
        return cmd[:200]

    elif tool_name in ("Edit", "Write"):
        path = meaningful_parts(tool_input.get("file_path", ""), 3)
        content = tool_input.get("new_string", "") or tool_input.get("content", "")
        return f"{path} {content[:100]}"

    elif tool_name == "Glob":
        return tool_input.get("pattern", "")

    return ""


def query_memories(query_text):
    """Find relevant memories for a query. Returns list of formatted memory dicts."""
    import numpy as np

    if not query_text or not query_text.strip() or len(_all_entries) == 0:
        return []

    model = get_model()
    query_emb = model.encode([query_text])[0]

    norms = np.linalg.norm(_embeddings_matrix, axis=1)
    query_norm = np.linalg.norm(query_emb)
    scores = np.dot(_embeddings_matrix, query_emb) / (norms * query_norm + 1e-10)

    top_indices = np.argsort(scores)[::-1][:20]

    now = time.time()
    results = []
    seen_titles = set()

    for idx in top_indices:
        if len(results) >= MAX_MEMORIES_PER_QUERY:
            break

        score = float(scores[idx])
        if score < SIMILARITY_THRESHOLD:
            break

        entry = _all_entries[idx]
        h = entry["hash"]

        if h in _recently_surfaced and now - _recently_surfaced[h] < COOLDOWN_SECONDS:
            continue

        title = entry["title"]
        if title in seen_titles:
            continue
        seen_titles.add(title)

        source = entry["source"]
        date = entry.get("date", "")
        text = entry["text"]

        if source == "diary":
            label = f"Diary: {title}"
        elif source == "memory":
            label = f"Memory: {title}"
        elif source == "who-we-are":
            label = "who-we-are.md"
        elif source == "now":
            label = "now.md"
        else:
            label = title
        if date:
            label = f"[{date}] {label}"

        preview = text[:250].strip()
        if len(text) > 250:
            preview += "..."

        results.append({"label": label, "preview": preview, "score": round(score, 3), "hash": h})
        _recently_surfaced[h] = now

    return results


def format_output(memories):
    """Format memories as a natural 'whisper' for injection into context."""
    if not memories:
        return ""
    lines = ["<subconscious>"]
    for m in memories:
        lines.append(f"[{m['label']}] (relevance: {m['score']})")
        lines.append(m["preview"])
        lines.append("")
    lines.append("</subconscious>")
    return "\n".join(lines)


# ── Socket server ──

def send_msg(conn, data):
    payload = json.dumps(data).encode()
    conn.sendall(struct.pack("!I", len(payload)) + payload)


def recv_msg(conn):
    raw_len = conn.recv(4)
    if not raw_len:
        return None
    msg_len = struct.unpack("!I", raw_len)[0]
    data = b""
    while len(data) < msg_len:
        chunk = conn.recv(min(msg_len - len(data), 4096))
        if not chunk:
            return None
        data += chunk
    return json.loads(data)


def handle_client(conn):
    try:
        msg = recv_msg(conn)
        if not msg:
            return

        cmd = msg.get("cmd", "query")

        if cmd == "query":
            query_text = extract_query(msg)
            memories = query_memories(query_text)
            send_msg(conn, {"memories": memories, "query": query_text})

        elif cmd == "status":
            send_msg(conn, {
                "status": "running",
                "entries": len(_all_entries),
                "recently_surfaced": len(_recently_surfaced),
            })

        elif cmd == "reload":
            load_index_from_disk()
            send_msg(conn, {"status": "reloaded", "entries": len(_all_entries)})

    except Exception as e:
        try:
            send_msg(conn, {"error": str(e)})
        except Exception:
            pass
    finally:
        conn.close()


def run_daemon():
    """Main daemon loop."""
    if os.path.exists(SOCKET_PATH):
        os.unlink(SOCKET_PATH)

    load_index_from_disk()
    get_model()  # warm up now, so the first query isn't the one paying for it

    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(SOCKET_PATH)
    server.listen(5)
    server.settimeout(1.0)

    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))

    print(f"Subconscious daemon running (pid {os.getpid()}, socket {SOCKET_PATH})", file=sys.stderr, flush=True)
    print(f"Loaded {len(_all_entries)} indexed chunks.", file=sys.stderr, flush=True)

    running = True

    def handle_signal(signum, frame):
        nonlocal running
        running = False

    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    try:
        while running:
            try:
                conn, _ = server.accept()
                handle_client(conn)
            except socket.timeout:
                continue
            except Exception as e:
                print(f"Error: {e}", file=sys.stderr, flush=True)
    finally:
        server.close()
        if os.path.exists(SOCKET_PATH):
            os.unlink(SOCKET_PATH)
        if os.path.exists(PID_FILE):
            os.unlink(PID_FILE)
        print("Daemon stopped.", file=sys.stderr, flush=True)


# ── Client functions ──

def client_send(msg):
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.settimeout(2.0)
    try:
        sock.connect(SOCKET_PATH)
        send_msg(sock, msg)
        return recv_msg(sock)
    finally:
        sock.close()


def is_running():
    if not os.path.exists(PID_FILE):
        return False
    try:
        pid = int(Path(PID_FILE).read_text().strip())
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, ValueError, PermissionError):
        return False


def start_daemon():
    if is_running():
        print("Daemon already running.")
        return

    if "--foreground" in sys.argv:
        run_daemon()
    else:
        import subprocess
        script = os.path.abspath(__file__)
        with open(LOG_FILE, "a") as log:
            subprocess.Popen(
                [sys.executable, script, "--start", "--foreground"],
                stdout=log, stderr=log,
                stdin=subprocess.DEVNULL,
                start_new_session=True,
            )
        print("Subconscious daemon starting in background (model loading takes ~10s).")
        print("Check status: python3 tools/subconscious.py --status")


def stop_daemon():
    if not os.path.exists(PID_FILE):
        print("No daemon running.")
        return

    try:
        pid = int(Path(PID_FILE).read_text().strip())
        os.kill(pid, signal.SIGTERM)
        print(f"Sent SIGTERM to daemon (pid {pid}).")
        for _ in range(10):
            time.sleep(0.2)
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                print("Daemon stopped.")
                return
        print("Daemon may still be shutting down.")
    except (ProcessLookupError, ValueError):
        print("Daemon not running (stale PID file).")
        if os.path.exists(PID_FILE):
            os.unlink(PID_FILE)


def main():
    args = sys.argv[1:]

    if not args:
        print(__doc__)
        return

    if "--index" in args:
        build_index()
    elif "--start" in args:
        start_daemon()
    elif "--stop" in args:
        stop_daemon()
    elif "--status" in args:
        if is_running():
            try:
                resp = client_send({"cmd": "status"})
                print(f"Running: {resp.get('entries', '?')} entries loaded, "
                      f"{resp.get('recently_surfaced', 0)} recently surfaced")
            except Exception:
                print("Running (socket not responding yet — model may still be loading)")
        else:
            print("Not running.")
    elif "--reload" in args:
        if not is_running():
            print("Daemon not running.")
            return
        resp = client_send({"cmd": "reload"})
        print(f"Reloaded: {resp.get('entries', '?')} entries")
    elif "--query" in args:
        if not is_running():
            print("Daemon not running. Start with --start first.", file=sys.stderr)
            sys.exit(1)
        if not sys.stdin.isatty():
            data = json.load(sys.stdin)
        else:
            remaining = [a for a in args if a != "--query"]
            data = {"context": " ".join(remaining)}

        resp = client_send({"cmd": "query", **data})
        memories = resp.get("memories", [])
        if memories:
            print(format_output(memories))
        else:
            print(f"(no relevant memories for: {resp.get('query', '?')})", file=sys.stderr)
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
