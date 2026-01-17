#!/bin/bash
# MarketData Collection Script
# Orchestrates symbol and market data collection

set -e  # Exit on error

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SRC_DIR="$PROJECT_ROOT/src"

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
python3 "$SRC_DIR/symbol_kr.py" || {
    echo "[ERROR] Failed to fetch symbols"
    exit 1
}
echo ""

# Step 2: Fetch KR day data
echo "[2/3] Fetching KR daily data..."
python3 "$SRC_DIR/fetch_kr1d.py" -d "$DATE" -c "$CONCURRENCY" || {
    echo "[ERROR] Failed to fetch KR daily data"
    exit 1
}
echo ""

# Step 3: Fetch KR 1-minute data
echo "[3/3] Fetching KR 1-minute data..."
python3 "$SRC_DIR/fetch_kr1m.py" -d "$DATE" -c "$CONCURRENCY" || {
    echo "[ERROR] Failed to fetch KR 1-minute data"
    exit 1
}
echo ""

echo "=========================================="
echo "✓ Data collection completed successfully"
echo "=========================================="
