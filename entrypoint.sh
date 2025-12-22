#!/bin/bash
set -e

echo "Running src/run.py..."
exec python3 ./src/run.py "$@"
