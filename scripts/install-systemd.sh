#!/bin/bash
# Install MarketData as a systemd user timer service
# This script sets up automatic data collection via systemd --user

set -e

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
# Project root is one level up from scripts/
PROJECT_DIR="$( cd "$SCRIPT_DIR/.." &> /dev/null && pwd )"

# Identify the user
CURRENT_USER=$(whoami)

echo "============================================================"
echo "Installing MarketData systemd USER timer service"
echo "============================================================"
echo "Project Dir: $PROJECT_DIR"
echo "User: $CURRENT_USER"
echo ""

# Ensure data directory exists
echo "📁 Ensuring data directory exists..."
mkdir -p "$PROJECT_DIR/data"

# Setup Python virtual environment if not exists
if [ ! -d "$PROJECT_DIR/.venv" ]; then
    echo "🐍 Setting up Python virtual environment..."
    cd "$PROJECT_DIR"
    python3 -m venv .venv
    .venv/bin/pip install --upgrade pip
    .venv/bin/pip install -r requirements.txt
else
    echo "✅ Virtual environment already exists"
fi

# Enable linger so the user services run without an active session
echo "🏠 Enabling linger for user $CURRENT_USER..."
echo "Note: This may require sudo password"
sudo loginctl enable-linger "$CURRENT_USER"

# Template paths
SERVICE_TEMPLATE="$PROJECT_DIR/scripts/systemd/marketdata-fetch.service"
TIMER_TEMPLATE="$PROJECT_DIR/scripts/systemd/marketdata-fetch.timer"

# Target paths (systemd user directory)
USER_SYSTEMD_DIR="$HOME/.config/systemd/user"
mkdir -p "$USER_SYSTEMD_DIR"

SERVICE_TARGET="$USER_SYSTEMD_DIR/marketdata-fetch.service"
TIMER_TARGET="$USER_SYSTEMD_DIR/marketdata-fetch.timer"

# Create service file from template
echo "⚙️  Installing systemd user service..."
sed -e "s|{{PROJECT_ROOT}}|$PROJECT_DIR|g" \
    "$SERVICE_TEMPLATE" > "$SERVICE_TARGET"

# Copy timer file
cp "$TIMER_TEMPLATE" "$TIMER_TARGET"

# Reload systemd user daemon
echo "🔄 Reloading systemctl --user daemon..."
systemctl --user daemon-reload

# Enable and start the timer
echo "▶️  Enabling and starting marketdata-fetch.timer..."
systemctl --user enable marketdata-fetch.timer
systemctl --user start marketdata-fetch.timer

echo ""
echo "============================================================"
echo "✅ Systemd user timer installation complete!"
echo "============================================================"
echo ""
echo "The application is running from: $PROJECT_DIR"
echo "Data will be saved to: $PROJECT_DIR/data"
echo "Data will be collected automatically according to the timer schedule."
echo ""
echo "Useful commands:"
echo "  systemctl --user status marketdata-fetch.timer    # Check timer status"
echo "  systemctl --user status marketdata-fetch.service  # Check last run"
echo "  journalctl --user -t marketdata-fetch.service     # View logs (use --user-unit for older versions)"
echo ""
systemctl --user status marketdata-fetch.timer --no-pager
