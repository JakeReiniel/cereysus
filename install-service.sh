#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_FILE="$SCRIPT_DIR/cereysus-ui.service"

if [ ! -f "$SERVICE_FILE" ]; then
  echo "Error: cereysus-ui.service not found in $SCRIPT_DIR"
  exit 1
fi

echo "Installing Cereysus UI service..."
echo "Make sure you've edited cereysus-ui.service with your username and paths first!"
echo ""

sudo cp "$SERVICE_FILE" /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable cereysus-ui
sudo systemctl start cereysus-ui
sudo systemctl status cereysus-ui
