#!/usr/bin/env bash
set -euo pipefail

BRIDGE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Prefer .venv if it exists
for py in "$BRIDGE_DIR/.venv/bin/python3" "$BRIDGE_DIR/.venv/bin/python"; do
    if [ -f "$py" ]; then
        exec "$py" "$BRIDGE_DIR/server.py"
    fi
done

# Fall back to config.json
CONFIG="$BRIDGE_DIR/config.json"
if [ ! -f "$CONFIG" ]; then
    echo "config.json not found. Run setup.ps1 first." >&2
    exit 1
fi

AGENT_PYTHON=$(grep -o '"python_env"[[:space:]]*:[[:space:]]*"[^"]*"' "$CONFIG" | cut -d'"' -f4)
if [ -z "$AGENT_PYTHON" ] || [ ! -f "$AGENT_PYTHON" ]; then
    echo "Python not found in config.json. Run setup.ps1 first." >&2
    exit 1
fi

exec "$AGENT_PYTHON" "$BRIDGE_DIR/server.py"
