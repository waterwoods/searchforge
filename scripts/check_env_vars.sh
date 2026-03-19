#!/usr/bin/env bash
# Helper to check required environment variables without printing values

set -euo pipefail

check_env_var() {
    local var_name="$1"
    if [ -z "${!var_name:-}" ]; then
        echo "❌ Missing: $var_name"
        return 1
    else
        echo "✅ Present: $var_name"
        return 0
    fi
}

# Check all required vars
MISSING=0

check_env_var "QDRANT_URL" || MISSING=1
check_env_var "QDRANT_API_KEY" || MISSING=1
check_env_var "QDRANT_COLLECTION" || MISSING=1
check_env_var "GCP_PROJECT" || MISSING=1
check_env_var "GCP_REGION" || MISSING=1

if [ $MISSING -eq 1 ]; then
    echo ""
    echo "❌ Some required environment variables are missing"
    echo "   Please set them before deploying"
    exit 1
fi

echo ""
echo "✅ All required environment variables are present"
