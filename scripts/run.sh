#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_PYTHON="$PROJECT_DIR/.venv/bin/python"

# Check if venv exists
if [ ! -f "$VENV_PYTHON" ]; then
    echo "[ERROR] Virtual environment not found at $VENV_PYTHON"
    echo "Please run: bash scripts/setup-env.sh"
    exit 1
fi

# Step 1: Run core logic
"$VENV_PYTHON" "$PROJECT_DIR/src/main.py" "$@"
