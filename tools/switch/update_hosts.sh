#!/usr/bin/env bash
# Update /etc/hosts with IP from SSH config for remote hostname resolution

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$WORKSPACE_ROOT"

HOST=${HOST:-andy-wsl}

# Get IP from SSH config
IP=$(ssh -G "$HOST" 2>/dev/null | awk '/^hostname /{print $2}')

if [ -z "$IP" ]; then
    echo "❌ Error: Could not determine IP address for host '$HOST'"
    echo "   Make sure '$HOST' is configured in ~/.ssh/config"
    exit 1
fi

# Detect OS for sed syntax
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS uses BSD sed
    SED_INPLACE="sed -i ''"
else
    # Linux uses GNU sed
    SED_INPLACE="sed -i"
fi

# Check if entry exists in /etc/hosts (handle cases where HOST appears alone or with other hostnames)
if grep -qE "^\s*[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+\s+.*\b${HOST}\b" /etc/hosts 2>/dev/null; then
    # Entry exists, replace IP
    echo "Updating existing entry for $HOST in /etc/hosts..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS: replace IP on lines containing the hostname
        sudo sed -i '' -E "s/^([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)([[:space:]]+.*\b${HOST}\b.*)$/${IP}\2/" /etc/hosts
    else
        # Linux: replace IP on lines containing the hostname
        sudo sed -i -E "s/^([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)([[:space:]]+.*\b${HOST}\b.*)$/${IP}\2/" /etc/hosts
    fi
else
    # Entry doesn't exist, append it
    echo "Adding new entry for $HOST to /etc/hosts..."
    echo "$IP $HOST" | sudo tee -a /etc/hosts > /dev/null
fi

echo "✅ Updated /etc/hosts: $IP $HOST"
