#!/bin/bash
# worktree-commit.sh - Land worktree changes back to main.
# Usage: ./tools/worktree-commit.sh <name> [commit message]
#
# This script:
# 1. Syncs main into the worktree branch (catches up on shared file changes)
# 2. Commits any uncommitted changes in the worktree
# 3. Merges the worktree branch into main
# 4. Pushes main (if a remote is configured)
# 5. Cleans up the worktree

set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORKTREE_DIR="$REPO_ROOT/.claude/worktrees"

name="$1"
message="${2:-Merge worktree $name}"

if [ -z "$name" ]; then
    echo "Usage: $0 <name> [commit message]"
    exit 1
fi

branch="wt/$name"
path="$WORKTREE_DIR/$name"

if [ ! -d "$path" ]; then
    echo "Error: worktree '$name' not found at $path"
    exit 1
fi

echo "Landing worktree '$name'..."

# Step 1: Sync main into worktree to pick up any shared file changes
echo "  Syncing main into worktree..."
cd "$path"
git merge main --no-edit 2>/dev/null || {
    echo "Error: merge conflict syncing main into worktree."
    echo "Resolve conflicts in $path, then commit and re-run."
    exit 1
}

# Step 2: Commit any uncommitted changes in the worktree
if [ -n "$(git status --porcelain)" ]; then
    echo "  Committing uncommitted changes..."
    git add -A
    git commit -m "$message"
fi

# Step 3: Switch to main and merge the worktree branch
echo "  Merging into main..."
cd "$REPO_ROOT"
git merge "$branch" --no-edit || {
    echo "Error: merge conflict merging $branch into main."
    echo "Resolve conflicts in $REPO_ROOT, then commit."
    exit 1
}

# Step 4: Push (only if an 'origin' remote exists)
if git remote get-url origin >/dev/null 2>&1; then
    echo "  Pushing to remote..."
    git push
fi

# Step 5: Clean up
echo "  Cleaning up worktree..."
git worktree remove "$path"
git branch -d "$branch" 2>/dev/null || true

echo "Done. Worktree '$name' landed on main."
