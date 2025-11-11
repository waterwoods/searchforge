#!/usr/bin/env bash

set -euo pipefail

if ! command -v tailscale >/dev/null 2>&1; then
  curl -fsSL https://tailscale.com/install.sh | sh
fi

sudo systemctl enable --now tailscaled
sudo tailscale up --ssh
tailscale status

echo "[tailscale] SSH enabled. Use: tailscale ssh andy@$(hostname) 'hostname -I'"

