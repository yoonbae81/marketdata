#!/bin/bash

# Exit on error
set -e

# Run as root check
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (use sudo)"
  exit 1
fi

PROJECT_ROOT=$(pwd)
CURRENT_USER=$(logname || echo $USER)

echo "Setting up systemd for krx-price..."
echo "Project Root: $PROJECT_ROOT"
echo "User: $CURRENT_USER"

# Template paths
SERVICE_TEMPLATE="scripts/systemd/krx-price.service"
TIMER_TEMPLATE="scripts/systemd/krx-price.timer"

# Target paths
SERVICE_TARGET="/etc/systemd/system/krx-price.service"
TIMER_TARGET="/etc/systemd/system/krx-price.timer"

# Create service file from template
sed -e "s|{{PROJECT_ROOT}}|$PROJECT_ROOT|g" \
    -e "s|{{USER}}|$CURRENT_USER|g" \
    "$SERVICE_TEMPLATE" > "$SERVICE_TARGET"

# Copy timer file
cp "$TIMER_TEMPLATE" "$TIMER_TARGET"

# Reload systemd
echo "Reloading systemd daemon..."
systemctl daemon-reload

# Enable and start the timer
echo "Enabling and starting krx-price.timer..."
systemctl enable krx-price.timer
systemctl start krx-price.timer

echo "Systemd setup complete!"
systemctl status krx-price.timer --no-pager
