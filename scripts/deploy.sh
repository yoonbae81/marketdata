#!/bin/bash
# KRX Price Collection Deployment Script (User Mode)

set -e

# Configuration
INSTALL_DIR="/srv/krx-price"
SYSTEMD_USER_DIR="${HOME}/.config/systemd/user"
SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "� Setting up KRX Price Collection in USER mode..."
echo "   Source: $SRC_DIR"
echo "   Target: $INSTALL_DIR"

# 1. Setup target directory (requires sudo for /srv, then transfer ownership)
if [ ! -d "$INSTALL_DIR" ]; then
    echo "📂 Creating $INSTALL_DIR with sudo..."
    sudo mkdir -p "$INSTALL_DIR"
    sudo chown "${USER}:${USER}" "$INSTALL_DIR"
fi

# Create subdirectories
mkdir -p "${INSTALL_DIR}/data"
mkdir -p "${SYSTEMD_USER_DIR}"

# 2. File installation
echo "📝 Installing application files..."
if [ "$SRC_DIR" != "$INSTALL_DIR" ]; then
    cp -r "${SRC_DIR}"/* "$INSTALL_DIR/" 2>/dev/null || true
fi

# 3. Enable linger so services run without login
echo "👤 Enabling linger for user ${USER}..."
loginctl enable-linger "${USER}"

# 4. Docker build
echo "🐳 Building Docker image at target location..."
cd "$INSTALL_DIR"
docker compose build

# 5. Systemd unit setup (with template processing)
echo "📝 Setting up systemd units..."
SERVICE_TEMPLATE="${INSTALL_DIR}/scripts/systemd/krx-price.service"
TIMER_TEMPLATE="${INSTALL_DIR}/scripts/systemd/krx-price.timer"
SERVICE_TARGET="${SYSTEMD_USER_DIR}/krx-price.service"
TIMER_TARGET="${SYSTEMD_USER_DIR}/krx-price.timer"

# Replace variables in service template
sed "s|{{PROJECT_ROOT}}|$INSTALL_DIR|g" "$SERVICE_TEMPLATE" > "$SERVICE_TARGET"
cp "$TIMER_TEMPLATE" "$TIMER_TARGET"

# 6. Start the timer
echo "🔄 Reloading systemd user daemon..."
systemctl --user daemon-reload
systemctl --user enable krx-price.timer
systemctl --user start krx-price.timer

echo ""
echo "✅ Setup complete for user ${USER} at ${INSTALL_DIR}!"
echo ""
echo "📊 Monitoring (User Mode):"
echo "   Timer status:  systemctl --user status krx-price.timer"
echo "   View logs:     journalctl --user -u krx-price.service -f"
echo "   Trigger now:   systemctl --user start krx-price.service"
echo ""
