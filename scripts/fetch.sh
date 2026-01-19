#!/bin/bash
# MarketData Collection Script
# Orchestrates symbol and market data collection

set -e  # Exit on error

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SRC_DIR="$PROJECT_ROOT/src"
VENV_PYTHON="$PROJECT_ROOT/.venv/bin/python"

# Check if venv exists
if [ ! -f "$VENV_PYTHON" ]; then
    echo "[ERROR] Virtual environment not found at $VENV_PYTHON"
    echo "Please run: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt"
    exit 1
fi

# Default values
DATE=$(date +%Y-%m-%d)
CONCURRENCY=20

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--date)
            DATE="$2"
            shift 2
            ;;
        -c|--concurrency)
            CONCURRENCY="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [-d DATE] [-c CONCURRENCY]"
            echo "  -d, --date         Date to fetch (default: today)"
            echo "  -c, --concurrency  Concurrent requests (default: 20)"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "=========================================="
echo "MarketData Collection"
echo "Date: $DATE"
echo "Concurrency: $CONCURRENCY"
echo "=========================================="
echo ""

# Step 1: Fetch KR symbols
echo "[1/3] Fetching KR symbols..."
"$VENV_PYTHON" "$SRC_DIR/symbol_kr.py" || {
    echo "[ERROR] Failed to fetch symbols"
    exit 1
}
echo ""

# Step 2: Fetch KR day data
echo "[2/3] Fetching KR daily data..."
"$VENV_PYTHON" "$SRC_DIR/fetch_kr1d.py" -d "$DATE" -c "$CONCURRENCY" || {
    echo "[ERROR] Failed to fetch KR daily data"
    exit 1
}
echo ""

# Step 3: Fetch KR 1-minute data
echo "[3/3] Fetching KR 1-minute data..."
"$VENV_PYTHON" "$SRC_DIR/fetch_kr1m.py" -d "$DATE" -c "$CONCURRENCY" || {
    echo "[ERROR] Failed to fetch KR 1-minute data"
    exit 1
}
echo ""

echo "=========================================="
echo "✓ Data collection completed successfully"
echo "=========================================="
