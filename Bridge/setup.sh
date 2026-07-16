#!/usr/bin/env bash
set -euo pipefail

BRIDGE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENT_HOME="$(dirname "$BRIDGE_DIR")"
VENV_DIR="$BRIDGE_DIR/.venv"
VENV_PYTHON="$VENV_DIR/bin/python3"
VENV_PIP="$VENV_DIR/bin/pip3"

echo ""
echo "=== Agent OS Bridge Setup (Linux) ==="
echo ""

echo "[1/5] Detecting paths..."
echo "  Agent OS: $AGENT_HOME"
echo "  Bridge:   $BRIDGE_DIR"
if [ ! -f "$AGENT_HOME/Brain/BootProtocol.md" ]; then
    echo "ERROR: Agent OS not found at $AGENT_HOME" >&2
    exit 1
fi
echo "  Agent OS repository: OK"

# Step 2: Locate or install Python
echo ""
echo "[2/5] Locating Python..."
PY_EXE=""
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
        PY_EXE="$(command -v "$cmd")"
        break
    fi
done
if [ -z "$PY_EXE" ]; then
    echo "  Python not found. Installing via apt..."
    sudo apt update -qq
    sudo apt install -y -qq python3 python3-venv python3-pip
    PY_EXE="$(command -v python3)"
fi
echo "  Found: $($PY_EXE --version)"

# Step 3: Create venv
echo ""
echo "[3/5] Creating local Python environment..."
if [ ! -f "$VENV_PYTHON" ]; then
    echo "  Creating .venv at $VENV_DIR..."
    $PY_EXE -m venv "$VENV_DIR"
    echo "  .venv created."
else
    echo "  .venv already exists."
fi

# Fix pip path if needed
if [ ! -f "$VENV_PIP" ]; then
    VENV_PIP="$VENV_DIR/bin/pip"
fi

# Step 4: Install dependencies
echo ""
echo "[4/5] Installing dependencies..."
"$VENV_PIP" install -r "$BRIDGE_DIR/requirements.txt" --quiet
echo "  Dependencies installed."

# Step 5: Run tests + print next steps
echo ""
echo "[5/5] Running syntax check..."
"$VENV_PYTHON" -m py_compile "$BRIDGE_DIR/server.py"
echo "  Server syntax OK."

# Generate MCP config hint
echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "  1. Configure your AI client MCP to point to:"
echo "     Command: $VENV_PYTHON"
echo "     Args:    $BRIDGE_DIR/server.py"
echo ""
echo "  2. (Optional) Run the setup wizard for your agent profile:"
echo "     Edit my_profile.md manually, or if you have PowerShell:"
echo "     pwsh scripts/setup_wizard.ps1"
echo ""
echo "Quick test:"
echo "  Run: $VENV_PYTHON $BRIDGE_DIR/server.py"
echo "  Then in your AI client: call agent_ping"
echo ""
