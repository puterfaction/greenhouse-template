#!/bin/bash
# worktree.sh - Manage git worktrees for multi-agent ("fleet") sessions.
# Each worktree is an isolated working directory on its own branch, so several
# agents can work in parallel without stepping on each other's git status.
# Usage: ./tools/worktree.sh <command> [name]

set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORKTREE_DIR="$REPO_ROOT/.claude/worktrees"

usage() {
    echo "Usage: $0 <command> [name]"
    echo ""
    echo "Commands:"
    echo "  create <name>   Create a new worktree branched from main"
    echo "  list            List all worktrees"
    echo "  remove <name>   Remove a worktree and its branch"
    echo "  sync <name>     Merge latest main into worktree (updates shared files)"
    exit 1
}

cmd_create() {
    local name="$1"
    if [ -z "$name" ]; then
        echo "Error: name required"
        usage
    fi

    local branch="wt/$name"
    local path="$WORKTREE_DIR/$name"

    if [ -d "$path" ]; then
        echo "Worktree '$name' already exists at $path"
        exit 1
    fi

    mkdir -p "$WORKTREE_DIR"

    # Create worktree with a new branch from main
    cd "$REPO_ROOT"
    git worktree add -b "$branch" "$path" main

    echo "Created worktree '$name'"
    echo "  Branch: $branch"
    echo "  Path:   $path"
    echo ""
    echo "cd $path"
}

cmd_list() {
    cd "$REPO_ROOT"
    git worktree list
}

cmd_remove() {
    local name="$1"
    if [ -z "$name" ]; then
        echo "Error: name required"
        usage
    fi

    local branch="wt/$name"
    local path="$WORKTREE_DIR/$name"

    if [ ! -d "$path" ]; then
        echo "Worktree '$name' not found at $path"
        exit 1
    fi

    cd "$REPO_ROOT"
    git worktree remove "$path"
    git branch -d "$branch" 2>/dev/null || git branch -D "$branch" 2>/dev/null || true

    echo "Removed worktree '$name' and branch '$branch'"
}

cmd_sync() {
    local name="$1"
    if [ -z "$name" ]; then
        echo "Error: name required"
        usage
    fi

    local path="$WORKTREE_DIR/$name"

    if [ ! -d "$path" ]; then
        echo "Worktree '$name' not found at $path"
        exit 1
    fi

    cd "$path"
    git merge main --no-edit

    echo "Synced worktree '$name' with main"
}

# Main
case "${1:-}" in
    create) cmd_create "$2" ;;
    list)   cmd_list ;;
    remove) cmd_remove "$2" ;;
    sync)   cmd_sync "$2" ;;
    *)      usage ;;
esac
