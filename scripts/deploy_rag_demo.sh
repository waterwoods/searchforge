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

# ========================================
# Configuration (with defaults)
# ========================================
PROJECT_ID="${PROJECT_ID:-optimal-disk-472305-e2}"
REGION="${REGION:-us-west1}"
SERVICE_NAME="${SERVICE_NAME:-fiqa-api}"
DOCKERFILE_PATH="services/fiqa_api/Dockerfile.cloudrun"

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
        echo "❌ Error: QDRANT_API_KEY is required for Qdrant Cloud"
        echo ""
        echo "   Get your API key from the Qdrant Cloud dashboard"
        echo "   Then set: export QDRANT_API_KEY=your-api-key"
        exit 1
    fi
    
    # Quick validation using Python (if available)
    if command -v python3 &> /dev/null; then
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
    else
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
# Create temporary cloudbuild.yaml for the build
CLOUDBUILD_TMP=$(mktemp)
cat > "$CLOUDBUILD_TMP" <<EOF
steps:
- name: 'gcr.io/cloud-builders/docker'
  args: ['build', '-f', '$DOCKERFILE_PATH', '-t', '$IMAGE_NAME', '.']
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
ENV_VARS=(
    "QDRANT_URL=$QDRANT_URL"
    "QDRANT_COLLECTION=$QDRANT_COLLECTION"
    "DEMO_MODE=true"
    "TRANSLATION_ENABLED=1"
    "TRANSLATION_PROVIDER=argos"
)

if [ -n "$QDRANT_API_KEY" ]; then
    ENV_VARS+=("QDRANT_API_KEY=$QDRANT_API_KEY")
fi

# CORS: allow Vercel frontend when ALLOWED_ORIGINS is set in .env.cloudrun
if [ -n "${ALLOWED_ORIGINS:-}" ]; then
    ENV_VARS+=("ALLOWED_ORIGINS=$ALLOWED_ORIGINS")
fi

# OpenAI: required for LLM features (inbox triage, jobhunter, etc.)
if [ -n "${OPENAI_API_KEY:-}" ]; then
    ENV_VARS+=("OPENAI_API_KEY=$OPENAI_API_KEY")
    # Enable LLM triage when OpenAI key is present (override via .env.cloudrun if needed)
    ENV_VARS+=("LLM_GENERATION_ENABLED=${LLM_GENERATION_ENABLED:-1}")
fi

# Deploy to Cloud Run
echo ""
echo "🚀 Deploying to Cloud Run..."
gcloud run deploy "$SERVICE_NAME" \
    --image "$IMAGE_NAME" \
    --platform managed \
    --region "$REGION" \
    --project "$PROJECT_ID" \
    --allow-unauthenticated \
    --port 8080 \
    --memory 512Mi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 2 \
    --timeout 60 \
    --concurrency 80 \
    --set-env-vars "$(IFS=,; echo "${ENV_VARS[*]}")" \
    --quiet

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

HEALTHZ_OK=false
READYZ_OK=false

# Check /healthz
if curl -sf --max-time 10 "${SERVICE_URL}/healthz" > /dev/null 2>&1; then
    HEALTHZ_OK=true
    echo "✅ /healthz: OK"
else
    echo "❌ /healthz: FAILED"
fi

# Check /readyz
if curl -sf --max-time 10 "${SERVICE_URL}/readyz" > /dev/null 2>&1; then
    READYZ_OK=true
    echo "✅ /readyz: OK"
else
    echo "⚠️  /readyz: FAILED (may be normal if Qdrant not ready yet)"
fi

if [ "$HEALTHZ_OK" = false ]; then
    echo ""
    echo "⚠️  Health check failed. Service may still be starting up."
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
echo "   # Health check"
echo "   curl $SERVICE_URL/healthz"
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
echo "   Min Instances: 0 (cost-safe)"
echo "   Max Instances: 2 (cost-safe)"
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
