#!/bin/bash
# Setup development environment

set -e

echo "======================================================================"
echo "KRX Price Development Environment Setup"
echo "======================================================================"
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo "✓ Dependencies installed"

# Run tests to verify setup
echo ""
echo "Running tests to verify setup..."
python -m unittest tests.test_symbol.TestParseSymbols -v

echo ""
echo "======================================================================"
echo "Development environment setup complete!"
echo "======================================================================"
echo ""
echo "To activate the virtual environment, run:"
echo "  source .venv/bin/activate"
echo ""
echo "To run tests:"
echo "  python -m unittest discover tests -v              # All tests"
echo "  python -m unittest tests.test_symbol tests.test_day tests.test_minute -v  # Unit tests only"
echo "  python -m unittest tests.test_integration -v      # Integration tests only"
