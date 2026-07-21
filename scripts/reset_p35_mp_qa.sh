#!/usr/bin/env bash
# P35.1 — Founder Mini Program QA reset harness wrapper
#
# Usage:
#   bash scripts/reset_p35_mp_qa.sh status
#   bash scripts/reset_p35_mp_qa.sh inspect --session-id wx_xxxx
#   bash scripts/reset_p35_mp_qa.sh fresh --session-id wx_xxxx --confirm FRESH
#   bash scripts/reset_p35_mp_qa.sh active --session-id wx_xxxx --confirm ACTIVE --target qa
#   bash scripts/reset_p35_mp_qa.sh request-more --session-id wx_xxxx --confirm REQUEST_MORE --target qa
#
# Get session_id (WeChat DevTools console):
#   wx.getStorageSync('mp_customer_session_id')

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_DIR"

if [[ $# -lt 1 ]]; then
  sed -n '2,14p' "$0"
  exit 2
fi

PYTHONPATH=. python3 scripts/p35_mp_qa_harness.py "$@"
