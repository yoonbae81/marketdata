#!/bin/bash
set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"
SERVICE_NAME=$(basename "$PROJECT_DIR")

echo "Starting deployment for $SERVICE_NAME..."

# 1. Pull latest code
echo "Pulling latest changes from git..."
if [ -d .git ]; then
    git pull origin main
else
    echo "Warning: Not a git repository, skipping git pull"
fi

# 2. Update dependencies
if [ -f "$PROJECT_DIR/requirements.txt" ]; then
    echo "Updating dependencies..."
    if [ -d "$PROJECT_DIR/.venv" ]; then
        "$PROJECT_DIR/.venv/bin/pip" install -r "$PROJECT_DIR/requirements.txt"
    else
        echo "Warning: .venv not found, skipping dependency update"
    fi
fi

# 3. Restart services (Optional, if systemd is used)
if systemctl --user list-unit-files | grep -q "$SERVICE_NAME.service"; then
    echo "Restarting service..."
    systemctl --user restart "$SERVICE_NAME.service"
else
    echo "Systemd service $SERVICE_NAME.service not found, skipping restart"
fi

echo "Deployment completed successfully!"
