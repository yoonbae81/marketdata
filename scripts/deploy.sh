#!/bin/bash

# Exit on error
set -e

# Run as root check
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (use sudo)"
  exit 1
fi

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
# Project root is one level up from scripts/
PROJECT_DIR="$( cd "$SCRIPT_DIR/.." &> /dev/null && pwd )"

TARGET_DIR="/srv/krx-price"
CURRENT_USER=$(logname || echo $USER)

echo "Setting up systemd for krx-price..."
echo "Project Dir (Source): $PROJECT_DIR"
echo "Target Dir (Operation): $TARGET_DIR"
echo "User: $CURRENT_USER"

# Create target directory and data directory
echo "Creating directories..."
mkdir -p "$TARGET_DIR"
mkdir -p "$TARGET_DIR/data"

# Copy necessary files to target directory
echo "Copying files to $TARGET_DIR..."
cp -r "$PROJECT_DIR/src" "$TARGET_DIR/"
cp -r "$PROJECT_DIR/scripts" "$TARGET_DIR/"
cp "$PROJECT_DIR/Dockerfile" "$TARGET_DIR/"
cp "$PROJECT_DIR/docker-compose.yml" "$TARGET_DIR/"
cp "$PROJECT_DIR/entrypoint.sh" "$TARGET_DIR/"
cp "$PROJECT_DIR/requirements.txt" "$TARGET_DIR/"

# Fix permissions
chown -R "$CURRENT_USER:$CURRENT_USER" "$TARGET_DIR"

# Template paths
SERVICE_TEMPLATE="$PROJECT_DIR/scripts/systemd/krx-price.service"
TIMER_TEMPLATE="$PROJECT_DIR/scripts/systemd/krx-price.timer"

# Target paths
SERVICE_TARGET="/etc/systemd/system/krx-price.service"
TIMER_TARGET="/etc/systemd/system/krx-price.timer"

# Create service file from template
# Use TARGET_DIR as the WorkingDirectory
sed -e "s|{{PROJECT_ROOT}}|$TARGET_DIR|g" \
    -e "s|{{USER}}|$CURRENT_USER|g" \
    "$SERVICE_TEMPLATE" > "$SERVICE_TARGET"

# Copy timer file
cp "$TIMER_TEMPLATE" "$TIMER_TARGET"

# Reload systemd
echo "Reloading systemd daemon..."
systemctl daemon-reload

# Build the docker image at the target location
echo "Building Docker image at $TARGET_DIR..."
cd "$TARGET_DIR"
docker compose build

# Enable and start the timer
echo "Enabling and starting krx-price.timer..."
systemctl enable krx-price.timer
systemctl start krx-price.timer

echo "Systemd setup complete!"
echo "The application is now operating from $TARGET_DIR"
systemctl status krx-price.timer --no-pager
