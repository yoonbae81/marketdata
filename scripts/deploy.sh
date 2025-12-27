#!/bin/bash
# KRX Price Collection Deployment Script (User Mode)

set -e

# Configuration
DATA_DIR="/srv/krx-price"
SYSTEMD_USER_DIR="${HOME}/.config/systemd/user"
SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "🚀 Setting up KRX Price Collection..."
echo "   Source (Host): $SRC_DIR"
echo "   Data (Host):   $DATA_DIR"

# 1. Setup data directory (requires sudo for /srv, then transfer ownership)
if [ ! -d "$DATA_DIR" ]; then
    echo "📂 Creating $DATA_DIR with sudo..."
    sudo mkdir -p "$DATA_DIR"
    sudo chown "${USER}:${USER}" "$DATA_DIR"
fi

# Create subdirectories in data dir
mkdir -p "${DATA_DIR}/day"
mkdir -p "${DATA_DIR}/minute"
mkdir -p "${SYSTEMD_USER_DIR}"

# 2. File installation (SKIPPED as per request - running from source)
echo "📝 Application will run from $SRC_DIR"

# 3. Enable linger so services run without login
echo "👤 Enabling linger for user ${USER}..."
loginctl enable-linger "${USER}" 2>/dev/null || true

# 4. Docker build
echo "🐳 Building Docker image..."
cd "$SRC_DIR"
docker compose build

# 5. Systemd unit setup (pointing to source directory)
echo "📝 Setting up systemd units..."
SERVICE_TEMPLATE="${SRC_DIR}/scripts/systemd/krx-price.service"
TIMER_TEMPLATE="${SRC_DIR}/scripts/systemd/krx-price.timer"
SERVICE_TARGET="${SYSTEMD_USER_DIR}/krx-price.service"
TIMER_TARGET="${SYSTEMD_USER_DIR}/krx-price.timer"

# Replace variables in service template - using SRC_DIR instead of INSTALL_DIR
sed -e "s|{{PROJECT_ROOT}}|$SRC_DIR|g" \
    -e "s|{{UID}}|$(id -u)|g" \
    -e "s|{{GID}}|$(id -g)|g" \
    "$SERVICE_TEMPLATE" > "$SERVICE_TARGET"
cp "$TIMER_TEMPLATE" "$TIMER_TARGET"

# 6. Start the timer
echo "🔄 Reloading systemd user daemon..."
systemctl --user daemon-reload
systemctl --user enable krx-price.timer
systemctl --user restart krx-price.timer

echo ""
echo "✅ Setup complete for user ${USER}!"
echo "   Source: $SRC_DIR"
echo "   Data:   $DATA_DIR"
echo ""
echo "📊 Monitoring (User Mode):"
echo "   Timer status:  systemctl --user status krx-price.timer"
echo "   View logs:     journalctl --user -u krx-price.service -f"
echo "   Trigger now:   systemctl --user start krx-price.service"
echo ""
