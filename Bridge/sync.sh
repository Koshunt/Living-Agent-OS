#!/usr/bin/env bash
# Incremental memory sync — the "everyone else pushes increments" half of the
# multi-machine topology (docs/DreamAndSync.md). Cron-friendly, e.g. hourly:
#   0 * * * * /path/to/Living-Agent-OS/Bridge/sync.sh
#
# Hardened pattern from the production deployment:
#   1. abort any stale rebase left by a crashed pull (it blocks everything)
#   2. add + commit whatever changed, tagged by hostname
#   3. pull --rebase, push — quiet failures; next run retries
# Only Brain content and similar increments should ever flow through here;
# code changes deserve a reviewed commit instead.
set -u
cd "$(dirname "$0")/.." || exit 1

if [ "${1:-}" = "--dry-run" ]; then
  echo "dry-run: would rebase --abort (if stale), add -A, commit 'sync(host): auto', pull --rebase, push"
  git status --short | head -10
  exit 0
fi

HOST_TAG="$(hostname | cut -d. -f1 | tr '[:upper:]' '[:lower:]')"

git rebase --abort >/dev/null 2>&1
git add -A
git commit -qm "sync(${HOST_TAG}): auto" >/dev/null 2>&1
git pull --rebase -q && git push -q
