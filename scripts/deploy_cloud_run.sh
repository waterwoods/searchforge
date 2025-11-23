#!/usr/bin/env bash
# scripts/deploy_cloud_run.sh - Deploy backend API to GCP Cloud Run
#
# This script builds a Docker image and deploys it to Cloud Run.
# Prerequisites:
#   - gcloud CLI installed and authenticated
#   - Docker installed and running
#   - GCP project with Cloud Run API enabled
#   - Default project set: gcloud config set project YOUR_PROJECT_ID
#
# After deployment, you still need to:
#   1. Go to Cloud Run console to set environment variables:
#      - OPENAI_API_KEY
#      - USE_ML_APPROVAL_SCORE=true
#      - LLM_GENERATION_ENABLED=true
#      - ALLOWED_ORIGINS=https://your-frontend-domain
#   2. Or use: gcloud run services update SERVICE_NAME --update-env-vars KEY=VALUE

set -euo pipefail

# ========================================
# Configuration (can be overridden via env vars)
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
SERVICE_NAME="${SERVICE_NAME:-mortgage-agent-api}"
REGION="${REGION:-us-west1}"
IMAGE_NAME="${IMAGE_NAME:-gcr.io/${PROJECT_ID}/${SERVICE_NAME}}"

# Alternative: Use Artifact Registry (recommended for new projects)
# ARTIFACT_REGISTRY="${ARTIFACT_REGISTRY:-${REGION}-docker.pkg.dev}"
# IMAGE_NAME="${IMAGE_NAME:-${ARTIFACT_REGISTRY}/${PROJECT_ID}/${SERVICE_NAME}/${SERVICE_NAME}}"

PORT="${PORT:-8080}"

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
echo "📝 Next steps:"
echo "   1. Get the service URL:"
echo "      gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)'"
echo ""
echo "   2. Set environment variables in Cloud Run console:"
echo "      - OPENAI_API_KEY=your-key"
echo "      - USE_ML_APPROVAL_SCORE=true"
echo "      - LLM_GENERATION_ENABLED=true"
echo "      - ALLOWED_ORIGINS=https://your-frontend-domain"
echo ""
echo "   3. Or use gcloud to update env vars:"
echo "      gcloud run services update $SERVICE_NAME \\"
echo "        --region $REGION \\"
echo "        --update-env-vars OPENAI_API_KEY=your-key,USE_ML_APPROVAL_SCORE=true,LLM_GENERATION_ENABLED=true,ALLOWED_ORIGINS=https://your-frontend-domain"
echo ""
echo "   4. Test the endpoint:"
echo "      curl \$(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)')/health"
echo ""

