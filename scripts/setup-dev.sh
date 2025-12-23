#!/bin/bash
# Development Environment Setup Script for macOS/Linux
# Sets up local development environment for KRX Price Collector

set -e

echo "🔧 Setting up KRX Price Collector development environment..."
echo ""

# Check for Python (Required)
if ! command -v python3 &> /dev/null; then
    echo "❌ ERROR: Python 3 is not installed"
    echo "   Please install Python 3.11 or later"
    exit 1
fi
echo "✅ Python 3 is installed"

# Check if Docker is installed (Optional)
DOCKER_FOUND=0
if ! command -v docker &> /dev/null; then
    echo "⚠️  WARNING: Docker is not installed"
    echo "   Docker is used for containerized execution."
    echo "   Please install Docker: https://www.docker.com/get-started"
else
    echo "✅ Docker is installed"
    DOCKER_FOUND=1
fi

# Check if Docker Compose is available (Optional)
COMPOSE_FOUND=0
if [ $DOCKER_FOUND -eq 1 ]; then
    if ! docker compose version &> /dev/null; then
        echo "⚠️  WARNING: Docker Compose is not available"
    else
        echo "✅ Docker Compose is available"
        COMPOSE_FOUND=1
    fi
fi
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

# Build Docker images
if [ $COMPOSE_FOUND -eq 1 ]; then
    echo "🐳 Building Docker images..."
    if docker compose build; then
        echo "✅ Docker images built"
    else
        echo "⚠️  WARNING: Docker build failed"
    fi
    echo ""
fi

# Run initial tests to verify setup
echo "🧪 Running initial tests to verify setup..."
source .venv/bin/activate
if python -m unittest tests.test_symbol.TestParseSymbols -v; then
    echo "✅ Initial tests passed"
else
    echo "⚠️  WARNING: Initial tests failed. Please check your environment."
fi
echo ""

echo "=" | tr '=' '=' | head -c 60; echo ""
echo "✅ Development environment setup complete!"
echo "=" | tr '=' '=' | head -c 60; echo ""
echo ""
echo "📋 Next steps:"
echo ""
echo "1. Activate virtual environment (for local development/tests):"
echo "   source .venv/bin/activate"
echo ""
echo "2. Run unit tests:"
echo "   python -m unittest tests.test_symbol tests.test_day tests.test_minute -v"
echo ""
echo "3. Run integration tests (real API calls):"
echo "   python -m unittest tests.test_integration -v"
echo ""
echo "4. Run using Docker Compose (immediate execution):"
echo "   docker compose run --rm app"
echo ""
echo "📌 Note: For production deployment with automatic scheduling,"
echo "   use scripts/setup-systemd.sh on a Linux server"
echo ""
