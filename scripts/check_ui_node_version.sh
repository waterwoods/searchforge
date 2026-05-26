#!/usr/bin/env bash
# scripts/check_ui_node_version.sh — fail fast when Node is too old for Vite 7 UI build
#
# Usage (from repo root):
#   bash scripts/check_ui_node_version.sh
#   bash scripts/check_ui_node_version.sh --quiet   # exit code only

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
QUIET=0
if [[ "${1:-}" == "--quiet" ]]; then
    QUIET=1
fi

_required_from_nvmrc() {
    local nvmrc="$REPO_ROOT/.nvmrc"
    if [[ -f "$nvmrc" ]]; then
        tr -d 'v \t\r\n' < "$nvmrc"
        return
    fi
    echo "22.22.0"
}

REQUIRED="$(_required_from_nvmrc)"
REQUIRED_MAJOR="${REQUIRED%%.*}"

if ! command -v node >/dev/null 2>&1; then
    echo "❌ node not found on PATH (required: Node ${REQUIRED_MAJOR}.x, see .nvmrc → ${REQUIRED})" >&2
    echo "   Hint: nvm use && cd ui && npm run build" >&2
    exit 1
fi

CURRENT="$(node -v | tr -d 'v')"
CURRENT_MAJOR="${CURRENT%%.*}"

if [[ "$CURRENT_MAJOR" != "$REQUIRED_MAJOR" ]]; then
    echo "❌ Node ${CURRENT} on PATH — UI build requires Node ${REQUIRED_MAJOR}.x (see .nvmrc → ${REQUIRED})" >&2
    echo "   Hint: nvm install ${REQUIRED} && nvm use" >&2
    echo "   Or:  source scripts/with_node22_path.sh  (see docs/runbooks/NODE_22_SETUP.md)" >&2
    exit 1
fi

if [[ "$QUIET" -eq 0 ]]; then
    echo "✅ Node ${CURRENT} OK for UI build (required major: ${REQUIRED_MAJOR}.x, .nvmrc: ${REQUIRED})"
fi
