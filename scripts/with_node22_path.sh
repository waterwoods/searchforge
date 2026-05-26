#!/usr/bin/env bash
# Prepend Node 22 from nvm to PATH (Cursor/WSL often defaults to Node 20).
#
# Usage (from repo root):
#   source scripts/with_node22_path.sh
#   node --version && cd ui && npm run build
#
# Trial scripts source this automatically unless SKIP_NVM_NODE22_FOR_UI=1.

_with_node22_repo_root() {
    if [[ -n "${BASH_SOURCE[0]:-}" ]]; then
        local _src
        _src="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
        echo "$(cd "$_src/.." && pwd)"
    else
        echo "$(pwd)"
    fi
}

_prepend_node22_path() {
    local repo_root required ver
    repo_root="$(_with_node22_repo_root)"
    required="22.22.0"
    if [[ -f "$repo_root/.nvmrc" ]]; then
        required="$(tr -d 'v \t\r\n' < "$repo_root/.nvmrc")"
    fi
    ver="v${required}"

    for nv in \
        "$HOME/.nvm/versions/node/${ver}/bin" \
        "$HOME/.nvm/versions/node/v22.22.0/bin" \
        "$HOME/.nvm/versions/node/v22.14.0/bin"; do
        if [[ -x "$nv/node" ]]; then
            export PATH="$nv:$PATH"
            return 0
        fi
    done

    if [[ -s "${NVM_DIR:-$HOME/.nvm}/nvm.sh" ]]; then
        # shellcheck disable=SC1090
        . "${NVM_DIR:-$HOME/.nvm}/nvm.sh"
        nvm use "${required}" 2>/dev/null || nvm use 22 2>/dev/null || true
    fi
}

if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then
    _prepend_node22_path
else
    echo "Source this file: source scripts/with_node22_path.sh" >&2
    exit 1
fi
