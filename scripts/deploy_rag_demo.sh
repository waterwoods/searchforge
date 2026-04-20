#!/usr/bin/env bash
# scripts/deploy_rag_demo.sh - One-command Cloud Run deployment for fiqa-api
#
# Deploys the fiqa_api backend to Google Cloud Run with cost-safe defaults.
# Requires: gcloud CLI, authenticated account, .env.cloudrun file
#
# Usage:
#   # 1. Create .env.cloudrun from template (if not exists)
#   cp configs/demo.env.example .env.cloudrun
#   # 2. Edit .env.cloudrun with your real values
#   # 3. Run deployment (automatically loads .env.cloudrun)
#   bash scripts/deploy_rag_demo.sh

set -euo pipefail

# ========================================
# Load Environment Variables from .env.cloudrun
# ========================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="$REPO_ROOT/.env.cloudrun"

if [ ! -f "$ENV_FILE" ]; then
    echo "❌ Error: Missing .env.cloudrun file"
    echo ""
    echo "   Please create .env.cloudrun from the template:"
    echo "     cp configs/demo.env.example .env.cloudrun"
    echo ""
    echo "   Then edit .env.cloudrun and fill in your real secrets:"
    echo "     - QDRANT_URL"
    echo "     - QDRANT_API_KEY (if using Qdrant Cloud)"
    echo "     - QDRANT_COLLECTION"
    echo ""
    echo "   Note: .env.cloudrun is git-ignored and will not be committed."
    exit 1
fi

echo "📋 Loading environment variables from .env.cloudrun..."
# Use set -a to automatically export all variables
set -a
source "$ENV_FILE"
set +a
echo "✅ Environment variables loaded"

# CORS / deploy drift: full deploy uses --set-env-vars with the bundle built below. That replaces the
# service env for keys we pass; keep ALLOWED_ORIGINS complete in .env.cloudrun or the next deploy can
# narrow CORS vs a manually patched Cloud Run value.
if [ -n "${ALLOWED_ORIGINS:-}" ]; then
    _ORIG_COUNT=$(echo "$ALLOWED_ORIGINS" | awk -F',' '{print NF}')
    echo "ℹ️  ALLOWED_ORIGINS set ($_ORIG_COUNT comma-separated origin(s)) — will be sent to Cloud Run on this deploy."
else
    echo "⚠️  ALLOWED_ORIGINS not set in .env.cloudrun — it will be omitted from --set-env-vars; live service may drop prior ALLOWED_ORIGINS and fall back to permissive demo CORS in app_main.py."
fi

# Optional: bind sensitive env vars from Secret Manager on Cloud Run (no plaintext for these keys).
# Set CLOUD_RUN_USE_SECRET_MANAGER=1 in .env.cloudrun after creating secrets + IAM (see configs/demo.env.example).
# Secret names default to the production pilot names; override with CLOUD_RUN_SECRET_* if needed.
CLOUD_RUN_USE_SECRET_MANAGER="${CLOUD_RUN_USE_SECRET_MANAGER:-0}"

# ========================================
# Configuration (with defaults)
# ========================================
PROJECT_ID="${PROJECT_ID:-optimal-disk-472305-e2}"
REGION="${REGION:-us-west1}"
SERVICE_NAME="${SERVICE_NAME:-fiqa-api}"
DOCKERFILE_PATH="services/fiqa_api/Dockerfile.cloudrun"

# Cloud Run container sizing — keep in sync with live fiqa-api (us-west1).
# Do not lower memory/concurrency here without an explicit ops decision; regressions have caused instability.
# Override in .env.cloudrun if you intentionally diverge (e.g. cost experiments): CLOUD_RUN_MEMORY, CLOUD_RUN_CONCURRENCY
CLOUD_RUN_MEMORY="${CLOUD_RUN_MEMORY:-1Gi}"
CLOUD_RUN_CONCURRENCY="${CLOUD_RUN_CONCURRENCY:-30}"
CLOUD_RUN_MIN_INSTANCES="${CLOUD_RUN_MIN_INSTANCES:-0}"
CLOUD_RUN_MAX_INSTANCES="${CLOUD_RUN_MAX_INSTANCES:-2}"

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

# Check QDRANT_URL (required)
if [ -z "${QDRANT_URL:-}" ]; then
    echo "❌ Error: QDRANT_URL environment variable is required"
    echo ""
    echo "   QDRANT_URL should be set in .env.cloudrun"
    echo "   Please edit .env.cloudrun and set:"
    echo "     QDRANT_URL=https://your-qdrant-instance.com:6333"
    echo ""
    echo "   Examples:"
    echo "     - Qdrant Cloud: https://xxx.us-east4-0.gcp.cloud.qdrant.io"
    echo "     - Self-hosted: http://1.2.3.4:6333"
    echo "     - Local dev: http://localhost:6333"
    echo ""
    echo "   See configs/demo.env.example for all required variables"
    exit 1
fi

# Validate QDRANT_URL format
if [[ ! "$QDRANT_URL" =~ ^https?:// ]]; then
    echo "❌ Error: QDRANT_URL must start with http:// or https://"
    exit 1
fi

# Optional Qdrant vars
QDRANT_API_KEY="${QDRANT_API_KEY:-}"
# Default to Unified Intake collection; override in .env.cloudrun if needed
QDRANT_COLLECTION="${QDRANT_COLLECTION:-auto_insurance_demo_core}"

# Validate Qdrant Cloud connection (if using cloud)
if [[ "$QDRANT_URL" =~ \.cloud\.qdrant\.io ]] || [[ "$QDRANT_URL" =~ \.qdrant\.io ]]; then
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
# Mask Qdrant URL (cluster ID) in output
QDRANT_DISPLAY="${QDRANT_URL:-}"
if [[ "$QDRANT_DISPLAY" =~ \.cloud\.qdrant\.io ]]; then
    QDRANT_DISPLAY="https://***.cloud.qdrant.io (masked)"
fi
echo "   Qdrant: ${QDRANT_DISPLAY}"
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
    "QDRANT_URL=$QDRANT_URL"
    "QDRANT_COLLECTION=$QDRANT_COLLECTION"
    "DEMO_MODE=true"
    "TRANSLATION_ENABLED=1"
    "TRANSLATION_PROVIDER=argos"
    "GIT_SHA=$GIT_SHA_DEPLOY"
    "SOURCE_REV=$GIT_SHA_DEPLOY"
    "ENABLE_ASSIST_LAYER=$ENABLE_ASSIST_LAYER"
    "DEBUG_TRUTH_GUARDRAILS=$DEBUG_TRUTH_GUARDRAILS"
    "ADD_CAR_CONTRACT_STRICT=$ADD_CAR_CONTRACT_STRICT"
)

if [ "$CLOUD_RUN_USE_SECRET_MANAGER" != "1" ] && [ -n "$QDRANT_API_KEY" ]; then
    ENV_VARS+=("QDRANT_API_KEY=$QDRANT_API_KEY")
fi

# CORS: allow Vercel frontend when ALLOWED_ORIGINS is set in .env.cloudrun
if [ -n "${ALLOWED_ORIGINS:-}" ]; then
    ENV_VARS+=("ALLOWED_ORIGINS=$ALLOWED_ORIGINS")
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
if [ -n "${UNIFIED_INTAKE_PG_DUAL_WRITE:-}" ]; then
    ENV_VARS+=("UNIFIED_INTAKE_PG_DUAL_WRITE=$UNIFIED_INTAKE_PG_DUAL_WRITE")
fi
# Optional: serve case reads from Postgres (multi-instance safe) when URL + flag are set
if [ -n "${UNIFIED_INTAKE_DB_PRIMARY_READS:-}" ]; then
    ENV_VARS+=("UNIFIED_INTAKE_DB_PRIMARY_READS=$UNIFIED_INTAKE_DB_PRIMARY_READS")
fi
if [ -n "${UNIFIED_INTAKE_JSON_READ_FALLBACK:-}" ]; then
    ENV_VARS+=("UNIFIED_INTAKE_JSON_READ_FALLBACK=$UNIFIED_INTAKE_JSON_READ_FALLBACK")
fi
# Optional: Postgres-primary case writes + JSON file writes off (pilot cutover)
if [ -n "${UNIFIED_INTAKE_DB_PRIMARY_WRITES:-}" ]; then
    ENV_VARS+=("UNIFIED_INTAKE_DB_PRIMARY_WRITES=$UNIFIED_INTAKE_DB_PRIMARY_WRITES")
fi
if [ -n "${UNIFIED_INTAKE_JSON_CASE_WRITES:-}" ]; then
    ENV_VARS+=("UNIFIED_INTAKE_JSON_CASE_WRITES=$UNIFIED_INTAKE_JSON_CASE_WRITES")
fi

# Optional: default client pack (GET /api/inbox/client-config without ?client= uses this)
if [ -n "${CLIENT_ID:-}" ]; then
    ENV_VARS+=("CLIENT_ID=$CLIENT_ID")
fi

# Optional: WeChat OAuth optional binding (staging/pilot — set in .env.cloudrun; never commit secrets)
if [ -n "${WECHAT_APP_ID:-}" ]; then
    ENV_VARS+=("WECHAT_APP_ID=$WECHAT_APP_ID")
fi
if [ -n "${WECHAT_APP_SECRET:-}" ]; then
    ENV_VARS+=("WECHAT_APP_SECRET=$WECHAT_APP_SECRET")
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

echo "Non-secret Unified Intake / persistence keys in this deploy bundle:"
UNIFIED_BUNDLE_PRINTED=0
for kv in "${ENV_VARS[@]}"; do
    case "$kv" in
        UNIFIED_INTAKE_*=*)
            echo "   $kv"
            UNIFIED_BUNDLE_PRINTED=1
            ;;
    esac
done
if [ "$UNIFIED_BUNDLE_PRINTED" -eq 0 ]; then
    echo "   (none — Cloud Run JSON-primary unless set in .env.cloudrun)"
fi
if [ -n "${SERVICE_RECORD_DATABASE_URL:-}" ] || [ "$CLOUD_RUN_USE_SECRET_MANAGER" = "1" ]; then
    echo "   SERVICE_RECORD_DATABASE_URL=(set — value not printed)"
fi

SECRET_EXTRA_ARGS=()
if [ "$CLOUD_RUN_USE_SECRET_MANAGER" = "1" ]; then
    SM_OPENAI="${CLOUD_RUN_SECRET_OPENAI:-fiqa-openai-api-key}"
    SM_QDRANT="${CLOUD_RUN_SECRET_QDRANT:-fiqa-qdrant-api-key}"
    SM_DB="${CLOUD_RUN_SECRET_SERVICE_RECORD_DB:-fiqa-service-record-database-url}"
    SECRET_EXTRA_ARGS=(
        --set-secrets
        "OPENAI_API_KEY=${SM_OPENAI}:latest,QDRANT_API_KEY=${SM_QDRANT}:latest,SERVICE_RECORD_DATABASE_URL=${SM_DB}:latest"
    )
    echo "🔐 CLOUD_RUN_USE_SECRET_MANAGER=1: binding OPENAI_API_KEY, QDRANT_API_KEY, SERVICE_RECORD_DATABASE_URL from Secret Manager (no plaintext on describe)."
fi

# Deploy to Cloud Run
echo ""
echo "🚀 Deploying to Cloud Run..."
# Values like ALLOWED_ORIGINS contain commas; gcloud's default --set-env-vars separator is comma.
# Use ^|^ so each KEY=value pair is joined with | (values may include commas; avoid | inside values).
ENV_VARS_FOR_GCLOUD="$(IFS='|'; echo "${ENV_VARS[*]}")"
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
    --quiet

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
    echo "⚠️  /readyz: FAILED (may be normal if Qdrant not ready yet)"
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
echo "🧪 Test Commands:"
echo ""
echo "   # Liveness (use on Cloud Run — /healthz may 404 at Google edge)"
echo "   curl $SERVICE_URL/health/live"
echo "   curl $SERVICE_URL/readyz"
echo ""
echo "   # Query API (example)"
echo "   curl -X POST $SERVICE_URL/api/query \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"question\": \"What is an ETF?\", \"top_k\": 5, \"rerank\": false}'"
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
