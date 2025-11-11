#!/usr/bin/env bash

set -euo pipefail

HOST_ALIAS=${HOST_ALIAS:-andy-wsl}
USER_NAME=${USER_NAME:-andy}
KEY=${KEY:-"$HOME/.ssh/id_ed25519"}

mkdir -p "$HOME/.ssh"
chmod 700 "$HOME/.ssh"

if [ ! -f "$KEY" ]; then
  ssh-keygen -t ed25519 -N "" -f "$KEY"
fi

ssh-keyscan -H "$HOST_ALIAS" 2>/dev/null | sort -u | tee -a "$HOME/.ssh/known_hosts" >/dev/null
chmod 600 "$HOME/.ssh/known_hosts"

CFG="$HOME/.ssh/config"
if ! grep -q "Host $HOST_ALIAS" "$CFG" 2>/dev/null; then
cat >>"$CFG" <<EOF
Host $HOST_ALIAS
  HostName $HOST_ALIAS
  User $USER_NAME
  IdentityFile $KEY
  BatchMode yes
  StrictHostKeyChecking accept-new
  PreferredAuthentications publickey
  ServerAliveInterval 30
  ServerAliveCountMax 4
EOF
chmod 600 "$CFG"
fi

echo "[client] SSH client configured for $HOST_ALIAS"

