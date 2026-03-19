#!/usr/bin/env bash
# scripts/deploy_vitals_ingest_lite.sh - Deploy lightweight vitals ingest service to GCP Cloud Run
#
# Service name: vitals-ingest-lite
# Endpoint: POST /ingest

set -euo pipefail

# ========================================
# Configuration
# ========================================

# Get project ID from gcloud config or env var
PROJECT_ID="${PROJECT_ID:-$(gcloud config get-value project 2>/dev/null || echo '')}"
if [ -z "$PROJECT_ID" ]; then
    echo "❌ Error: PROJECT_ID not set. Either:"
    echo "   export PROJECT_ID=your-project-id"
    echo "   or: gcloud config set project your-project-id"
    exit 1
fi

# Service configuration
SERVICE_NAME="vitals-ingest-lite"
REGION="us-central1"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"
PORT="8080"

# ========================================
# Script directory detection
# ========================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SERVICE_DIR="${REPO_ROOT}/services/vitals_ingest_lite"
DOCKERFILE_PATH="${SERVICE_DIR}/Dockerfile"

# ========================================
# Validation
# ========================================
if [ ! -f "$DOCKERFILE_PATH" ]; then
    echo "❌ Error: Dockerfile not found at $DOCKERFILE_PATH"
    exit 1
fi

if [ ! -f "${SERVICE_DIR}/main.py" ]; then
    echo "❌ Error: main.py not found at ${SERVICE_DIR}/main.py"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker is not installed or not in PATH"
    exit 1
fi

if ! command -v gcloud &> /dev/null; then
    echo "❌ Error: gcloud CLI is not installed or not in PATH"
    exit 1
fi

# ========================================
# Build Docker image
# ========================================
echo "🔨 Building Docker image: $IMAGE_NAME"
echo "   Using Dockerfile: $DOCKERFILE_PATH"
echo "   Project: $PROJECT_ID"
echo ""

cd "$SERVICE_DIR"

# Build the image
docker build \
    -t "$IMAGE_NAME" \
    -f Dockerfile \
    .

if [ $? -ne 0 ]; then
    echo "❌ Error: Docker build failed"
    exit 1
fi

echo "✅ Docker image built successfully"
echo ""

# ========================================
# Push image to GCP registry
# ========================================
echo "📤 Pushing image to GCP registry..."

# Configure Docker to use gcloud as a credential helper
gcloud auth configure-docker --quiet 2>/dev/null || true

# Push the image
docker push "$IMAGE_NAME"

if [ $? -ne 0 ]; then
    echo "❌ Error: Docker push failed"
    echo "   Make sure you're authenticated: gcloud auth configure-docker"
    exit 1
fi

echo "✅ Image pushed successfully"
echo ""

# ========================================
# Deploy to Cloud Run
# ========================================
echo "🚀 Deploying to Cloud Run..."
echo "   Service: $SERVICE_NAME"
echo "   Region: $REGION"
echo "   Image: $IMAGE_NAME"
echo ""

gcloud run deploy "$SERVICE_NAME" \
    --image "$IMAGE_NAME" \
    --platform managed \
    --region "$REGION" \
    --allow-unauthenticated \
    --port "$PORT" \
    --memory 256Mi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 10 \
    --timeout 60 \
    --concurrency 80

if [ $? -ne 0 ]; then
    echo "❌ Error: Cloud Run deployment failed"
    exit 1
fi

echo ""
echo "✅ Deployment successful!"
echo ""

# Get the service URL
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --region "$REGION" --format 'value(status.url)' 2>/dev/null)

if [ -z "$SERVICE_URL" ]; then
    echo "⚠️  Warning: Could not retrieve service URL"
else
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "✅ Vitals Ingest Lite Service Deployed"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "Service Name: $SERVICE_NAME"
    echo "Region: $REGION"
    echo "Ingest URL: $SERVICE_URL/ingest"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "📋 Verification Command:"
    echo "curl -X POST $SERVICE_URL/ingest \\"
    echo "  -H \"Content-Type: application/json\" \\"
    echo "  -d '{\"hr\": 72.5, \"spo2\": 97.8, \"source\": \"esp32-test\"}'"
    echo ""
fi
