#!/usr/bin/env bash
# Print current SearchForge target

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$WORKSPACE_ROOT"

if [ -f .env.current ]; then
    TARGET=$(grep "^SEARCHFORGE_TARGET=" .env.current 2>/dev/null | cut -d'=' -f2- | tr -d '"' || echo "unknown")
    echo "Current target: $TARGET"
else
    echo "Current target: unknown (.env.current not found)"
fi
