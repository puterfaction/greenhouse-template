# Worktrees and "fleet" sessions

A git *worktree* is a second working directory attached to the same repository, checked
out on its own branch. It lets several agents work in parallel without stepping on each
other: each one has its own files and its own clean `git status`, so nobody sees anybody
else's half-finished changes.

This matters when you run more than one Claude Code session at once — a "fleet night,"
where you point several agents at independent pieces of work and let them run
concurrently. Without isolation they'd fight over the same working tree; with worktrees
each has a private sandbox that lands cleanly at the end.

## The two scripts

**`tools/worktree.sh`** — lifecycle management:

```
./tools/worktree.sh create <name>   # new worktree at .claude/worktrees/<name> on branch wt/<name>
./tools/worktree.sh list            # show all worktrees
./tools/worktree.sh sync <name>     # merge latest main in (refresh shared files)
./tools/worktree.sh remove <name>   # tear down the worktree and its branch
```

**`tools/worktree-commit.sh`** — land the work back to main:

```
./tools/worktree-commit.sh <name> "commit message"
```

This syncs main into the worktree (so it catches up on any shared-file changes),
commits whatever's uncommitted, merges the branch into main, pushes if a remote exists,
and cleans up the worktree in one shot.

## The workflow

1. **Create** a worktree per independent task: `./tools/worktree.sh create search-index`.
2. **Work** inside it: `cd .claude/worktrees/search-index` and commit freely on `wt/search-index`.
3. **Sync before touching shared files.** now.md, who-we-are.md, and the diary are shared
   across every session. Before editing them, run `./tools/worktree.sh sync <name>` (or
   `git merge main`) so you're editing the latest version and don't create conflicts.
4. **Land** when done: `./tools/worktree-commit.sh search-index "Add search index"`.

## Coordination

The SessionStart hook lists active worktrees, and `tools/tend_check.py` flags any whose
branch hasn't seen a commit in two weeks — a dormant worktree that's either finished (land
it) or abandoned (remove it). During `/tend`, dormant worktrees get surfaced in now.md
rather than left looking active.

Branch names are always `wt/<name>`; reserve that prefix for worktrees so the dormancy
check and the landing script can find them.

## When *not* to bother

Quick, single-file tasks — a diary update, reading files, a one-line fix — don't need a
worktree. The isolation is worth it when work is substantial enough to leave the tree
dirty for a while, or when more than one session is running at once.
