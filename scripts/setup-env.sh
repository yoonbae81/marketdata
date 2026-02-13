#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_DIR="$PROJECT_DIR/.venv"

echo "MarketData - Environment Setup"
echo "========================================"
echo "Project directory: $PROJECT_DIR"
echo ""

# Check Python
echo "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi
echo "Found: $(python3 --version)"
echo ""

# Create venv
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    echo "Virtual environment created"
else
    echo "Virtual environment already exists"
fi
echo ""

# Upgrade pip
echo "Upgrading pip..."
"$VENV_DIR/bin/pip" install --upgrade pip --quiet
echo "pip upgraded"
echo ""

# Install dependencies
echo "Installing Python dependencies..."
"$VENV_DIR/bin/pip" install -r "$PROJECT_DIR/requirements.txt"
echo "Dependencies installed"
echo ""

# Create necessary directories
echo "Creating data directories..."
mkdir -p "$PROJECT_DIR/data/KR-1m"
mkdir -p "$PROJECT_DIR/data/KR-1d"
mkdir -p "$PROJECT_DIR/data/US-5m"
echo "Data directories created"
echo ""

# Check .env file
if [ ! -f "$PROJECT_DIR/.env" ]; then
    if [ -f "$PROJECT_DIR/.env.example" ]; then
        echo "Creating .env from .env.example..."
        cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
        echo ".env file created"
    else
        echo "Creating empty .env file..."
        touch "$PROJECT_DIR/.env"
        echo ".env file created"
    fi
    echo "Please edit .env and configure your settings"
else
    echo ".env file exists"
fi
echo ""

echo "Environment setup completed!"
