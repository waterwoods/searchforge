#!/bin/bash
# Get dataset information from the latest succeeded job

API_URL="${API_URL:-http://localhost:8011}"

echo "Fetching latest succeeded job..." >&2

# Step 1: Get the latest succeeded job ID
JOB_ID=$(curl -s "${API_URL}/api/experiment/jobs" \
  | jq -r '.jobs | map(select(.status=="SUCCEEDED")) | last | .job_id')

if [ -z "$JOB_ID" ] || [ "$JOB_ID" = "null" ]; then
  echo "Error: No succeeded job found" >&2
  exit 1
fi

echo "Found job_id: $JOB_ID" >&2

# Step 2: Get dataset information
echo "Fetching job details..." >&2
curl -s "${API_URL}/api/experiment/job/${JOB_ID}" \
  | jq '.config | {dataset_name, qrels_name, qdrant_collection}'






