#!/usr/bin/env bash

set -euo pipefail

REMOTE=${REMOTE:-andy-wsl}
REMOTE_USER=${REMOTE_USER:-andy}

run_remote() {
  if [ -n "${WSL_PASS:-}" ]; then
    ssh "${REMOTE_USER}@${REMOTE}" "WSL_PASS='${WSL_PASS}' bash -s" -- "$@"
  else
    ssh "${REMOTE_USER}@${REMOTE}" "bash -s" -- "$@"
  fi
}

run_remote <<'REMOTE_EOF'
set -euo pipefail

run_sudo() {
  if [ -n "${WSL_PASS:-}" ]; then
    printf '%s\n' "$WSL_PASS" | sudo -S "$@"
  else
    sudo "$@"
  fi
}

if ! command -v sshd >/dev/null 2>&1; then
  run_sudo apt-get update -y
  run_sudo apt-get install -y openssh-server
fi

run_sudo systemctl enable --now ssh

if command -v ufw >/dev/null 2>&1; then
  run_sudo ufw allow 22/tcp || true
fi

SSHD=/etc/ssh/sshd_config
run_sudo sed -i 's/^#\?PubkeyAuthentication.*/PubkeyAuthentication yes/' "$SSHD"
run_sudo sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication yes/' "$SSHD"
run_sudo systemctl restart ssh

echo "[remote] sshd status:"
systemctl is-active ssh || true

echo "[remote] Listening ports:"
ss -tlnp | grep -E ':22 ' || true
REMOTE_EOF

if [ -n "${WSL_PASS:-}" ]; then
  if ! command -v sshpass >/dev/null 2>&1; then
    echo "[local] sshpass is required when WSL_PASS is set. Please install sshpass first."
    exit 1
  fi
  sshpass -p "$WSL_PASS" ssh-copy-id -o StrictHostKeyChecking=accept-new "${REMOTE_USER}@${REMOTE}"
else
  echo "[local] Running ssh-copy-id (password prompt expected once if key not yet installed)"
  ssh-copy-id -o StrictHostKeyChecking=accept-new "${REMOTE_USER}@${REMOTE}"
fi

echo "[server] Public key installed for ${REMOTE_USER}@${REMOTE}"

