#!/usr/bin/env bash
# scripts/deploy_vitals_ingest.sh - Deploy vitals ingest service to GCP Cloud Run
#
# This script builds and deploys a dedicated Cloud Run service for ESP32 health vitals ingestion.
# Service name: vitals-ingest
# Endpoint: POST /api/vitals/ingest

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
SERVICE_NAME="vitals-ingest"
REGION="us-central1"  # Same region as vitals-viewer
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"
PORT="8080"

# ========================================
# Script directory detection
# ========================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DOCKERFILE_PATH="${REPO_ROOT}/services/fiqa_api/Dockerfile.cloudrun"

# ========================================
# Validation
# ========================================
if [ ! -f "$DOCKERFILE_PATH" ]; then
    echo "❌ Error: Dockerfile not found at $DOCKERFILE_PATH"
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

cd "$REPO_ROOT"

# Build the image
docker build \
    -t "$IMAGE_NAME" \
    -f "$DOCKERFILE_PATH" \
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
    --memory 512Mi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 10 \
    --timeout 300 \
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
    echo "✅ Vitals Ingest Service Deployed"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "Service Name: $SERVICE_NAME"
    echo "Region: $REGION"
    echo "Ingest URL: $SERVICE_URL/api/vitals/ingest"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "📋 Verification Command:"
    echo "curl -X POST $SERVICE_URL/api/vitals/ingest \\"
    echo "  -H \"Content-Type: application/json\" \\"
    echo "  -d '{\"hr\": 75.0, \"spo2\": 98.0}'"
    echo ""
fi
