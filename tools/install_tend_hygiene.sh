#!/usr/bin/env bash
# Install the weekly tend-hygiene launchd agent (macOS).
#
# Generates a launchd plist from tend-hygiene.plist.template with this repo's
# absolute path filled in, installs it into ~/Library/LaunchAgents, and loads it.
# Re-run any time to pick up changes (it unloads first, so it's idempotent).
#
# Linux users: use cron instead. See docs/hooks.md for a crontab line.
set -euo pipefail

# Repo root = parent of the dir holding this script, resolved absolutely.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$SCRIPT_DIR/.." && pwd)"

LABEL="com.greenhouse.tend-hygiene"
TEMPLATE="$SCRIPT_DIR/tend-hygiene.plist.template"
DEST="$HOME/Library/LaunchAgents/$LABEL.plist"

mkdir -p "$HOME/Library/LaunchAgents"

# Fill the __REPO__ and __PYTHON__ placeholders in the template.
PYTHON="$(command -v python3)"
sed -e "s|__REPO__|$REPO|g" -e "s|__PYTHON__|$PYTHON|g" "$TEMPLATE" > "$DEST"

# Unload if already loaded (ignore error on first install), then load fresh.
launchctl unload "$DEST" 2>/dev/null || true
launchctl load "$DEST"

echo "Installed and loaded $LABEL"
echo "Runs: Saturdays 9:00am local -> $REPO/tools/tend_hygiene.py"
echo "Verify:  launchctl list | grep tend-hygiene"
echo "Run now: launchctl start $LABEL"
echo "Remove:  launchctl unload $DEST && rm $DEST"
