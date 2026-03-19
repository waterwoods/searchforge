# Qdrant Cloud Migration Guide

This guide explains how to migrate your local Qdrant collection to Qdrant Cloud and configure the RAG demo to use it.

## Overview

The RAG demo supports both local Qdrant instances and Qdrant Cloud. This guide covers:
- Migrating collections from local Qdrant to Qdrant Cloud
- Configuring the backend to use Qdrant Cloud
- Verifying the connection
- Deploying to Cloud Run with Qdrant Cloud

## Prerequisites

- Local Qdrant instance running with a working collection (e.g., `fiqa_10k_v1`)
- Qdrant Cloud account with a cluster created
- Qdrant Cloud cluster URL and API key
- Python 3.7+ with `qdrant-client` installed

## Step 1: Get Qdrant Cloud Credentials

1. Log in to [Qdrant Cloud](https://cloud.qdrant.io/)
2. Create or select a cluster
3. Copy your cluster URL (e.g., `https://your-cluster-id.us-east4-0.gcp.cloud.qdrant.io`)
4. Generate an API key from the cluster dashboard

## Step 2: Migrate Local Collection to Cloud

Use the migration script to copy your local collection to Qdrant Cloud:

```bash
python scripts/migrate_local_qdrant_to_cloud.py \
    --local-url http://localhost:6333 \
    --cloud-url https://your-cluster-id.us-east4-0.gcp.cloud.qdrant.io \
    --cloud-api-key eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9... \
    --collection fiqa_10k_v1
```

### Migration Script Options

- `--local-url`: Local Qdrant URL (default: `http://localhost:6333`)
- `--cloud-url`: Qdrant Cloud cluster URL (required)
- `--cloud-api-key`: Qdrant Cloud API key (required, or set `QDRANT_API_KEY` env var)
- `--collection`: Collection name to migrate (default: `fiqa_10k_v1`)
- `--recreate`: Delete and recreate collection on cloud if it exists
- `--skip-verify`: Skip verification step (not recommended)
- `--batch-size`: Batch size for upserting points (default: 500)

### What the Script Does

1. **Reads all points** from the local collection (with vectors and payloads)
2. **Creates the collection** on Qdrant Cloud with the same configuration
3. **Upserts all points** in batches to the cloud collection
4. **Verifies** the migration by comparing point counts and sampling random points

The script is **idempotent** and safe to re-run. If the collection already exists on cloud, it will skip creation unless `--recreate` is used.

## Step 3: Verify Cloud Connection

After migration, verify the connection:

```bash
export QDRANT_URL=https://your-cluster-id.us-east4-0.gcp.cloud.qdrant.io
export QDRANT_API_KEY=your-api-key
export QDRANT_COLLECTION=fiqa_10k_v1

python scripts/verify_qdrant_cloud.py
```

This will:
- Test the connection to Qdrant Cloud
- List available collections
- Check the specified collection and show point count
- Sample a few points to verify data integrity

## Step 4: Configure Environment Variables

Update your environment configuration:

### For Local Development

Create or update `.env` file:

```bash
QDRANT_URL=https://your-cluster-id.us-east4-0.gcp.cloud.qdrant.io
QDRANT_API_KEY=your-api-key
QDRANT_COLLECTION=fiqa_10k_v1
```

### For Cloud Run Deployment

Update `configs/demo.env.example` or create your own `.env.cloudrun`:

```bash
cp configs/demo.env.example .env.cloudrun
# Edit .env.cloudrun with your Qdrant Cloud credentials
source .env.cloudrun
```

## Step 5: Deploy to Cloud Run

The deployment script automatically validates Qdrant Cloud connections before deploying:

```bash
export QDRANT_URL=https://your-cluster-id.us-east4-0.gcp.cloud.qdrant.io
export QDRANT_API_KEY=your-api-key
export QDRANT_COLLECTION=fiqa_10k_v1

bash scripts/deploy_rag_demo.sh
```

The script will:
1. Validate that `QDRANT_URL` and `QDRANT_API_KEY` are set
2. Test the connection to Qdrant Cloud (if using cloud URL)
3. Build and deploy the Docker image
4. Configure Cloud Run with the environment variables
5. Run health checks

## Backend Configuration

The backend automatically detects whether to use URL-based (cloud) or host/port-based (local) connections:

- **If `QDRANT_URL` is set and contains `http://` or `https://`**: Uses URL-based connection with API key
- **Otherwise**: Falls back to `QDRANT_HOST`/`QDRANT_PORT` for local Qdrant (backward compatible)

The client initialization in `services/fiqa_api/clients.py` handles both modes automatically.

## Troubleshooting

### Connection Errors

If you see connection errors:

1. **Verify credentials**:
   ```bash
   python scripts/verify_qdrant_cloud.py
   ```

2. **Check network connectivity**:
   ```bash
   curl -H "api-key: $QDRANT_API_KEY" "$QDRANT_URL/collections"
   ```

3. **Verify API key permissions**: Ensure your API key has read/write access

### Migration Issues

If migration fails:

1. **Check local collection exists**:
   ```bash
   curl http://localhost:6333/collections
   ```

2. **Verify cloud collection doesn't exist** (or use `--recreate`):
   ```bash
   python scripts/verify_qdrant_cloud.py
   ```

3. **Check point counts match**: The verification step will warn if counts don't match

### Deployment Issues

If Cloud Run deployment fails:

1. **Check validation output**: The deploy script shows validation results
2. **Verify environment variables**: Ensure `QDRANT_URL` and `QDRANT_API_KEY` are set
3. **Check Cloud Run logs**:
   ```bash
   gcloud run services logs read fiqa-api --region us-west1
   ```

## Quick Reference

### Migration Command
```bash
python scripts/migrate_local_qdrant_to_cloud.py \
    --cloud-url $QDRANT_URL \
    --cloud-api-key $QDRANT_API_KEY \
    --collection fiqa_10k_v1
```

### Verification Command
```bash
python scripts/verify_qdrant_cloud.py
```

### Deployment Command
```bash
export QDRANT_URL=https://your-cluster.qdrant.io
export QDRANT_API_KEY=your-key
bash scripts/deploy_rag_demo.sh
```

### Environment Variables
```bash
QDRANT_URL=https://your-cluster.qdrant.io      # Required
QDRANT_API_KEY=your-api-key                   # Required for cloud
QDRANT_COLLECTION=fiqa_10k_v1                 # Optional (default: fiqa_10k_v1)
```

## Backward Compatibility

The implementation maintains full backward compatibility:

- **Local Qdrant**: Still works with `QDRANT_HOST` and `QDRANT_PORT` (default)
- **Cloud Qdrant**: Works with `QDRANT_URL` and `QDRANT_API_KEY`
- **Automatic detection**: Backend detects which mode to use based on `QDRANT_URL`

You can switch between local and cloud by simply changing environment variables - no code changes needed.

## Additional Resources

- [Qdrant Cloud Documentation](https://qdrant.tech/documentation/cloud/)
- [Qdrant Python Client](https://qdrant.github.io/qdrant-client/)
- [Cloud Run Deployment Guide](scripts/deploy_rag_demo.sh)
