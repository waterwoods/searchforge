#!/bin/bash
# deploy_vitals_viewer.sh - Deploy vitals viewer to Cloud Run

set -e

echo "Deploying vitals-viewer to Cloud Run..."

# Set project
gcloud config set project optimal-disk-472305-e2

# Deploy to Cloud Run
gcloud run deploy vitals-viewer \
  --source services/vitals_viewer \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated

echo ""
echo "✅ Deployment complete!"
echo "The service URL will be shown above."
