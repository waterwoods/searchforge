# Cloud Run Deployment Guide

## Summary of Changes

### Code Changes
1. **`services/fiqa_api/health/ready.py`** - Added `DEMO_MODE` support to make embedding model optional for readiness checks
2. **`services/fiqa_api/clients.py`** - Enhanced Qdrant connection error logging with detailed diagnostics
3. **`scripts/deploy_rag_demo.sh`** - Updated to automatically include `DEMO_MODE=true` in Cloud Run environment variables
4. **`services/fiqa_api/Dockerfile.cloudrun`** - Added build-time fastembed model pre-download to avoid runtime HuggingFace download failures

### New Scripts
1. **`scripts/check_env_vars.sh`** - Helper to validate required environment variables without printing secrets
2. **`scripts/deploy_and_verify_cloud_run.sh`** - Complete deployment and verification script that:
   - Checks environment variables
   - Preflight verifies Qdrant Cloud connectivity
   - Deploys to Cloud Run
   - Waits for readiness (up to 3 minutes)
   - Tests query endpoint
   - Prints final checklist

## Deployment Steps

### Prerequisites
1. Set required environment variables:
   ```bash
   export QDRANT_URL=https://your-qdrant-cloud-instance.qdrant.io
   export QDRANT_API_KEY=your-api-key
   export QDRANT_COLLECTION=fiqa_10k_v1
   export GCP_PROJECT=your-project-id
   export GCP_REGION=us-west1
   ```

2. Or source from a `.env` file:
   ```bash
   source .env.cloudrun
   ```

### Deploy and Verify

Run the complete deployment script:
```bash
bash scripts/deploy_and_verify_cloud_run.sh
```

This will:
1. ✅ Check all required environment variables
2. ✅ Preflight verify Qdrant Cloud connectivity
3. ✅ Deploy to Cloud Run with `DEMO_MODE=true`
4. ✅ Wait for service readiness (up to 3 minutes)
5. ✅ Test query endpoint with sample queries
6. ✅ Print final checklist

### Manual Steps (Alternative)

If you prefer to run steps manually:

```bash
# Step 1: Check env vars
bash scripts/check_env_vars.sh

# Step 2: Preflight check
export DEMO_MODE=true
python3 scripts/verify_qdrant_cloud.py

# Step 3: Deploy
bash scripts/deploy_rag_demo.sh

# Step 4: Wait for readiness (check every 10s, max 3 minutes)
CLOUD_RUN_URL=$(gcloud run services describe fiqa-api --region us-west1 --format 'value(status.url)')
for i in {1..18}; do
  echo "Attempt $i/18:"
  curl -sS "$CLOUD_RUN_URL/readyz" | python3 -m json.tool
  sleep 10
done

# Step 5: Test query
curl -sS -X POST "$CLOUD_RUN_URL/api/query" \
  -H "Content-Type: application/json" \
  -d '{"question":"what is diversification","top_k":5}' | python3 -m json.tool
```

## Service URL

After deployment, capture the service URL:
```bash
CLOUD_RUN_URL=$(gcloud run services describe fiqa-api --region us-west1 --format 'value(status.url)')
echo "Service URL: $CLOUD_RUN_URL"
```

Default URL (may change after redeployment):
- `https://fiqa-api-g7zatxrycq-uw.a.run.app`

## Verification Checklist

After deployment, verify:

- [ ] `/healthz` returns 200
- [ ] `/readyz` returns `ok: true` with `qdrant_connected: true`
- [ ] `/api/query` returns results with `doc_id` and `text`/`snippet` fields
- [ ] Qdrant Cloud collection has ~10,000 points (if checking)

## Troubleshooting

### /readyz not ready

If `/readyz` is still `not_ready` after deployment:

1. Check Cloud Run logs:
   ```bash
   gcloud run services logs read fiqa-api --region us-west1 --limit 100
   ```

2. Common issues:
   - **Qdrant connection/auth failure**: Verify `QDRANT_URL` and `QDRANT_API_KEY` are correct
   - **Network connectivity**: Ensure Cloud Run can reach Qdrant Cloud
   - **Missing env vars**: Check that all required variables are set in Cloud Run

3. Check service environment variables:
   ```bash
   gcloud run services describe fiqa-api --region us-west1 --format 'value(spec.template.spec.containers[0].env)'
   ```

### Query endpoint returns no results

1. Verify collection exists and has data:
   ```bash
   python3 scripts/verify_qdrant_cloud.py
   ```

2. Check query response format:
   ```bash
   curl -sS -X POST "$CLOUD_RUN_URL/api/query" \
     -H "Content-Type: application/json" \
     -d '{"question":"test","top_k":5}' | python3 -m json.tool
   ```

3. Try different queries:
   - "what is diversification"
   - "risk premium"
   - "bond duration"

## Environment Variables Reference

### Required
- `QDRANT_URL` - Qdrant Cloud instance URL
- `QDRANT_API_KEY` - Qdrant Cloud API key
- `QDRANT_COLLECTION` - Collection name (e.g., `fiqa_10k_v1`)
- `GCP_PROJECT` - Google Cloud Project ID
- `GCP_REGION` - Google Cloud Region

### Automatically Set
- `DEMO_MODE=true` - Set automatically by deploy script

### Optional
- `OPENAI_API_KEY` - For LLM features (not required for retrieval-only)
- `ALLOWED_ORIGINS` - CORS origins (comma-separated)

## Build-Time Optimizations

### Embedding Model Pre-Download

The Dockerfile includes a build-time step to pre-download and cache the fastembed model (`BAAI/bge-small-en-v1.5`). This ensures:
- ✅ Model is available immediately at runtime (no HuggingFace download needed)
- ✅ Avoids network failures during cold start
- ✅ Faster container startup (model already cached)

The model is downloaded during Docker build, so runtime doesn't need HuggingFace network access. This prevents `embedding_warming` errors caused by download failures.

**Note**: The model name used at build time (`BAAI/bge-small-en-v1.5`) matches the runtime default. If you need a different model, set `FASTEMBED_MODEL` environment variable consistently at both build and runtime.

## Cost Controls

The deployment uses cost-safe defaults (see `scripts/deploy_rag_demo.sh`; live `fiqa-api` parity):
- Min instances: 0 (scales to zero)
- Max instances: 2
- CPU: 1
- Memory: 1Gi
- Timeout: 60s
- Concurrency: 30
