#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
SYSTEMD_USER_DIR="$HOME/.config/systemd/user"
SERVICE_NAME="marketdata-fetch"

echo "MarketData - Systemd Timer Installation"
echo "=============================================="
echo "Project directory: $PROJECT_DIR"
echo ""

# Ensure .env exists (setup-env.sh should handle this)
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo "Warning: .env file not found. Running setup-env.sh..."
    bash "$SCRIPT_DIR/setup-env.sh"
fi

# Load environment variables from .env
if [ -f "$PROJECT_DIR/.env" ]; then
    # Filter out comments and export
    export $(cat "$PROJECT_DIR/.env" | grep -v '^#' | xargs)
    echo "Environment variables loaded from .env"
fi

# Create systemd directory
echo "Setting up systemd timer..."
mkdir -p "$SYSTEMD_USER_DIR"

# Create service file from template
echo "Creating $SERVICE_NAME.service..."
sed -e "s|{{PROJECT_ROOT}}|$PROJECT_DIR|g" \
    "$SCRIPT_DIR/systemd/$SERVICE_NAME.service" > "$SYSTEMD_USER_DIR/$SERVICE_NAME.service"

# Copy timer file
echo "Copying $SERVICE_NAME.timer..."
cp "$SCRIPT_DIR/systemd/$SERVICE_NAME.timer" "$SYSTEMD_USER_DIR/"

echo "Systemd files installed"
echo ""

# Reload systemd daemon
echo "Reloading systemd daemon..."
systemctl --user daemon-reload

# Enable and start timer
echo "Enabling and starting timer..."
systemctl --user enable "$SERVICE_NAME.timer"
systemctl --user start "$SERVICE_NAME.timer"

echo ""
echo "Timer installation completed!"
echo ""
echo "Useful commands:"
echo "  • Check timer status:   systemctl --user status $SERVICE_NAME.timer"
echo "  • Check service logs:   journalctl --user -u $SERVICE_NAME.service"
echo "  • Follow logs:          journalctl --user -u $SERVICE_NAME.service -f"
