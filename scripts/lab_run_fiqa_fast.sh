#!/bin/bash
# lab_run_fiqa_fast.sh - Helper script to run fiqa-fast experiment
# This script is a convenience wrapper for calling the API endpoint.

set -euo pipefail

BASE=${BASE:-http://localhost:8011}

echo "🚀 Submitting fiqa-fast experiment job..."
echo "BASE=$BASE"

# Submit job via API
RESPONSE=$(curl -s -X POST "${BASE}/api/experiment/run" \
  -H 'Content-Type: application/json' \
  -d '{"kind":"fiqa-fast","dataset":"fiqa"}')

# Extract job_id
JOB_ID=$(echo "$RESPONSE" | jq -r '.job_id')

if [ "$JOB_ID" = "null" ] || [ -z "$JOB_ID" ]; then
  echo "❌ Failed to submit job"
  echo "$RESPONSE" | jq .
  exit 1
fi

echo "✅ Job submitted: $JOB_ID"
echo "$RESPONSE" | jq .

# Save job_id for later use
echo "$JOB_ID" > /tmp/last_job_id.txt

echo ""
echo "📊 To check status:"
echo "   curl -s ${BASE}/api/experiment/status/$JOB_ID | jq"
echo ""
echo "📋 To view logs:"
echo "   curl -s ${BASE}/api/experiment/logs/$JOB_ID | jq '.tail | length'"
echo ""
echo "🛑 To cancel:"
echo "   curl -s -X POST ${BASE}/api/experiment/cancel/$JOB_ID | jq"








