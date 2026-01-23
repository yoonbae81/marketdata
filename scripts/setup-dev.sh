#!/bin/bash
# Development Environment Setup Script for macOS/Linux
# Sets up local development environment for MarketData

set -e

echo "🔧 Setting up MarketData development environment..."
echo ""

# Check for Python (Required)
if ! command -v python3 &> /dev/null; then
    echo "❌ ERROR: Python 3 is not installed"
    echo "   Please install Python 3.11 or later"
    exit 1
fi
echo "✅ Python 3 is installed"
echo ""

# Create .venv if it doesn't exist
if [ ! -d .venv ]; then
    echo "🐍 Creating Python virtual environment (.venv)..."
    python3 -m venv .venv
    echo "✅ Virtual environment created"
    echo ""
    
    echo "📦 Installing dependencies..."
    source .venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    echo "✅ Dependencies installed"
    echo ""
else
    echo "✅ Python virtual environment already exists"
    echo ""
fi

# Create necessary directories
echo "📁 Creating data directories..."
mkdir -p data/KR-1m
mkdir -p data/KR-1d
mkdir -p data/US-5m
echo "✅ Directories created"
echo ""

# Run initial tests to verify setup
echo "🧪 Running initial tests to verify setup..."
source .venv/bin/activate
if python -m unittest discover tests -v; then
    echo "✅ Initial tests passed"
else
    echo "⚠️  WARNING: Some tests failed. Please check your environment."
fi
echo ""

echo "============================================================"
echo "✅ MarketData local environment setup complete!"
echo "============================================================"
echo ""
echo "📋 Next steps:"
echo ""
echo "1. Activate virtual environment:"
echo "   source .venv/bin/activate"
echo ""
echo "2. Run the fetch script:"
echo "   bash src/run.sh -d 2026-01-17"
echo ""
echo "3. Extract data:"
echo "   python src/extract.py min 005930 2026-01-17 2026-01-17"
echo ""
echo "📌 Note: For production deployment with automatic scheduling,"
echo "   use scripts/install-systemd.sh"
echo ""
