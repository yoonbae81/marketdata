#!/bin/bash
# Install MarketData as a systemd timer service
# This script sets up automatic data collection via systemd

set -e

# Run as root check
if [ "$EUID" -ne 0 ]; then
  echo "❌ Please run as root (use sudo)"
  exit 1
fi

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
# Project root is one level up from scripts/
PROJECT_DIR="$( cd "$SCRIPT_DIR/.." &> /dev/null && pwd )"

CURRENT_USER=$(logname || echo $USER)

echo "============================================================"
echo "Installing MarketData systemd timer service"
echo "============================================================"
echo "Project Dir: $PROJECT_DIR"
echo "User: $CURRENT_USER"
echo ""

# Ensure data directory exists
echo "📁 Ensuring data directory exists..."
mkdir -p "$PROJECT_DIR/data"
chown -R "$CURRENT_USER:$CURRENT_USER" "$PROJECT_DIR/data"

# Setup Python virtual environment if not exists
if [ ! -d "$PROJECT_DIR/.venv" ]; then
    echo "🐍 Setting up Python virtual environment..."
    cd "$PROJECT_DIR"
    sudo -u "$CURRENT_USER" python3 -m venv .venv
    sudo -u "$CURRENT_USER" .venv/bin/pip install --upgrade pip
    sudo -u "$CURRENT_USER" .venv/bin/pip install -r requirements.txt
else
    echo "✅ Virtual environment already exists"
fi

# Template paths
SERVICE_TEMPLATE="$PROJECT_DIR/scripts/systemd/marketdata-fetch.service"
TIMER_TEMPLATE="$PROJECT_DIR/scripts/systemd/marketdata-fetch.timer"

# Target paths
SERVICE_TARGET="/etc/systemd/system/marketdata-fetch.service"
TIMER_TARGET="/etc/systemd/system/marketdata-fetch.timer"

# Create service file from template
echo "⚙️  Installing systemd service..."
sed -e "s|{{PROJECT_ROOT}}|$PROJECT_DIR|g" \
    -e "s|{{USER}}|$CURRENT_USER|g" \
    "$SERVICE_TEMPLATE" > "$SERVICE_TARGET"

# Copy timer file
cp "$TIMER_TEMPLATE" "$TIMER_TARGET"

# Reload systemd
echo "🔄 Reloading systemd daemon..."
systemctl daemon-reload

# Enable and start the timer
echo "▶️  Enabling and starting marketdata-fetch.timer..."
systemctl enable marketdata-fetch.timer
systemctl start marketdata-fetch.timer

echo ""
echo "============================================================"
echo "✅ Systemd timer installation complete!"
echo "============================================================"
echo ""
echo "The application is running from: $PROJECT_DIR"
echo "Data will be saved to: $PROJECT_DIR/data"
echo "Data will be collected automatically according to the timer schedule."
echo ""
echo "Useful commands:"
echo "  systemctl status marketdata-fetch.timer    # Check timer status"
echo "  systemctl status marketdata-fetch.service  # Check last run"
echo "  journalctl -u marketdata-fetch.service     # View logs"
echo ""
systemctl status marketdata-fetch.timer --no-pager
