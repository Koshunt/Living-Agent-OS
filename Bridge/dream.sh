#!/usr/bin/env bash
# Nightly memory consolidation cron entry — see docs/DreamAndSync.md.
#
# Host guard: exactly ONE machine should dream (the "dreamer"); other machines
# only chat and push increments. Configure it once:
#   export LIVINGOS_DREAM_HOST="your-dreamer-hostname"   (or set "dream_host"
#   in Bridge/config.json). The comparison uses the hostname with its domain
#   suffix stripped (myhost.example.local -> myhost.example) and is case-insensitive.
set -u
BRIDGE="$(cd "$(dirname "$0")" && pwd)"
LOG="$BRIDGE/dream.log"

export PATH="/usr/local/bin:/usr/bin:/bin:$HOME/.local/bin"
HOST_SHORT="$(hostname | cut -d. -f1 | tr '[:upper:]' '[:lower:]')"

DREAM_HOST="${LIVINGOS_DREAM_HOST:-}"
if [ -z "$DREAM_HOST" ] && [ -f "$BRIDGE/config.json" ]; then
  DREAM_HOST="$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1])).get("dream_host",""))' "$BRIDGE/config.json" 2>/dev/null || true)"
fi
DREAM_HOST="$(printf '%s' "$DREAM_HOST" | cut -d. -f1 | tr '[:upper:]' '[:lower:]')"

if [ -z "$DREAM_HOST" ]; then
  echo "$(date '+%F %T') LIVINGOS_DREAM_HOST not configured; skipping" >> "$LOG"
  exit 0
fi
if [ "$HOST_SHORT" != "$DREAM_HOST" ]; then
  echo "$(date '+%F %T') not the dreamer host ($HOST_SHORT != $DREAM_HOST); skipping" >> "$LOG"
  exit 0
fi

LOCK="/tmp/livingos-dream.lock"
exec 9>"$LOCK"
flock -n 9 || { echo "$(date '+%F %T') previous dream still running; skipping" >> "$LOG"; exit 0; }

echo "=== $(date '+%F %T') falling asleep" >> "$LOG"
timeout 900 python3 "$BRIDGE/dream.py" >> "$LOG" 2>&1
rc=$?
echo "=== $(date '+%F %T') waking up (exit $rc)" >> "$LOG"
exit $rc
