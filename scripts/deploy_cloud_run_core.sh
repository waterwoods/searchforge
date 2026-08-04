#!/usr/bin/env bash
# scripts/deploy_cloud_run_core.sh - Shared Cloud Run deploy implementation for fiqa-api
#
# **Operators:** use an entry script — do not invoke this file directly unless you know posture.
#   Paid broker pilot:  bash scripts/deploy_paid_pilot.sh
#   Cloud QA (P36):     bash scripts/deploy_cloud_qa.sh   → .env.cloudrun.qa / fiqa-api-qa
#   Demo cloud smoke:   bash scripts/deploy_demo_cloud_smoke.sh
#
# This file loads the env file selected by DEPLOY_ENTRY / CLOUD_RUN_ENV_FILE and deploys.
# Posture (DEMO_MODE vs product_only+PG) follows ENV / PILOT_DEPLOY_STRICT / flags when invoked.
#
# Requires: gcloud CLI, authenticated account, and the selected env file
#
# Usage (prefer wrappers above):
#   cp configs/demo.env.example .env.cloudrun
#   bash scripts/deploy_paid_pilot.sh
#
# Safety-only (no gcloud): DEPLOY_SAFETY_CHECK_ONLY=1 bash scripts/deploy_paid_pilot.sh

set -euo pipefail

# ========================================
# Load Environment Variables (Production vs Cloud QA)
# ========================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Env file selection (P36 T3):
#   CLOUD_RUN_ENV_FILE override wins when set by wrapper
#   DEPLOY_ENTRY=cloud_qa → .env.cloudrun.qa
#   default / paid_pilot / demo_smoke → .env.cloudrun
if [ -n "${CLOUD_RUN_ENV_FILE:-}" ]; then
    ENV_FILE="$CLOUD_RUN_ENV_FILE"
elif [ "${DEPLOY_ENTRY:-}" = "cloud_qa" ]; then
    ENV_FILE="$REPO_ROOT/.env.cloudrun.qa"
else
    ENV_FILE="$REPO_ROOT/.env.cloudrun"
fi

if [ ! -f "$ENV_FILE" ]; then
    echo "❌ Error: Missing env file: $ENV_FILE"
    echo ""
    if [ "${DEPLOY_ENTRY:-}" = "cloud_qa" ] || [[ "$(basename "$ENV_FILE")" == ".env.cloudrun.qa" ]]; then
        echo "   Cloud QA: create .env.cloudrun.qa from the template:"
        echo "     cp configs/cloud_qa.env.example .env.cloudrun.qa"
        echo "   SSOT: docs/runbooks/CLOUD_QA_RESOURCE_NAMES.md"
    else
        echo "   Please create .env.cloudrun from the template:"
        echo "     cp configs/demo.env.example .env.cloudrun"
        echo ""
        echo "   Then edit .env.cloudrun and fill in your real secrets (see PILOT ONE PATH in template):"
        echo "     - SERVICE_RECORD_DATABASE_URL, API keys, OPENAI_API_KEY"
        echo "     - QDRANT_* optional for intake-only deploy (intake-core readiness)"
    fi
    echo ""
    echo "   Note: .env.cloudrun / .env.cloudrun.qa are git-ignored and will not be committed."
    exit 1
fi

echo "📋 Loading environment variables from $(basename "$ENV_FILE")..."
# Use set -a to automatically export all variables
set -a
source "$ENV_FILE"
set +a
echo "✅ Environment variables loaded"

# Entry wrappers set DEPLOY_ENTRY so posture wins over stale env-file keys (see deploy_paid_pilot.sh).
_apply_deploy_entry_posture() {
    case "${DEPLOY_ENTRY:-}" in
        paid_pilot)
            export ENV=prod
            export PILOT_DEPLOY_STRICT=1
            export UNIFIED_INTAKE_PRODUCT_ONLY=1
            export UNIFIED_INTAKE_DB_PRIMARY_READS=1
            export UNIFIED_INTAKE_DB_PRIMARY_WRITES=1
            export UNIFIED_INTAKE_JSON_CASE_WRITES=0
            export UNIFIED_INTAKE_JSON_READ_FALLBACK=0
            export UNIFIED_INTAKE_PG_DUAL_WRITE=0
            export UNIFIED_INTAKE_INTAKE_CORE_READINESS=1
            unset DEMO_MODE
            ;;
        cloud_qa)
            # Product-like Cloud QA posture; harness flags remain opt-in from env file only.
            export ENV="${ENV:-qa}"
            export PILOT_DEPLOY_STRICT=1
            export UNIFIED_INTAKE_PRODUCT_ONLY=1
            export UNIFIED_INTAKE_DB_PRIMARY_READS=1
            export UNIFIED_INTAKE_DB_PRIMARY_WRITES=1
            export UNIFIED_INTAKE_JSON_CASE_WRITES=0
            export UNIFIED_INTAKE_JSON_READ_FALLBACK=0
            export UNIFIED_INTAKE_PG_DUAL_WRITE=0
            export UNIFIED_INTAKE_INTAKE_CORE_READINESS=1
            unset DEMO_MODE
            ;;
        demo_smoke)
            unset PILOT_DEPLOY_STRICT
            unset UNIFIED_INTAKE_PRODUCT_ONLY
            unset UNIFIED_INTAKE_DB_PRIMARY_WRITES
            export DEMO_MODE=true
            ;;
    esac
}
_apply_deploy_entry_posture

# P36 T3 — fail-closed deploy safety (env file ↔ service ↔ DB secret ↔ QA harness)
echo "🔒 P36 deploy safety check..."
if ! PYTHONPATH=. python3 "$SCRIPT_DIR/p36_deploy_safety_check.py" \
    --env-file "$ENV_FILE" \
    --deploy-entry "${DEPLOY_ENTRY:-}"; then
    echo "❌ Deploy safety check failed. Refusing to continue (no gcloud deploy)."
    exit 1
fi
echo "✅ Deploy safety check passed"

case "${DEPLOY_SAFETY_CHECK_ONLY:-0}" in
    1|true|TRUE|yes|YES|on|ON)
        echo "✅ DEPLOY_SAFETY_CHECK_ONLY=1 — stopping before gcloud (no deploy)."
        exit 0
        ;;
esac

# Paid-pilot / production-like deploy posture (see docs/CURRENT_PRODUCT_SHAPE.md)
_is_paid_pilot_posture() {
    case "${ENV:-}" in
        [Pp][Rr][Oo][Dd]) return 0 ;;
    esac
    case "${PILOT_DEPLOY_STRICT:-0}" in
        1|true|TRUE|yes|YES|on|ON) return 0 ;;
    esac
    case "${UNIFIED_INTAKE_DB_PRIMARY_WRITES:-0}" in
        1|true|TRUE|yes|YES|on|ON) return 0 ;;
    esac
    case "${UNIFIED_INTAKE_PRODUCT_ONLY:-0}" in
        1|true|TRUE|yes|YES|on|ON) return 0 ;;
    esac
    return 1
}

# Intake SaaS deploy: Qdrant preflight optional when intake-core readiness is on.
# Override: SKIP_QDRANT_DEPLOY_PREFLIGHT=1 (same effect, explicit operator escape hatch).
_skip_qdrant_deploy_preflight() {
    case "${SKIP_QDRANT_DEPLOY_PREFLIGHT:-0}" in
        1|true|TRUE|yes|YES|on|ON) return 0 ;;
    esac
    case "${UNIFIED_INTAKE_INTAKE_CORE_READINESS:-0}" in
        1|true|TRUE|yes|YES|on|ON) return 0 ;;
    esac
    return 1
}

if _is_paid_pilot_posture; then
    echo "🔒 Paid-pilot / product deploy posture — validating env minimum tuple (required)..."
    if ! PYTHONPATH=. python3 "$SCRIPT_DIR/validate_pilot_deploy_env.py" --env-file "$ENV_FILE"; then
        echo "❌ Pilot deploy env validation failed. Fix $(basename "$ENV_FILE") (see docs/CURRENT_PRODUCT_SHAPE.md)."
        exit 1
    fi
fi

# CORS / deploy drift: full deploy uses --set-env-vars with the bundle built below. That replaces the
# service env for keys we pass; keep ALLOWED_ORIGINS complete in the env file or the next deploy can
# narrow CORS vs a manually patched Cloud Run value.
if [ -n "${ALLOWED_ORIGINS:-}" ]; then
    _ORIG_COUNT=$(echo "$ALLOWED_ORIGINS" | awk -F',' '{print NF}')
    echo "ℹ️  ALLOWED_ORIGINS set ($_ORIG_COUNT comma-separated origin(s)) — will be sent to Cloud Run on this deploy."
else
    echo "⚠️  ALLOWED_ORIGINS not set in $(basename "$ENV_FILE") — it will be omitted from --set-env-vars; live service may drop prior ALLOWED_ORIGINS and fall back to permissive demo CORS in app_main.py."
fi

# Optional: bind sensitive env vars from Secret Manager on Cloud Run (no plaintext for these keys).
# Set CLOUD_RUN_USE_SECRET_MANAGER=1 after creating secrets + IAM (see configs/demo.env.example / cloud_qa.env.example).
# Production defaults to cloudsql-private DB secret; Cloud QA must set CLOUD_RUN_SECRET_SERVICE_RECORD_DB explicitly.
CLOUD_RUN_USE_SECRET_MANAGER="${CLOUD_RUN_USE_SECRET_MANAGER:-0}"

# ========================================
# Configuration (with defaults)
# ========================================
PROJECT_ID="${PROJECT_ID:-optimal-disk-472305-e2}"
REGION="${REGION:-us-west1}"
# Never default Cloud QA onto fiqa-api. Production path keeps historic default.
if [ "${DEPLOY_ENTRY:-}" = "cloud_qa" ]; then
    SERVICE_NAME="${SERVICE_NAME:-fiqa-api-qa}"
else
    SERVICE_NAME="${SERVICE_NAME:-fiqa-api}"
fi
DOCKERFILE_PATH="services/fiqa_api/Dockerfile.cloudrun"

# Cloud Run container sizing — keep in sync with live fiqa-api (us-west1).
# Do not lower memory/concurrency here without an explicit ops decision; regressions have caused instability.
# Override in .env.cloudrun if you intentionally diverge (e.g. cost experiments): CLOUD_RUN_MEMORY, CLOUD_RUN_CONCURRENCY
CLOUD_RUN_MEMORY="${CLOUD_RUN_MEMORY:-1Gi}"
CLOUD_RUN_CONCURRENCY="${CLOUD_RUN_CONCURRENCY:-30}"
CLOUD_RUN_MIN_INSTANCES="${CLOUD_RUN_MIN_INSTANCES:-0}"
CLOUD_RUN_MAX_INSTANCES="${CLOUD_RUN_MAX_INSTANCES:-2}"

# Direct VPC egress — Production baseline (fiqa-api): network=default, subnet=default,
# vpc-egress=all-traffic (private Cloud SQL + WeCom NAT parity).
# Cloud QA MUST set these on the first fiqa-api-qa revision (do not deploy broken then patch).
# Override: CLOUD_RUN_VPC_NETWORK / CLOUD_RUN_VPC_SUBNET / CLOUD_RUN_VPC_EGRESS
# Disable only with CLOUD_RUN_DIRECT_VPC=0 (not for real Cloud QA / paid-pilot deploys).
CLOUD_RUN_VPC_NETWORK="${CLOUD_RUN_VPC_NETWORK:-default}"
CLOUD_RUN_VPC_SUBNET="${CLOUD_RUN_VPC_SUBNET:-default}"
CLOUD_RUN_VPC_EGRESS="${CLOUD_RUN_VPC_EGRESS:-all-traffic}"
_CLOUD_RUN_DIRECT_VPC_DEFAULT=1
if [ "${DEPLOY_ENTRY:-}" = "demo_smoke" ]; then
    _CLOUD_RUN_DIRECT_VPC_DEFAULT=0
fi
CLOUD_RUN_DIRECT_VPC="${CLOUD_RUN_DIRECT_VPC:-$_CLOUD_RUN_DIRECT_VPC_DEFAULT}"

# ========================================
# Validation
# ========================================
echo "🔍 Validating prerequisites..."

# Check gcloud
if ! command -v gcloud &> /dev/null; then
    echo "❌ Error: gcloud CLI not found. Install: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check authentication
ACTIVE_ACCOUNT=$(gcloud config get-value account 2>/dev/null || echo "")
if [ -z "$ACTIVE_ACCOUNT" ]; then
    echo "❌ Error: Not authenticated. Run: gcloud auth login"
    exit 1
fi

# Check project
CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null || echo "")
if [ -z "$CURRENT_PROJECT" ]; then
    echo "⚠️  No default project set. Using: $PROJECT_ID"
    gcloud config set project "$PROJECT_ID"
else
    if [ "$CURRENT_PROJECT" != "$PROJECT_ID" ]; then
        echo "⚠️  Current project ($CURRENT_PROJECT) differs from default ($PROJECT_ID)"
        echo "   Using current project: $CURRENT_PROJECT"
        PROJECT_ID="$CURRENT_PROJECT"
    fi
fi

echo "✅ gcloud authenticated as: $ACTIVE_ACCOUNT"
echo "✅ Project: $PROJECT_ID"
echo "✅ Region: $REGION"

# Qdrant — required for full-stack/RAG deploy; optional for intake-core SaaS
QDRANT_API_KEY="${QDRANT_API_KEY:-}"
QDRANT_COLLECTION="${QDRANT_COLLECTION:-auto_insurance_demo_core}"

if [ -z "${QDRANT_URL:-}" ]; then
    if _skip_qdrant_deploy_preflight; then
        echo "ℹ️  Intake-only deploy: QDRANT_URL not set — skipping Qdrant preflight"
        echo "   Triage + workbench run on Postgres; notice/knowledge retrieval disabled until Qdrant is wired."
        echo "   /readyz uses intake_core posture (UNIFIED_INTAKE_INTAKE_CORE_READINESS=1)."
    else
        echo "❌ Error: QDRANT_URL is required for full-stack deploy"
        echo ""
        echo "   For intake SaaS without vectors, set in .env.cloudrun:"
        echo "     UNIFIED_INTAKE_INTAKE_CORE_READINESS=1"
        echo "   Or export SKIP_QDRANT_DEPLOY_PREFLIGHT=1"
        echo ""
        echo "   For RAG/notice flows, set QDRANT_URL in .env.cloudrun (see configs/demo.env.example)."
        exit 1
    fi
elif [[ ! "$QDRANT_URL" =~ ^https?:// ]]; then
    echo "❌ Error: QDRANT_URL must start with http:// or https://"
    exit 1
fi

# Validate Qdrant Cloud connection (when URL is set)
if [ -n "${QDRANT_URL:-}" ] && { [[ "$QDRANT_URL" =~ \.cloud\.qdrant\.io ]] || [[ "$QDRANT_URL" =~ \.qdrant\.io ]]; }; then
    echo "🔍 Detected Qdrant Cloud URL, validating connection..."
    
    if [ -z "$QDRANT_API_KEY" ]; then
        if [ "${CLOUD_RUN_USE_SECRET_MANAGER:-0}" = "1" ]; then
            echo "⚠️  QDRANT_API_KEY not set in .env.cloudrun — skipping Qdrant preflight (Cloud Run uses Secret Manager binding)."
        else
            echo "❌ Error: QDRANT_API_KEY is required for Qdrant Cloud"
            echo ""
            echo "   Get your API key from the Qdrant Cloud dashboard"
            echo "   Then set: export QDRANT_API_KEY=your-api-key"
            exit 1
        fi
    fi
    
    # Quick validation using Python (if available)
    if [ -n "$QDRANT_API_KEY" ] && command -v python3 &> /dev/null; then
        VALIDATION_SCRIPT=$(cat <<'PYTHON_EOF'
import sys
try:
    from qdrant_client import QdrantClient
    import os
    url = os.environ.get('QDRANT_URL')
    api_key = os.environ.get('QDRANT_API_KEY')
    if url and api_key:
        client = QdrantClient(url=url, api_key=api_key)
        client.get_collections()
        print("OK")
    else:
        print("MISSING_VARS")
        sys.exit(1)
except ImportError:
    print("NO_CLIENT")
    sys.exit(1)
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
PYTHON_EOF
)
        VALIDATION_RESULT=$(python3 -c "$VALIDATION_SCRIPT" 2>&1)
        
        if [ "$VALIDATION_RESULT" = "OK" ]; then
            echo "✅ Qdrant Cloud connection validated"
        elif [ "$VALIDATION_RESULT" = "NO_CLIENT" ]; then
            echo "⚠️  Warning: qdrant-client not installed, skipping validation"
            echo "   Install with: pip install qdrant-client"
        elif [ "$VALIDATION_RESULT" = "MISSING_VARS" ]; then
            echo "⚠️  Warning: Could not validate (missing env vars in subprocess)"
        else
            echo "❌ Error: Qdrant Cloud validation failed: $VALIDATION_RESULT"
            echo ""
            echo "   Please verify:"
            echo "   1. QDRANT_URL is correct"
            echo "   2. QDRANT_API_KEY is valid"
            echo "   3. Network connectivity to Qdrant Cloud"
            echo ""
            echo "   Test manually:"
            echo "     python scripts/verify_qdrant_cloud.py"
            exit 1
        fi
    elif [ -n "$QDRANT_API_KEY" ]; then
        echo "⚠️  Warning: python3 not found, skipping Qdrant Cloud validation"
        echo "   Please verify connection manually before deploying"
    fi
fi

# Check Dockerfile exists
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DOCKERFILE_FULL="$REPO_ROOT/$DOCKERFILE_PATH"

if [ ! -f "$DOCKERFILE_FULL" ]; then
    echo "❌ Error: Dockerfile not found at $DOCKERFILE_FULL"
    exit 1
fi

# ========================================
# Build and Deploy
# ========================================
cd "$REPO_ROOT"

echo ""
echo "🚀 Deploying $SERVICE_NAME to Cloud Run..."
echo "   Project: $PROJECT_ID"
echo "   Region: $REGION"
if [ -n "${QDRANT_URL:-}" ]; then
    QDRANT_DISPLAY="${QDRANT_URL}"
    if [[ "$QDRANT_DISPLAY" =~ \.cloud\.qdrant\.io ]]; then
        QDRANT_DISPLAY="https://***.cloud.qdrant.io (masked)"
    fi
    echo "   Qdrant: ${QDRANT_DISPLAY}"
else
    echo "   Qdrant: (none — intake-only deploy)"
fi
echo ""

# Build image using Cloud Build
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest"

echo "📦 Building Docker image..."
GIT_SHA_DEPLOY="$(git -C "$REPO_ROOT" rev-parse --short=9 HEAD 2>/dev/null || echo unknown)"
echo "   GIT_SHA for image: $GIT_SHA_DEPLOY"
# Create temporary cloudbuild.yaml for the build
CLOUDBUILD_TMP=$(mktemp)
cat > "$CLOUDBUILD_TMP" <<EOF
steps:
- name: 'gcr.io/cloud-builders/docker'
  args:
    - 'build'
    - '--build-arg'
    - 'GIT_SHA=$GIT_SHA_DEPLOY'
    - '-f'
    - '$DOCKERFILE_PATH'
    - '-t'
    - '$IMAGE_NAME'
    - '.'
images:
- '$IMAGE_NAME'
EOF
gcloud builds submit \
    --config "$CLOUDBUILD_TMP" \
    --project "$PROJECT_ID" \
    "$REPO_ROOT" \
    --quiet
rm -f "$CLOUDBUILD_TMP"

echo "✅ Image built: $IMAGE_NAME"

# Prepare environment variables
# GIT_SHA_DEPLOY set above for Cloud Build --build-arg; reuse here for runtime env.
# Add-Car pilot flags — explicit defaults match docs/PILOT_CONTRACT_ADD_CAR_V1 / configs/demo.env.example;
# override via .env.cloudrun when needed.
ENABLE_ASSIST_LAYER="${ENABLE_ASSIST_LAYER:-1}"
DEBUG_TRUTH_GUARDRAILS="${DEBUG_TRUTH_GUARDRAILS:-0}"
ADD_CAR_CONTRACT_STRICT="${ADD_CAR_CONTRACT_STRICT:-0}"

ENV_VARS=(
    "TRANSLATION_ENABLED=1"
    "TRANSLATION_PROVIDER=argos"
    "GIT_SHA=$GIT_SHA_DEPLOY"
    "SOURCE_REV=$GIT_SHA_DEPLOY"
    "ENABLE_ASSIST_LAYER=$ENABLE_ASSIST_LAYER"
    "DEBUG_TRUTH_GUARDRAILS=$DEBUG_TRUTH_GUARDRAILS"
    "ADD_CAR_CONTRACT_STRICT=$ADD_CAR_CONTRACT_STRICT"
)

if [ -n "${QDRANT_URL:-}" ]; then
    ENV_VARS+=(
        "QDRANT_URL=$QDRANT_URL"
        "QDRANT_COLLECTION=$QDRANT_COLLECTION"
    )
fi

# Paid pilot: product-only + PG-primary defaults; DEMO_MODE forbidden (validator enforces).
# Legacy demo cloud deploy: relaxed readiness via DEMO_MODE=true.
if _is_paid_pilot_posture; then
    UNIFIED_INTAKE_PRODUCT_ONLY="${UNIFIED_INTAKE_PRODUCT_ONLY:-1}"
    ENV="${ENV:-prod}"
    UNIFIED_INTAKE_DB_PRIMARY_READS="${UNIFIED_INTAKE_DB_PRIMARY_READS:-1}"
    UNIFIED_INTAKE_DB_PRIMARY_WRITES="${UNIFIED_INTAKE_DB_PRIMARY_WRITES:-1}"
    UNIFIED_INTAKE_JSON_CASE_WRITES="${UNIFIED_INTAKE_JSON_CASE_WRITES:-0}"
    UNIFIED_INTAKE_JSON_READ_FALLBACK="${UNIFIED_INTAKE_JSON_READ_FALLBACK:-0}"
    UNIFIED_INTAKE_PG_DUAL_WRITE="${UNIFIED_INTAKE_PG_DUAL_WRITE:-0}"
    ENV_VARS+=(
        "ENV=$ENV"
        "UNIFIED_INTAKE_PRODUCT_ONLY=$UNIFIED_INTAKE_PRODUCT_ONLY"
        "UNIFIED_INTAKE_DB_PRIMARY_READS=$UNIFIED_INTAKE_DB_PRIMARY_READS"
        "UNIFIED_INTAKE_DB_PRIMARY_WRITES=$UNIFIED_INTAKE_DB_PRIMARY_WRITES"
        "UNIFIED_INTAKE_JSON_CASE_WRITES=$UNIFIED_INTAKE_JSON_CASE_WRITES"
        "UNIFIED_INTAKE_JSON_READ_FALLBACK=$UNIFIED_INTAKE_JSON_READ_FALLBACK"
        "UNIFIED_INTAKE_PG_DUAL_WRITE=$UNIFIED_INTAKE_PG_DUAL_WRITE"
    )
    if _skip_qdrant_deploy_preflight; then
        ENV_VARS+=("UNIFIED_INTAKE_INTAKE_CORE_READINESS=1")
    elif [ -n "${UNIFIED_INTAKE_INTAKE_CORE_READINESS:-}" ]; then
        ENV_VARS+=("UNIFIED_INTAKE_INTAKE_CORE_READINESS=$UNIFIED_INTAKE_INTAKE_CORE_READINESS")
    fi
else
    ENV_VARS+=("DEMO_MODE=${DEMO_MODE:-true}")
fi

if [ "$CLOUD_RUN_USE_SECRET_MANAGER" != "1" ] && [ -n "$QDRANT_API_KEY" ]; then
    ENV_VARS+=("QDRANT_API_KEY=$QDRANT_API_KEY")
fi

# CORS: allow Vercel frontend when ALLOWED_ORIGINS is set in .env.cloudrun
if [ -n "${ALLOWED_ORIGINS:-}" ]; then
    ENV_VARS+=("ALLOWED_ORIGINS=$ALLOWED_ORIGINS")
fi
# Optional regex for ephemeral Vercel Preview hosts (see app_main ALLOWED_ORIGIN_REGEX).
if [ -n "${ALLOWED_ORIGIN_REGEX:-}" ]; then
    ENV_VARS+=("ALLOWED_ORIGIN_REGEX=$ALLOWED_ORIGIN_REGEX")
fi

# OpenAI: required for LLM features (inbox triage, jobhunter, etc.)
if [ "$CLOUD_RUN_USE_SECRET_MANAGER" = "1" ] || [ -n "${OPENAI_API_KEY:-}" ]; then
    if [ "$CLOUD_RUN_USE_SECRET_MANAGER" != "1" ] && [ -n "${OPENAI_API_KEY:-}" ]; then
        ENV_VARS+=("OPENAI_API_KEY=$OPENAI_API_KEY")
    fi
    # Enable LLM triage when OpenAI key is present or loaded from Secret Manager (override via .env.cloudrun if needed)
    ENV_VARS+=("LLM_GENERATION_ENABLED=${LLM_GENERATION_ENABLED:-1}")
fi

# Optional: Stage-1 Add-Car service-record Postgres mirror (pilot/staging parity)
# When unset, Cloud Run stays JSON-only for cases; PG consistency checks are skipped remotely.
# Same plaintext-env caveat as OPENAI/Qdrant: prefer Secret Manager for production DB URLs.
if [ "$CLOUD_RUN_USE_SECRET_MANAGER" != "1" ] && [ -n "${SERVICE_RECORD_DATABASE_URL:-}" ]; then
    ENV_VARS+=("SERVICE_RECORD_DATABASE_URL=$SERVICE_RECORD_DATABASE_URL")
fi
# Optional persistence flags — legacy demo cloud path only (paid pilot sets defaults above)
if ! _is_paid_pilot_posture; then
    if [ -n "${UNIFIED_INTAKE_PG_DUAL_WRITE:-}" ]; then
        ENV_VARS+=("UNIFIED_INTAKE_PG_DUAL_WRITE=$UNIFIED_INTAKE_PG_DUAL_WRITE")
    fi
    if [ -n "${UNIFIED_INTAKE_DB_PRIMARY_READS:-}" ]; then
        ENV_VARS+=("UNIFIED_INTAKE_DB_PRIMARY_READS=$UNIFIED_INTAKE_DB_PRIMARY_READS")
    fi
    if [ -n "${UNIFIED_INTAKE_JSON_READ_FALLBACK:-}" ]; then
        ENV_VARS+=("UNIFIED_INTAKE_JSON_READ_FALLBACK=$UNIFIED_INTAKE_JSON_READ_FALLBACK")
    fi
    if [ -n "${UNIFIED_INTAKE_DB_PRIMARY_WRITES:-}" ]; then
        ENV_VARS+=("UNIFIED_INTAKE_DB_PRIMARY_WRITES=$UNIFIED_INTAKE_DB_PRIMARY_WRITES")
    fi
    if [ -n "${UNIFIED_INTAKE_JSON_CASE_WRITES:-}" ]; then
        ENV_VARS+=("UNIFIED_INTAKE_JSON_CASE_WRITES=$UNIFIED_INTAKE_JSON_CASE_WRITES")
    fi
    if [ -n "${UNIFIED_INTAKE_PRODUCT_ONLY:-}" ]; then
        ENV_VARS+=("UNIFIED_INTAKE_PRODUCT_ONLY=$UNIFIED_INTAKE_PRODUCT_ONLY")
    fi
    if [ -n "${ENV:-}" ]; then
        ENV_VARS+=("ENV=$ENV")
    fi
fi

# Pilot SaaS security perimeter (required for paid pilot — validator enforces)
if [ -n "${UNIFIED_INTAKE_INTAKE_API_KEY:-}" ]; then
    ENV_VARS+=("UNIFIED_INTAKE_INTAKE_API_KEY=$UNIFIED_INTAKE_INTAKE_API_KEY")
fi
if [ -n "${UNIFIED_INTAKE_SUPPORT_API_KEY:-}" ]; then
    ENV_VARS+=("UNIFIED_INTAKE_SUPPORT_API_KEY=$UNIFIED_INTAKE_SUPPORT_API_KEY")
fi

# P25 — Launch Golden QA (internal Founder tool; off unless explicitly enabled — never default ON)
if [ -n "${ENABLE_GOLDEN_QA_LAUNCH:-}" ]; then
    ENV_VARS+=("ENABLE_GOLDEN_QA_LAUNCH=$ENABLE_GOLDEN_QA_LAUNCH")
fi

# QA Harness / fixture flags — opt-in only (pass through if set in env file; never default ON).
# Production paid-pilot path refuses truthy harness flags via p36_deploy_safety_check.py.
if [ -n "${ENABLE_P26H_FIXTURE_RUNNER:-}" ]; then
    ENV_VARS+=("ENABLE_P26H_FIXTURE_RUNNER=$ENABLE_P26H_FIXTURE_RUNNER")
fi
if [ -n "${UNIFIED_INTAKE_QA_FIXTURE_SURFACE:-}" ]; then
    ENV_VARS+=("UNIFIED_INTAKE_QA_FIXTURE_SURFACE=$UNIFIED_INTAKE_QA_FIXTURE_SURFACE")
fi
if [ -n "${ENABLE_P35_MP_QA_HARNESS:-}" ]; then
    ENV_VARS+=("ENABLE_P35_MP_QA_HARNESS=$ENABLE_P35_MP_QA_HARNESS")
fi
if [ -n "${P20_SLICE1_REQUEST_MORE:-}" ]; then
    ENV_VARS+=("P20_SLICE1_REQUEST_MORE=$P20_SLICE1_REQUEST_MORE")
fi
# P4 Cap 01 mock Customer Lookup (Cloud QA Founder harness — default OFF)
if [ -n "${P4_CUSTOMER_LOOKUP_MOCK:-}" ]; then
    ENV_VARS+=("P4_CUSTOMER_LOOKUP_MOCK=$P4_CUSTOMER_LOOKUP_MOCK")
fi
if [ -n "${P4_CUSTOMER_LOOKUP_FORCE_UNAVAILABLE:-}" ]; then
    ENV_VARS+=("P4_CUSTOMER_LOOKUP_FORCE_UNAVAILABLE=$P4_CUSTOMER_LOOKUP_FORCE_UNAVAILABLE")
fi
# Chen Demo Invite overlay (QA only — never enable on Production)
if [ -n "${CHEN_DEMO_INVITE_ENABLED:-}" ]; then
    ENV_VARS+=("CHEN_DEMO_INVITE_ENABLED=$CHEN_DEMO_INVITE_ENABLED")
fi

# Optional: default client pack (GET /api/inbox/client-config without ?client= uses this)
if [ -n "${CLIENT_ID:-}" ]; then
    ENV_VARS+=("CLIENT_ID=$CLIENT_ID")
fi

# P20 Customer Start Claim — server-derived office stamp for Mini Program cold-start Cap2 drafts
if [ -n "${UNIFIED_INTAKE_CUSTOMER_START_CLAIM_OFFICE_ID:-}" ]; then
    ENV_VARS+=("UNIFIED_INTAKE_CUSTOMER_START_CLAIM_OFFICE_ID=$UNIFIED_INTAKE_CUSTOMER_START_CLAIM_OFFICE_ID")
fi

# Optional: WeChat OAuth optional binding (staging/pilot — set in .env.cloudrun; never commit secrets)
if [ -n "${WECHAT_APP_ID:-}" ]; then
    ENV_VARS+=("WECHAT_APP_ID=$WECHAT_APP_ID")
fi
if [ -n "${WECHAT_APP_SECRET:-}" ]; then
    ENV_VARS+=("WECHAT_APP_SECRET=$WECHAT_APP_SECRET")
fi
# Mini Program jscode2session (Cloud QA / staging — never Production without review)
if [ -n "${WECHAT_MP_APP_ID:-}" ]; then
    ENV_VARS+=("WECHAT_MP_APP_ID=$WECHAT_MP_APP_ID")
fi
if [ -n "${WECHAT_MP_APP_SECRET:-}" ]; then
    ENV_VARS+=("WECHAT_MP_APP_SECRET=$WECHAT_MP_APP_SECRET")
fi
if [ -n "${WECHAT_MP_ALLOW_SIMULATE:-}" ]; then
    ENV_VARS+=("WECHAT_MP_ALLOW_SIMULATE=$WECHAT_MP_ALLOW_SIMULATE")
fi
if [ -n "${WECHAT_BINDING_REDIRECT_URI:-}" ]; then
    ENV_VARS+=("WECHAT_BINDING_REDIRECT_URI=$WECHAT_BINDING_REDIRECT_URI")
fi
if [ -n "${PUBLIC_API_BASE_URL:-}" ]; then
    ENV_VARS+=("PUBLIC_API_BASE_URL=$PUBLIC_API_BASE_URL")
fi
if [ -n "${API_PUBLIC_URL:-}" ]; then
    ENV_VARS+=("API_PUBLIC_URL=$API_PUBLIC_URL")
fi
if [ -n "${UNIFIED_INTAKE_FRONTEND_ORIGIN:-}" ]; then
    ENV_VARS+=("UNIFIED_INTAKE_FRONTEND_ORIGIN=$UNIFIED_INTAKE_FRONTEND_ORIGIN")
fi
if [ -n "${WECHAT_BINDING_PEPPER:-}" ]; then
    ENV_VARS+=("WECHAT_BINDING_PEPPER=$WECHAT_BINDING_PEPPER")
fi
if [ -n "${WECHAT_BINDING_STATE_SECRET:-}" ]; then
    ENV_VARS+=("WECHAT_BINDING_STATE_SECRET=$WECHAT_BINDING_STATE_SECRET")
fi
if [ -n "${WECHAT_BINDING_ALLOW_SIMULATE:-}" ]; then
    ENV_VARS+=("WECHAT_BINDING_ALLOW_SIMULATE=$WECHAT_BINDING_ALLOW_SIMULATE")
fi

# Optional: WeCom KF callback spike (ADR-004 Phase 0 — set in .env.cloudrun; never commit secrets)
if [ -n "${WECOM_CORP_ID:-}" ]; then
    ENV_VARS+=("WECOM_CORP_ID=$WECOM_CORP_ID")
fi
if [ -n "${WECOM_KF_TOKEN:-}" ]; then
    ENV_VARS+=("WECOM_KF_TOKEN=$WECOM_KF_TOKEN")
fi
if [ -n "${WECOM_KF_ENCODING_AES_KEY:-}" ]; then
    ENV_VARS+=("WECOM_KF_ENCODING_AES_KEY=$WECOM_KF_ENCODING_AES_KEY")
fi
if [ -n "${WECOM_KF_SECRET:-}" ]; then
    ENV_VARS+=("WECOM_KF_SECRET=$WECOM_KF_SECRET")
fi
if [ -n "${WECOM_CORP_SECRET:-}" ]; then
    ENV_VARS+=("WECOM_CORP_SECRET=$WECOM_CORP_SECRET")
fi
if [ -n "${WECOM_SECRET:-}" ]; then
    ENV_VARS+=("WECOM_SECRET=$WECOM_SECRET")
fi
if [ -n "${WECOM_AGENT_SECRET:-}" ]; then
    ENV_VARS+=("WECOM_AGENT_SECRET=$WECOM_AGENT_SECRET")
fi
# P0 fix (WeCom reply idempotency, 2026-07): these two flags were previously
# only ever applied by hand via `gcloud run services update --update-env-vars`
# and were NOT in this bundle. Since this script deploys with --set-env-vars
# (a full replace, not a merge), every prior deploy through this script
# silently dropped them from the live service. Set in .env.cloudrun so they
# survive deploys going forward.
if [ -n "${WECOM_B0_ACTIVE_WORKSPACE:-}" ]; then
    ENV_VARS+=("WECOM_B0_ACTIVE_WORKSPACE=$WECOM_B0_ACTIVE_WORKSPACE")
fi
if [ -n "${WECOM_SLICE_SEND_REPLY:-}" ]; then
    ENV_VARS+=("WECOM_SLICE_SEND_REPLY=$WECOM_SLICE_SEND_REPLY")
fi
if [ -n "${WECOM_INBOX_QUEUE:-}" ]; then
    ENV_VARS+=("WECOM_INBOX_QUEUE=$WECOM_INBOX_QUEUE")
fi
if [ -n "${WECOM_REPLY_OUTBOX:-}" ]; then
    ENV_VARS+=("WECOM_REPLY_OUTBOX=$WECOM_REPLY_OUTBOX")
fi
if [ -n "${WECOM_QUEUE_ADMIN_TOKEN:-}" ]; then
    ENV_VARS+=("WECOM_QUEUE_ADMIN_TOKEN=$WECOM_QUEUE_ADMIN_TOKEN")
fi

# Accident Story Assistant — restricted pilot kill switches (Cloud QA).
# Defaults stay safe when unset; explicit values from .env.cloudrun.qa survive --set-env-vars.
if [ -n "${ACCIDENT_STORY_ASSISTANT_ENABLED:-}" ]; then
    ENV_VARS+=("ACCIDENT_STORY_ASSISTANT_ENABLED=$ACCIDENT_STORY_ASSISTANT_ENABLED")
fi
if [ -n "${ACCIDENT_STORY_LLM:-}" ]; then
    ENV_VARS+=("ACCIDENT_STORY_LLM=$ACCIDENT_STORY_LLM")
fi
if [ -n "${ACCIDENT_STORY_LANGSMITH_TRACING:-}" ]; then
    ENV_VARS+=("ACCIDENT_STORY_LANGSMITH_TRACING=$ACCIDENT_STORY_LANGSMITH_TRACING")
fi
if [ -n "${ACCIDENT_STORY_OFFICE_ALLOWLIST:-}" ]; then
    ENV_VARS+=("ACCIDENT_STORY_OFFICE_ALLOWLIST=$ACCIDENT_STORY_OFFICE_ALLOWLIST")
fi
if [ -n "${ACCIDENT_STORY_LLM_TIMEOUT_SECONDS:-}" ]; then
    ENV_VARS+=("ACCIDENT_STORY_LLM_TIMEOUT_SECONDS=$ACCIDENT_STORY_LLM_TIMEOUT_SECONDS")
fi
if [ -n "${ACCIDENT_STORY_LLM_MAX_RETRIES:-}" ]; then
    ENV_VARS+=("ACCIDENT_STORY_LLM_MAX_RETRIES=$ACCIDENT_STORY_LLM_MAX_RETRIES")
fi

echo "Non-secret Unified Intake / persistence keys in this deploy bundle:"
UNIFIED_BUNDLE_PRINTED=0
for kv in "${ENV_VARS[@]}"; do
    case "$kv" in
        UNIFIED_INTAKE_SUPPORT_API_KEY=*|UNIFIED_INTAKE_INTAKE_API_KEY=*)
            key="${kv%%=*}"
            echo "   ${key}=(set — value not printed)"
            UNIFIED_BUNDLE_PRINTED=1
            ;;
        UNIFIED_INTAKE_*=*|ENABLE_P26H_FIXTURE_RUNNER=*|ENABLE_GOLDEN_QA_LAUNCH=*|ENABLE_P35_MP_QA_HARNESS=*|P20_SLICE1_REQUEST_MORE=*)
            echo "   $kv"
            UNIFIED_BUNDLE_PRINTED=1
            ;;
    esac
done
if [ "$UNIFIED_BUNDLE_PRINTED" -eq 0 ]; then
    if _is_paid_pilot_posture; then
        echo "   (unexpected — paid-pilot bundle should include UNIFIED_INTAKE_* keys above)"
    else
        echo "   (none — legacy demo cloud path; JSON-primary unless set in .env.cloudrun)"
    fi
fi
if [ -n "${SERVICE_RECORD_DATABASE_URL:-}" ] || [ "$CLOUD_RUN_USE_SECRET_MANAGER" = "1" ]; then
    echo "   SERVICE_RECORD_DATABASE_URL=(set — value not printed)"
fi

SECRET_EXTRA_ARGS=()
if [ "$CLOUD_RUN_USE_SECRET_MANAGER" = "1" ]; then
    SM_OPENAI="${CLOUD_RUN_SECRET_OPENAI:-fiqa-openai-api-key}"
    SM_QDRANT="${CLOUD_RUN_SECRET_QDRANT:-fiqa-qdrant-api-key}"
    # Production DB secret default. Cloud QA must use fiqa-service-record-database-url-qa
    # (enforced by p36_deploy_safety_check.py — never silently inherit Production).
    # Legacy Neon secret (fiqa-service-record-database-url) DELETED 2026-07-11 — versions disabled.
    if [ "${DEPLOY_ENTRY:-}" = "cloud_qa" ]; then
        SM_DB="${CLOUD_RUN_SECRET_SERVICE_RECORD_DB:-fiqa-service-record-database-url-qa}"
    else
        SM_DB="${CLOUD_RUN_SECRET_SERVICE_RECORD_DB:-fiqa-service-record-database-url-cloudsql-private}"
    fi
    SM_H5="${CLOUD_RUN_SECRET_H5_TASK_TOKEN:-fiqa-h5-task-token-secret}"
    if [ "$SM_DB" = "fiqa-service-record-database-url" ]; then
        echo "❌ Error: CLOUD_RUN_SECRET_SERVICE_RECORD_DB points to legacy Neon secret."
        echo "   Production: fiqa-service-record-database-url-cloudsql-private"
        echo "   Cloud QA:   fiqa-service-record-database-url-qa"
        echo "   Neon is legacy rollback only — do not deploy against it."
        exit 1
    fi
    if [ "${DEPLOY_ENTRY:-}" = "cloud_qa" ] && [ "$SM_DB" = "fiqa-service-record-database-url-cloudsql-private" ]; then
        echo "❌ Error: Cloud QA deploy refused — Production DB secret bound."
        echo "   Set CLOUD_RUN_SECRET_SERVICE_RECORD_DB=fiqa-service-record-database-url-qa"
        exit 1
    fi
    if [ "${DEPLOY_ENTRY:-}" != "cloud_qa" ] && [ "$SM_DB" = "fiqa-service-record-database-url-qa" ]; then
        echo "❌ Error: Production deploy refused — Cloud QA DB secret bound."
        echo "   Use fiqa-service-record-database-url-cloudsql-private for Production."
        exit 1
    fi
    SECRET_EXTRA_ARGS=(
        --set-secrets
        "OPENAI_API_KEY=${SM_OPENAI}:latest,QDRANT_API_KEY=${SM_QDRANT}:latest,SERVICE_RECORD_DATABASE_URL=${SM_DB}:latest,H5_TASK_TOKEN_SECRET=${SM_H5}:latest"
    )
    echo "🔐 CLOUD_RUN_USE_SECRET_MANAGER=1: binding OPENAI_API_KEY, QDRANT_API_KEY, SERVICE_RECORD_DATABASE_URL, H5_TASK_TOKEN_SECRET from Secret Manager (no plaintext on describe)."
    echo "   SERVICE_RECORD_DATABASE_URL secret: ${SM_DB}:latest"
fi

# Deploy to Cloud Run
echo ""
echo "🚀 Deploying to Cloud Run..."
# Values like ALLOWED_ORIGINS contain commas; gcloud's default --set-env-vars separator is comma.
# Use ^|^ so each KEY=value pair is joined with | (values may include commas; avoid | inside values).
ENV_VARS_FOR_GCLOUD="$(IFS='|'; echo "${ENV_VARS[*]}")"

VPC_EXTRA_ARGS=()
case "${CLOUD_RUN_DIRECT_VPC}" in
    1|true|TRUE|yes|YES|on|ON)
        VPC_EXTRA_ARGS=(
            --network "$CLOUD_RUN_VPC_NETWORK"
            --subnet "$CLOUD_RUN_VPC_SUBNET"
            --vpc-egress "$CLOUD_RUN_VPC_EGRESS"
        )
        echo "🌐 Direct VPC: network=$CLOUD_RUN_VPC_NETWORK subnet=$CLOUD_RUN_VPC_SUBNET vpc-egress=$CLOUD_RUN_VPC_EGRESS"
        ;;
    *)
        echo "⚠️  CLOUD_RUN_DIRECT_VPC disabled — omitting network/subnet/vpc-egress (not for Cloud QA)"
        ;;
esac

gcloud run deploy "$SERVICE_NAME" \
    --image "$IMAGE_NAME" \
    --platform managed \
    --region "$REGION" \
    --project "$PROJECT_ID" \
    --allow-unauthenticated \
    --port 8080 \
    --memory "$CLOUD_RUN_MEMORY" \
    --cpu 1 \
    --min-instances "$CLOUD_RUN_MIN_INSTANCES" \
    --max-instances "$CLOUD_RUN_MAX_INSTANCES" \
    --timeout 60 \
    --concurrency "$CLOUD_RUN_CONCURRENCY" \
    --set-env-vars "^|^${ENV_VARS_FOR_GCLOUD}" \
    "${SECRET_EXTRA_ARGS[@]}" \
    "${VPC_EXTRA_ARGS[@]}" \
    --quiet

# Cloud Run occasionally leaves traffic on the prior revision after a successful
# deploy (seen on fiqa-api-qa). Promote the newest Ready revision explicitly.
LATEST_REV=$(gcloud run revisions list \
    --service "$SERVICE_NAME" \
    --region "$REGION" \
    --project "$PROJECT_ID" \
    --limit 1 \
    --format 'value(metadata.name)' 2>/dev/null || true)
ACTIVE_REV=$(gcloud run services describe "$SERVICE_NAME" \
    --region "$REGION" \
    --project "$PROJECT_ID" \
    --format 'value(status.traffic[0].revisionName)' 2>/dev/null || true)
if [ -n "$LATEST_REV" ] && [ -n "$ACTIVE_REV" ] && [ "$LATEST_REV" != "$ACTIVE_REV" ]; then
    echo "⚠️  Traffic still on $ACTIVE_REV after deploy; promoting $LATEST_REV to 100%..."
    gcloud run services update-traffic "$SERVICE_NAME" \
        --region "$REGION" \
        --project "$PROJECT_ID" \
        --to-revisions "$LATEST_REV=100" \
        --quiet
    echo "✅ Traffic promoted to $LATEST_REV"
fi

# Post-deploy: confirm Cloud Run accepted the requested runtime (catches typos / API drift)
ACTUAL_MEM=$(gcloud run services describe "$SERVICE_NAME" --region "$REGION" --project "$PROJECT_ID" --format='value(spec.template.spec.containers[0].resources.limits.memory)' 2>/dev/null || echo "")
ACTUAL_CC=$(gcloud run services describe "$SERVICE_NAME" --region "$REGION" --project "$PROJECT_ID" --format='value(spec.template.spec.containerConcurrency)' 2>/dev/null || echo "")
if [ -z "$ACTUAL_MEM" ] || [ -z "$ACTUAL_CC" ]; then
    echo "⚠️  Could not read back Cloud Run memory/concurrency (describe failed). Verify manually:"
    echo "     gcloud run services describe $SERVICE_NAME --region $REGION --project $PROJECT_ID"
elif [ "$ACTUAL_MEM" != "$CLOUD_RUN_MEMORY" ] || [ "$ACTUAL_CC" != "$CLOUD_RUN_CONCURRENCY" ]; then
    echo "❌ Runtime parity check failed after deploy."
    echo "   Requested: memory=$CLOUD_RUN_MEMORY concurrency=$CLOUD_RUN_CONCURRENCY"
    echo "   Actual:    memory=$ACTUAL_MEM concurrency=$ACTUAL_CC"
    exit 1
fi
echo "✅ Cloud Run runtime confirmed: memory=$ACTUAL_MEM concurrency=$ACTUAL_CC"

# Post-deploy: Direct VPC parity (required for Cloud QA / paid-pilot private DB path).
# Annotation keys contain '/' — gcloud --format value(...annotations.KEY) is unreliable; use JSON.
case "${CLOUD_RUN_DIRECT_VPC}" in
    1|true|TRUE|yes|YES|on|ON)
        if ! PYTHONPATH=. python3 - "$SERVICE_NAME" "$REGION" "$PROJECT_ID" \
            "$CLOUD_RUN_VPC_NETWORK" "$CLOUD_RUN_VPC_SUBNET" "$CLOUD_RUN_VPC_EGRESS" <<'PY'
import json, subprocess, sys

service, region, project, want_net, want_subnet, want_egress = sys.argv[1:7]
raw = subprocess.check_output(
    [
        "gcloud", "run", "services", "describe", service,
        "--region", region, "--project", project, "--format=json",
    ],
    text=True,
)
ann = (
    json.loads(raw)
    .get("spec", {})
    .get("template", {})
    .get("metadata", {})
    .get("annotations", {})
    or {}
)
egress = ann.get("run.googleapis.com/vpc-access-egress", "")
ifaces = ann.get("run.googleapis.com/network-interfaces", "")
try:
    parsed = json.loads(ifaces) if ifaces else []
except json.JSONDecodeError:
    parsed = []
net = (parsed[0].get("network") if parsed else "") or ""
subnet = (parsed[0].get("subnetwork") if parsed else "") or ""
ok = egress == want_egress and net == want_net and subnet == want_subnet
print(f"vpc-egress={egress} network={net} subnet={subnet}")
if not ok:
    print(
        f"MISMATCH want egress={want_egress} network={want_net} subnet={want_subnet}",
        file=sys.stderr,
    )
    sys.exit(1)
PY
        then
            echo "❌ Direct VPC parity check failed after deploy."
            echo "   Requested: network=$CLOUD_RUN_VPC_NETWORK subnet=$CLOUD_RUN_VPC_SUBNET vpc-egress=$CLOUD_RUN_VPC_EGRESS"
            exit 1
        fi
        echo "✅ Direct VPC confirmed: network=$CLOUD_RUN_VPC_NETWORK subnet=$CLOUD_RUN_VPC_SUBNET vpc-egress=$CLOUD_RUN_VPC_EGRESS"
        ;;
esac

# Get service URL
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
    --region "$REGION" \
    --project "$PROJECT_ID" \
    --format 'value(status.url)')

if [ -z "$SERVICE_URL" ]; then
    echo "❌ Error: Failed to get service URL"
    exit 1
fi

echo ""
echo "✅ Deployment complete!"
echo ""

# ========================================
# Health Checks
# ========================================
echo "🏥 Running health checks..."
echo ""

# Wait a few seconds for service to be ready
sleep 5

# Liveness: Cloud Run’s Google HTTP frontend returns 404 for top-level /healthz before the
# request reaches the container (not an app bug). Canonical probes: /health/live, /readyz.
# See docs/runbooks/KNOWN_DEPLOYMENT_GOTCHAS.md § Cloud Run /healthz.
LIVE_OK=false
READYZ_OK=false

if curl -sf --max-time 10 "${SERVICE_URL}/health/live" > /dev/null 2>&1; then
    LIVE_OK=true
    echo "✅ /health/live: OK (liveness)"
elif curl -sf --max-time 10 "${SERVICE_URL}/api/healthz" > /dev/null 2>&1; then
    LIVE_OK=true
    echo "✅ /api/healthz: OK (liveness alias)"
elif curl -sf --max-time 10 "${SERVICE_URL}/healthz" > /dev/null 2>&1; then
    LIVE_OK=true
    echo "✅ /healthz: OK (non–Cloud Run or future frontend behavior)"
else
    echo "❌ Liveness: FAILED (/health/live and /api/healthz unreachable)"
fi

if curl -sf --max-time 10 "${SERVICE_URL}/readyz" > /dev/null 2>&1; then
    READYZ_OK=true
    echo "✅ /readyz: OK"
else
    if _skip_qdrant_deploy_preflight; then
        echo "⚠️  /readyz: FAILED — check Postgres + API keys (Qdrant optional in intake_core mode)"
        echo "     bash scripts/summarize_readiness_posture.sh --probe '$SERVICE_URL'"
    else
        echo "⚠️  /readyz: FAILED (may be normal if Qdrant/embedding not ready yet)"
    fi
fi

if [ "$LIVE_OK" = false ]; then
    echo ""
    echo "⚠️  Liveness check failed. Service may still be starting up."
    echo "   Check logs:"
    echo "     gcloud run services logs read $SERVICE_NAME --region $REGION --project $PROJECT_ID"
    echo "   Or describe service:"
    echo "     gcloud run services describe $SERVICE_NAME --region $REGION --project $PROJECT_ID"
    echo ""
fi

# ========================================
# Output Summary
# ========================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Cloud Run Service Deployed"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📍 Service URL:"
echo "   $SERVICE_URL"
echo ""
if _skip_qdrant_deploy_preflight; then
    echo "📦 Deploy posture: intake SaaS (Postgres + API keys; Qdrant optional)"
    echo "   Readiness: curl $SERVICE_URL/readyz  → expect intake_core when Postgres healthy"
else
    echo "📦 Deploy posture: full-stack (Qdrant + embedding expected for /readyz)"
fi
echo ""
echo "🧪 Test Commands:"
echo ""
echo "   # Liveness (use on Cloud Run — /healthz may 404 at Google edge)"
echo "   curl $SERVICE_URL/health/live"
echo "   curl $SERVICE_URL/readyz"
echo "   bash scripts/summarize_readiness_posture.sh --probe '$SERVICE_URL'"
echo ""
if _is_paid_pilot_posture; then
    echo "   # Unified Intake support manifest (operator truth)"
    echo "   curl -H 'X-Unified-Intake-Support-Key: <support-key>' $SERVICE_URL/api/inbox/support/deployment-manifest"
else
    echo "   # Legacy RAG query (lab path — not paid pilot product)"
    echo "   curl -X POST $SERVICE_URL/api/query \\"
    echo "     -H 'Content-Type: application/json' \\"
    echo "     -d '{\"question\": \"What is an ETF?\", \"top_k\": 5, \"rerank\": false}'"
fi
echo ""
echo "📊 Service Info:"
echo "   Project: $PROJECT_ID"
echo "   Region: $REGION"
echo "   Service: $SERVICE_NAME"
echo "   Memory: $CLOUD_RUN_MEMORY"
echo "   Concurrency: $CLOUD_RUN_CONCURRENCY"
echo "   Min Instances: $CLOUD_RUN_MIN_INSTANCES (cost-safe default)"
echo "   Max Instances: $CLOUD_RUN_MAX_INSTANCES (cost-safe default)"
echo ""
echo "   Post-deploy runtime guardrail (read-only):"
echo "     bash scripts/guardrail_cloudrun_runtime.sh"
echo ""
echo "   Before inviting anyone to the product (automated slice + manual browser):"
echo "     bash scripts/unified_intake_release_gate.sh '$SERVICE_URL' 'https://<your-exact-frontend-origin>'"
echo "     Then complete: docs/runbooks/RELEASE_CHECKLIST.md (sections C–D + green bar)"
echo ""
echo "🔧 Update Environment Variables:"
echo "   gcloud run services update $SERVICE_NAME \\"
echo "     --region $REGION \\"
echo "     --project $PROJECT_ID \\"
echo "     --update-env-vars KEY=VALUE"
echo ""
echo "📝 View Logs:"
echo "   gcloud run services logs read $SERVICE_NAME --region $REGION --project $PROJECT_ID"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
