#!/usr/bin/env sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
HOOKS="$ROOT/.git/hooks"
[ -d "$HOOKS" ] || { echo "This folder is not a Git worktree." >&2; exit 1; }

cat > "$HOOKS/pre-push" <<'EOF'
#!/bin/sh
exec ./Bridge/.venv/bin/python3 scripts/check_before_push.py
EOF
chmod +x "$HOOKS/pre-push"
echo "Installed Agent OS pre-push check."
