# Cloud Run Deployment Audit Report

**Generated:** 2025-01-XX  
**Project:** searchforge  
**Target:** GCP Cloud Run (backend) + Vercel (frontend)

---

## 1. What Exists

### 1.1 Cloud Run Deployment Assets

#### ✅ Dockerfile for Cloud Run
- **Path:** `services/fiqa_api/Dockerfile.cloudrun`
- **Status:** ✅ EXISTS
- **Details:**
  - Uses Python 3.11-slim base image
  - Exposes port 8080 (Cloud Run default)
  - Health check endpoint: `/health` (line 59)
  - Entrypoint: `services.fiqa_api.app_main:app`
  - Build context: repo root (expects `requirements.txt` at root)
  - Copies required service modules and dependencies

#### ✅ Deploy Script (Generic)
- **Path:** `scripts/deploy_cloud_run.sh`
- **Status:** ✅ EXISTS (but configured for `mortgage-agent-api`, not `fiqa_api`)
- **Details:**
  - Uses `gcr.io` registry (legacy, should migrate to Artifact Registry)
  - Default region: `us-west1`
  - Default service name: `mortgage-agent-api` (needs update)
  - Includes Docker build, push, and deploy steps
  - Sets: `--min-instances 0`, `--max-instances 10`, `--memory 512Mi`, `--cpu 1`, `--concurrency 80`

#### ⚠️ Makefile Targets
- **Path:** `Makefile`
- **Status:** ❌ NO Cloud Run targets found
- **Note:** Makefile has extensive docker-compose targets but no `gcloud run deploy` targets

#### ⚠️ Kubernetes Manifests
- **Path:** `k8s/`
- **Status:** ✅ EXISTS (but for GKE, not Cloud Run)
- **Note:** Contains deployment.yaml, service.yaml, configmap.yaml, etc. - not relevant for Cloud Run

#### ❌ Cloud Build Configuration
- **Path:** `cloudbuild.yaml`
- **Status:** ❌ NOT FOUND
- **Note:** No Cloud Build YAML for automated deployments

---

### 1.2 Backend Service Entrypoint

#### FastAPI Application
- **Entrypoint:** `services.fiqa_api.app_main:app`
- **File:** `services/fiqa_api/app_main.py`
- **Port Configuration:**
  - Cloud Run: Uses `PORT` env var (defaults to 8080)
  - Local: Uses `MAIN_PORT` env var (defaults to 8000)
  - Dockerfile.cloudrun CMD: `python -m uvicorn services.fiqa_api.app_main:app --host 0.0.0.0 --port ${PORT:-8080}`

#### Health Check Endpoints
- **Liveness:** `/health/live` → `{"ok": true}`
- **Readiness:** `/health/ready` → checks clients_ready status
- **Healthz:** `/healthz` → `{"ok": true, "version": "v11", "status": "healthy", "embedding_ready": bool}`
- **Readyz:** `/readyz` → detailed readiness with clients_ready, qdrant_ok, etc.
- **Qdrant Health:** `/api/health/qdrant` → HTTP + gRPC connectivity check

**Note:** Dockerfile.cloudrun healthcheck uses `/health` (line 59), but app_main.py doesn't define this exact route. Should use `/healthz` or `/health/live` instead.

---

### 1.3 Environment Variables Inventory

#### Required (Core Functionality)
| Variable | Default | Source | Notes |
|----------|---------|--------|-------|
| `PORT` | `8080` | Cloud Run auto-set | ✅ Handled by Cloud Run |
| `QDRANT_HOST` | `localhost` | `services/fiqa_api/clients.py:57` | ❌ Must be external Qdrant URL for Cloud Run |
| `QDRANT_PORT` | `6333` | `services/fiqa_api/clients.py:58` | ❌ Must be external Qdrant port |
| `QDRANT_URL` | `http://{QDRANT_HOST}:{QDRANT_PORT}` | `services/fiqa_api/clients.py:60` | ✅ Can override QDRANT_HOST/PORT |

#### Optional but Recommended
| Variable | Default | Source | Notes |
|----------|---------|--------|-------|
| `OPENAI_API_KEY` | `None` | `services/fiqa_api/app_main.py:57` | ⚠️ Required for code_lookup LLM features |
| `ALLOWED_ORIGINS` | `*` (if ALLOW_ALL_CORS=1) | `services/fiqa_api/app_main.py:169` | ✅ Required for CORS (Vercel frontend) |
| `CORS_ORIGINS` | `""` | `services/fiqa_api/app_main.py:177` | Legacy, use ALLOWED_ORIGINS |
| `MAIN_PORT` | `8000` | `services/fiqa_api/app_main.py:160` | Not used in Cloud Run (uses PORT) |

#### Optional (Feature Flags & Tuning)
| Variable | Default | Source |
|----------|---------|--------|
| `LLM_GENERATION_ENABLED` | `false` | `services/fiqa_api/utils/llm_client.py:26` |
| `USE_ML_APPROVAL_SCORE` | `false` | `services/fiqa_api/mortgage/approval/ml_approval_score.py` |
| `EMBEDDING_MODEL_NAME` | `all-MiniLM-L6-v2` | `services/fiqa_api/clients.py:52` |
| `EMBEDDING_BACKEND` | `FASTEMBED` | `services/fiqa_api/clients.py:54` |
| `API_LOG_LEVEL` | `info` | `services/fiqa_api/app_main.py:41` |
| `FAST_STARTUP` | `1` | `services/fiqa_api/app_main.py:193` |
| `DISABLE_FAISS` | `false` | `services/fiqa_api/app_main.py:501` |
| `VECTOR_BACKEND` | `faiss` | `services/fiqa_api/routes/query.py:443` |
| `COLLECTION_NAME` | `fiqa_50k_v1` | `services/fiqa_api/services/search_core.py:32` |

#### Observability (Optional)
| Variable | Default | Source |
|----------|---------|--------|
| `OBS_ENABLED` | `0` | `services/fiqa_api/obs.py:50` |
| `LANGFUSE_SECRET_KEY` | `None` | `services/fiqa_api/obs.py:50` |
| `LANGFUSE_HOST` | `https://cloud.langfuse.com` | `services/fiqa_api/obs.py:75` |
| `LANGFUSE_PUBLIC_KEY` | `None` | `services/fiqa_api/obs.py:65` |
| `LANGCHAIN_API_KEY` | `None` | `services/fiqa_api/telemetry/langsmith_config.py:39` |

**Summary:** Core requirement is `QDRANT_URL` (or `QDRANT_HOST`+`QDRANT_PORT`). `OPENAI_API_KEY` and `ALLOWED_ORIGINS` are highly recommended.

---

### 1.4 Frontend Configuration

#### ✅ Vite/React Frontend
- **Path:** `ui/`
- **Framework:** Vite + React (confirmed by `ui/package.json`)
- **Vercel Config:** `ui/vercel.json` exists with SPA rewrites
- **Status:** ✅ Ready for Vercel deployment
- **Build Command:** `npm run build` (from `ui/package.json`)
- **Output Directory:** `dist` (Vite default)

**Note:** Frontend should remain on Vercel. No changes needed for Cloud Run deployment.

---

## 2. What Is Missing

### 2.1 Critical Missing Items

1. **❌ fiqa_api-specific deploy script**
   - `scripts/deploy_cloud_run.sh` is configured for `mortgage-agent-api`
   - Needs: service name update, correct Dockerfile path (already correct), env var template

2. **❌ requirements.txt location mismatch**
   - Dockerfile.cloudrun expects `requirements.txt` at repo root (line 26)
   - ✅ Root `requirements.txt` exists, but verify it includes all fiqa_api dependencies

3. **❌ Health check endpoint mismatch**
   - Dockerfile.cloudrun healthcheck uses `/health` (line 59)
   - App defines `/healthz`, `/health/live`, `/health/ready` but not `/health`
   - **Fix:** Update Dockerfile.cloudrun line 59 to use `/healthz` or `/health/live`

4. **❌ External Qdrant dependency**
   - Cloud Run service needs external Qdrant instance (not localhost)
   - Options: Cloud Run Qdrant service, Qdrant Cloud, or separate GCE/GKE instance
   - **Action Required:** Provision external Qdrant and set `QDRANT_URL` env var

5. **❌ Environment variable documentation**
   - No `.env.example` or deployment guide for required vars
   - No template for Cloud Run env vars

### 2.2 Nice-to-Have Missing Items

1. **Cloud Build YAML** (`cloudbuild.yaml`) for CI/CD automation
2. **Makefile target** for Cloud Run deployment (e.g., `make deploy-cloudrun`)
3. **Pre-deployment validation script** (check Qdrant connectivity, env vars, etc.)

---

## 3. Local GCP Setup Status

### ✅ gcloud CLI
- **Version:** `Google Cloud SDK 539.0.0`
- **Status:** ✅ Installed and working

### ✅ Authentication
- **Active Account:** `ainew6380@gmail.com`
- **Status:** ✅ Authenticated

### ✅ Project Configuration
- **Active Project:** `optimal-disk-472305-e2`
- **Default Region:** `us-west1` (from `gcloud config list`)
- **Status:** ✅ Configured

### ✅ Cloud Run API
- **Status:** ✅ ENABLED
- **Service Name:** `projects/1013093472160/services/run.googleapis.com`
- **Action Required:** None

---

## 4. Proposed Cloud Run Deployment Plan

### 4.1 Service Configuration

| Setting | Recommended Value | Rationale |
|---------|-------------------|-----------|
| **Service Name** | `fiqa-api` | Short, clear, matches service directory |
| **Region** | `us-west1` | Matches existing gcloud config default |
| **Port** | `8080` | Cloud Run default (already in Dockerfile) |
| **CPU** | `1` | Cost-effective for low traffic |
| **Memory** | `512Mi` | Sufficient for FastAPI + embeddings (all-MiniLM-L6-v2 is lightweight) |
| **Min Instances** | `0` | ✅ Cost control - scale to zero |
| **Max Instances** | `2` | ✅ Cost control - limit burst (was 10 in deploy script) |
| **Concurrency** | `80` | Standard for FastAPI (can lower to 40-60 if needed) |
| **Timeout** | `300s` | 5 minutes (sufficient for RAG queries) |
| **CPU Allocation** | `CPU_ALWAYS` | Required for min-instances=0 (default) |

### 4.2 Image Registry Strategy

**Recommendation:** Use **Artifact Registry** (modern, recommended) instead of legacy `gcr.io`.

**Artifact Registry Setup:**
```bash
# Create repository (one-time)
gcloud artifacts repositories create fiqa-api-repo \
  --repository-format=docker \
  --location=us-west1 \
  --description="Docker images for fiqa-api Cloud Run service"
```

**Image Name Format:**
```
us-west1-docker.pkg.dev/optimal-disk-472305-e2/fiqa-api-repo/fiqa-api:latest
```

**Alternative:** Use `gcloud run deploy --source` (builds directly from source, no manual Docker build needed).

---

### 4.3 Proposed Deploy Command Template

#### Option A: Using Pre-built Image (Artifact Registry)
```bash
gcloud run deploy fiqa-api \
  --image us-west1-docker.pkg.dev/optimal-disk-472305-e2/fiqa-api-repo/fiqa-api:latest \
  --platform managed \
  --region us-west1 \
  --allow-unauthenticated \
  --port 8080 \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 2 \
  --timeout 300 \
  --concurrency 80 \
  --set-env-vars "QDRANT_URL=https://your-qdrant-instance.com,ALLOWED_ORIGINS=https://your-frontend.vercel.app" \
  --update-secrets "OPENAI_API_KEY=openai-api-key:latest"
```

#### Option B: Using Source Deployment (Recommended for simplicity)
```bash
gcloud run deploy fiqa-api \
  --source . \
  --dockerfile services/fiqa_api/Dockerfile.cloudrun \
  --platform managed \
  --region us-west1 \
  --allow-unauthenticated \
  --port 8080 \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 2 \
  --timeout 300 \
  --concurrency 80 \
  --set-env-vars "QDRANT_URL=https://your-qdrant-instance.com,ALLOWED_ORIGINS=https://your-frontend.vercel.app" \
  --update-secrets "OPENAI_API_KEY=openai-api-key:latest"
```

**Note:** `--source` builds in Cloud Build, no local Docker required.

---

## 5. Environment Variables Checklist

### Required for Deployment

```bash
# Qdrant Connection (REQUIRED)
QDRANT_URL=https://your-qdrant-instance.com:6333
# OR
QDRANT_HOST=your-qdrant-instance.com
QDRANT_PORT=6333

# CORS (REQUIRED for Vercel frontend)
ALLOWED_ORIGINS=https://your-project.vercel.app,https://your-project-git-main.vercel.app
```

### Recommended

```bash
# OpenAI API (for code_lookup LLM features)
OPENAI_API_KEY=sk-...  # Use Secret Manager

# Optional Feature Flags
LLM_GENERATION_ENABLED=true  # If using LLM features
USE_ML_APPROVAL_SCORE=true   # If using ML approval
API_LOG_LEVEL=info
FAST_STARTUP=1
```

### Optional (Tuning)

```bash
EMBEDDING_MODEL_NAME=all-MiniLM-L6-v2
EMBEDDING_BACKEND=FASTEMBED
COLLECTION_NAME=fiqa_50k_v1
DISABLE_FAISS=false
VECTOR_BACKEND=faiss
```

### Observability (Optional)

```bash
OBS_ENABLED=1
LANGFUSE_SECRET_KEY=sk-...  # Use Secret Manager
LANGFUSE_HOST=https://cloud.langfuse.com
LANGFUSE_PUBLIC_KEY=pk-...
```

---

## 6. Cost Control Settings

### Recommended Configuration (Low Cost)

| Setting | Value | Monthly Cost Estimate* |
|---------|-------|------------------------|
| Min Instances | `0` | $0 (scales to zero) |
| Max Instances | `2` | ~$0-20 (pay per request) |
| CPU | `1` | Included |
| Memory | `512Mi` | Included |
| Requests | Pay-per-use | ~$0.40 per 1M requests |
| **Total (low traffic)** | | **~$0-25/month** |

*Assumes low traffic (<100k requests/month), no min instances, and external Qdrant costs not included.

### Cost Optimization Tips

1. **Keep min-instances=0** - Only pay when handling requests
2. **Limit max-instances=2** - Prevent cost spikes from traffic bursts
3. **Use Cloud Run's free tier** - 2M requests/month free
4. **Monitor with Cloud Monitoring** - Set budget alerts

---

## 7. Next Steps for Prompt C (Deploy Script Generation)

### 7.1 Tasks for `scripts/deploy_rag_demo.sh` (or `scripts/deploy_fiqa_api.sh`)

1. **Create fiqa_api-specific deploy script**
   - Copy `scripts/deploy_cloud_run.sh` as template
   - Update service name: `fiqa-api`
   - Update Dockerfile path: `services/fiqa_api/Dockerfile.cloudrun` (already correct)
   - Add Artifact Registry support (or use `--source`)

2. **Fix Dockerfile.cloudrun healthcheck**
   - Change line 59 from `/health` to `/healthz` or `/health/live`

3. **Add environment variable validation**
   - Check `QDRANT_URL` is set
   - Check `ALLOWED_ORIGINS` is set (warn if missing)
   - Validate format (URLs, etc.)

4. **Add pre-deployment checks**
   - Verify gcloud auth
   - Verify project is set
   - Verify Cloud Run API is enabled (already done)
   - Optionally: test Qdrant connectivity

5. **Add post-deployment verification**
   - Wait for service to be ready
   - Test `/healthz` endpoint
   - Print service URL
   - Print command to update env vars

6. **Support both deployment methods**
   - Option 1: `--source` (build from source, recommended)
   - Option 2: Pre-built image (for CI/CD pipelines)

### 7.2 Script Structure Template

```bash
#!/usr/bin/env bash
# scripts/deploy_fiqa_api.sh - Deploy fiqa-api to GCP Cloud Run

set -euo pipefail

# Configuration
PROJECT_ID="${PROJECT_ID:-$(gcloud config get-value project)}"
SERVICE_NAME="fiqa-api"
REGION="${REGION:-us-west1}"
DEPLOY_METHOD="${DEPLOY_METHOD:-source}"  # 'source' or 'image'

# Validation
# - Check gcloud auth
# - Check PROJECT_ID
# - Check QDRANT_URL env var (if provided)

# Deploy
gcloud run deploy "$SERVICE_NAME" \
  --source . \
  --dockerfile services/fiqa_api/Dockerfile.cloudrun \
  --platform managed \
  --region "$REGION" \
  --allow-unauthenticated \
  --port 8080 \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 2 \
  --timeout 300 \
  --concurrency 80 \
  "${ENV_VARS[@]}"  # From validation/input

# Post-deploy verification
# - Wait for service
# - Test /healthz
# - Print URL and next steps
```

---

## 8. File Paths Summary

### Existing Files (Referenced)
- `services/fiqa_api/Dockerfile.cloudrun` - Cloud Run Dockerfile
- `services/fiqa_api/app_main.py` - FastAPI entrypoint
- `scripts/deploy_cloud_run.sh` - Generic deploy script (needs customization)
- `requirements.txt` - Root-level Python dependencies
- `ui/vercel.json` - Vercel frontend config
- `ui/package.json` - Frontend dependencies

### Missing Files (To Create)
- `scripts/deploy_fiqa_api.sh` - fiqa_api-specific deploy script
- `.env.cloudrun.example` - Environment variable template (optional)

### Files to Update
- `services/fiqa_api/Dockerfile.cloudrun` - Fix healthcheck endpoint (line 59)

---

## 9. Architecture Confirmation

### Target Architecture
- **Backend:** GCP Cloud Run (FastAPI) ✅
- **Frontend:** Vercel (Vite/React) ✅
- **Vector DB:** External Qdrant (to be provisioned) ⚠️
- **Other Services:** Redis, Milvus (optional, not required for basic deployment)

### Deployment Flow
1. Build Docker image from `Dockerfile.cloudrun`
2. Push to Artifact Registry (or use `--source`)
3. Deploy to Cloud Run with env vars
4. Configure CORS for Vercel frontend
5. Test health endpoints
6. Update Vercel `VITE_API_BASE_URL` to point to Cloud Run URL

---

## 10. Risk Assessment

### Low Risk ✅
- Dockerfile exists and is well-structured
- FastAPI app is Cloud Run compatible (port 8080, stateless)
- Health endpoints are implemented
- gcloud is configured and authenticated

### Medium Risk ⚠️
- External Qdrant dependency (must provision separately)
- Environment variables need careful configuration
- CORS must be configured correctly for Vercel

### High Risk ❌
- None identified (deployment is straightforward)

---

## Summary

**Status:** ✅ Ready for deployment with minor fixes

**Critical Actions:**
1. Fix Dockerfile.cloudrun healthcheck endpoint
2. Create fiqa_api-specific deploy script
3. Provision external Qdrant instance
4. Set environment variables (QDRANT_URL, ALLOWED_ORIGINS)

**Estimated Time to Deploy:** 30-60 minutes (including Qdrant setup)

---

**DEPLOY AUDIT READY. NEXT: generate scripts/deploy_rag_demo.sh (Prompt C).**

---

## 11. How to Deploy in One Command

### Quick Start

1. **Set required environment variable:**
   ```bash
   export QDRANT_URL=https://your-qdrant-instance.com:6333
   ```

2. **Run the deploy script:**
   ```bash
   bash scripts/deploy_rag_demo.sh
   ```

3. **Test the deployment:**
   ```bash
   curl <SERVICE_URL>/healthz
   ```

### Detailed Steps

#### Prerequisites
- gcloud CLI installed and authenticated
- GCP project: `optimal-disk-472305-e2` (or set `PROJECT_ID` env var)
- External Qdrant instance URL (required)

#### Environment Variables

**Required:**
- `QDRANT_URL` - External Qdrant instance URL (e.g., `https://your-cluster.qdrant.io:6333`)

**Optional:**
- `QDRANT_API_KEY` - Qdrant authentication key (if required)
- `QDRANT_COLLECTION` - Collection name (default: `fiqa_10k_v1`)
- `PROJECT_ID` - Override default project
- `REGION` - Override default region (default: `us-west1`)

#### Using Environment File

1. Copy the example file:
   ```bash
   cp configs/demo.env.example .env.cloudrun
   ```

2. Edit `.env.cloudrun` with your values:
   ```bash
   # Required
   QDRANT_URL=https://your-qdrant-instance.com:6333
   
   # Optional
   QDRANT_COLLECTION=fiqa_10k_v1
   ```

3. Source and deploy:
   ```bash
   source .env.cloudrun
   bash scripts/deploy_rag_demo.sh
   ```

#### What the Script Does

1. ✅ Validates gcloud authentication and project
2. ✅ Checks required environment variables (fails fast if missing)
3. ✅ Builds Docker image using Cloud Build
4. ✅ Deploys to Cloud Run with cost-safe defaults:
   - Min instances: 0 (scales to zero)
   - Max instances: 2 (cost control)
   - CPU: 1, Memory: 512Mi
   - Timeout: 60s, Concurrency: 80
5. ✅ Runs health checks (`/healthz`, `/readyz`)
6. ✅ Prints service URL and example curl commands

#### Post-Deployment

**Update environment variables:**
```bash
gcloud run services update fiqa-api \
  --region us-west1 \
  --update-env-vars "ALLOWED_ORIGINS=https://your-frontend.vercel.app"
```

**View logs:**
```bash
gcloud run services logs read fiqa-api --region us-west1
```

**Test query API:**
```bash
curl -X POST https://fiqa-api-xxx.run.app/api/query \
  -H 'Content-Type: application/json' \
  -d '{"question": "What is an ETF?", "top_k": 5, "rerank": false}'
```

### Troubleshooting

**Health check fails:**
- Service may still be starting (wait 30-60 seconds)
- Check logs: `gcloud run services logs read fiqa-api --region us-west1`
- Verify Qdrant connectivity: ensure `QDRANT_URL` is reachable from Cloud Run

**Deployment fails:**
- Verify gcloud authentication: `gcloud auth list`
- Verify project: `gcloud config get-value project`
- Check Cloud Run API is enabled: `gcloud services list --enabled | grep run`

**Qdrant connection issues:**
- Cloud Run cannot reach `localhost` - use external URL
- For local Qdrant, use port forwarding or deploy Qdrant to Cloud Run separately
- Verify Qdrant URL is accessible from internet (or use VPC connector for private networks)

---

**PROMPT C COMPLETE: One-command Cloud Run deployment is ready.**

---

## HR Demo Operator Checklist

**Purpose:** Quick validation steps for HR-facing online demo deployment.

### Pre-Deployment

1. **Backend (Cloud Run):**
   ```bash
   # Set required env vars
   export QDRANT_URL=https://your-qdrant-instance.com:6333
   export QDRANT_API_KEY=your-api-key  # If using Qdrant Cloud
   export QDRANT_COLLECTION=fiqa_10k_v1
   
   # Deploy
   bash scripts/deploy_rag_demo.sh
   ```

2. **Verify Backend Endpoints:**
   ```bash
   CLOUD_RUN_URL="https://fiqa-api-g7zatxrycq-uw.a.run.app"
   
   # All should return 200
   curl -i $CLOUD_RUN_URL/healthz
   curl -i $CLOUD_RUN_URL/readyz
   curl -i $CLOUD_RUN_URL/api/metrics/demo-summary
   curl -i -X POST $CLOUD_RUN_URL/api/query \
     -H 'Content-Type: application/json' \
     -d '{"question":"test","top_k":5}'
   ```

### Frontend (Vercel)

1. **Set Environment Variable:**
   ```bash
   vercel env add VITE_API_BASE_URL production
   # Paste: https://fiqa-api-g7zatxrycq-uw.a.run.app
   ```

2. **Redeploy:**
   ```bash
   vercel --prod
   ```

3. **Verify in Browser:**
   - Open deployed frontend URL
   - Open DevTools (F12) → Console
   - Navigate to MetricsHub page
   - Verify no CORS errors
   - Test a query in search playground
   - Check MetricsHub demo mode loads

### Final E2E Check

Run the automated check:
```bash
bash scripts/demo_e2e_check.sh
```

Expected output:
- ✅ Cloud Run /healthz: 200
- ✅ Cloud Run /readyz: 200
- ✅ Cloud Run /api/query: 200 (or 503 with warmup, retry)
- ✅ Cloud Run /api/metrics/demo-summary: 200 (never 404)

### Troubleshooting

**/healthz returns 404:**
- Verify endpoint exists in `services/fiqa_api/app_main.py`
- Check Cloud Run logs: `gcloud run services logs read fiqa-api --region us-west1`

**/api/metrics/demo-summary returns 404:**
- Should never happen after fix - endpoint returns safe defaults
- Check logs for file read errors

**CORS errors in browser:**
- Verify `VITE_API_BASE_URL` is set in Vercel
- Verify frontend was redeployed after setting env var
- Check Cloud Run CORS config (should allow all origins for demo)

**Query endpoint returns 503:**
- Normal during cold start (embedding_warming)
- Wait 10-30 seconds and retry
- Service will be ready after warmup

---
