# Qdrant API Key Rotation Note

**Date**: 2026-03-11  
**Reason**: Credentials were previously exposed in tracked files (reports, docs).

## Action Required

The Qdrant Cloud API key that was used in this project may have been exposed in:
- `results/auto_insurance/CLOUD_UPSERT_REPORT.md` (redacted 2026-03-11)
- `docs/archive/QDRANT_CONFIG_DISCOVERY_REPORT.md` (redacted 2026-03-11)

**Recommendation**: Rotate the Qdrant Cloud API key.

## Steps

1. Log in to [Qdrant Cloud](https://cloud.qdrant.io/)
2. Open your cluster → API Keys
3. Revoke the old key (if still active)
4. Generate a new API key
5. Update `.env.cloudrun` with the new `QDRANT_API_KEY`
6. Update Cloud Run secret (if already deployed) with the new value
7. Re-deploy or restart the backend to pick up the new key

## After Rotation

- Local: `source .env.cloudrun` and restart `run_demo_local.sh`
- Cloud Run: Update the secret in GCP Secret Manager / Cloud Run env, then redeploy
