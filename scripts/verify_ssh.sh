#!/usr/bin/env bash

set -euo pipefail

HOST=${HOST:-andy-wsl}

echo "== DNS/hosts =="
getent hosts "$HOST" || true

echo "== Ping =="
ping -c 2 "$HOST" || true

echo "== Port 22 check =="
nc -vz "$HOST" 22 || true

echo "== SSH test =="
ssh -o BatchMode=yes "$HOST" 'echo ok && hostname && whoami'

