# Deployment Secrets Management

## Overview

All sensitive information for Cloud Run deployment is managed through `.env.cloudrun`, which is **never committed to git**.

## Quick Start

### 1. Create `.env.cloudrun`

```bash
cp configs/demo.env.example .env.cloudrun
```

### 2. Fill in Real Values

Edit `.env.cloudrun` with your actual credentials:

```bash
# Required: Qdrant Connection
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_API_KEY=your-api-key
QDRANT_COLLECTION=auto_insurance_v1

# Optional: GCP Overrides
PROJECT_ID=your-project-id
REGION=us-west1
```

### 3. Deploy

The deployment script automatically loads `.env.cloudrun`:

```bash
bash scripts/deploy_rag_demo.sh
```

## File Structure

```
project-root/
├── configs/
│   └── demo.env.example          # Template (committed, no secrets)
├── .env.cloudrun                  # Your secrets (git-ignored)
├── .env                           # Local Python scripts (git-ignored)
└── .gitignore                     # Contains .env.cloudrun
```

## Security

- ✅ `.env.cloudrun` is in `.gitignore` (never committed)
- ✅ `configs/demo.env.example` is a template only (no real values)
- ✅ Deployment script validates `.env.cloudrun` exists before running
- ✅ Dockerfiles do NOT copy `.env.cloudrun` into images
- ✅ Secrets passed to Cloud Run via environment variables

## Verification

### Check Environment Variables

```bash
# Verify .env.cloudrun is loaded correctly
python scripts/check_qdrant_env.py
```

### Test Deployment Script

```bash
# Should fail if .env.cloudrun is missing
bash scripts/deploy_rag_demo.sh
```

## Troubleshooting

### Error: "Missing .env.cloudrun"

**Solution**:
```bash
cp configs/demo.env.example .env.cloudrun
# Edit .env.cloudrun with your values
```

### Error: "QDRANT_URL is required for full-stack deploy"

**Intake SaaS (paid pilot):** Qdrant is optional. Use `bash scripts/deploy_paid_pilot.sh` (sets `UNIFIED_INTAKE_INTAKE_CORE_READINESS=1`) or export `SKIP_QDRANT_DEPLOY_PREFLIGHT=1`.

**RAG / notice retrieval:** Ensure `.env.cloudrun` contains `QDRANT_URL=...` and is properly formatted (no spaces around `=`).

### Secrets Not Loading

**Check**:
1. `.env.cloudrun` exists in project root
2. File is readable: `cat .env.cloudrun`
3. Variables are set: `QDRANT_URL=...` (not `export QDRANT_URL=...`)
4. No syntax errors in file

## Best Practices

1. **Never commit `.env.cloudrun`** - Already in `.gitignore`
2. **Use `configs/demo.env.example` as reference** - Shows all available variables
3. **Rotate secrets regularly** - Update `.env.cloudrun` when credentials change
4. **Use different `.env.cloudrun` per environment** - Dev/staging/prod
5. **Verify before deploying** - Run `python scripts/check_qdrant_env.py`

## Migration from Old Method

If you were previously using `export` commands:

**Old way**:
```bash
export QDRANT_URL=...
export QDRANT_API_KEY=...
bash scripts/deploy_rag_demo.sh
```

**New way**:
```bash
# Create .env.cloudrun once
cp configs/demo.env.example .env.cloudrun
# Edit .env.cloudrun with values
# Run deployment (automatically loads .env.cloudrun)
bash scripts/deploy_rag_demo.sh
```
