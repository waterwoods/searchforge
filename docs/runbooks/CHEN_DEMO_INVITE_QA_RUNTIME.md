# Chen Demo Invite — QA Cloud Run Runtime (process-local store)

**Status:** required for Chen known-customer Demo Invite day  
**Scope:** `fiqa-api-qa` only  
**Do not change:** Production `fiqa-api`

## Why

Demo Invite tokens and session overlays are **process-local in-memory**.
Multiple Cloud Run instances (or scale-to-zero cold starts mid-demo) can drop
or split invite state. For the demo window, pin QA to a single warm instance.

## Required demo configuration (`fiqa-api-qa`)

| Setting | Demo value | Purpose |
|---------|------------|---------|
| min instances | **1** | Avoid cold-start store wipe mid-demo |
| max instances | **1** | Keep invite/overlay on one process |

## Recorded baseline (pre-demo, 2026-07-29)

Service: `fiqa-api-qa` · Region: `us-west1` · Project: `optimal-disk-472305-e2`

| Setting | Baseline |
|---------|----------|
| max instances | **2** (`autoscaling.knative.dev/maxScale=2`) |
| min instances | **unset / 0** (no `autoscaling.knative.dev/minScale`) |
| traffic revision | `fiqa-api-qa-00021-bbh` (at audit time; confirm before change) |

Production `fiqa-api` must not be updated.

## Apply (QA only — Founder-authorized)

```bash
gcloud run services update fiqa-api-qa \
  --region=us-west1 \
  --project=optimal-disk-472305-e2 \
  --min-instances=1 \
  --max-instances=1
```

Verify:

```bash
gcloud run services describe fiqa-api-qa \
  --region=us-west1 \
  --project=optimal-disk-472305-e2 \
  --format='yaml(spec.template.metadata.annotations)'
```

Expect annotations including:
- `autoscaling.knative.dev/minScale: '1'`
- `autoscaling.knative.dev/maxScale: '1'`

## Restore after demo

```bash
gcloud run services update fiqa-api-qa \
  --region=us-west1 \
  --project=optimal-disk-472305-e2 \
  --min-instances=0 \
  --max-instances=2
```

## Safety

- Safe to apply to **QA** for a short demo window (single concurrent demo user).
- Not safe as a permanent QA posture if parallel harness / multi-user load is needed.
- **Never** apply these limits to Production `fiqa-api`.
- Env flags for demo (separate from scaling): `CHEN_DEMO_INVITE_ENABLED=1`.
  Do **not** enable `P4_CUSTOMER_LOOKUP_MOCK` globally for ordinary QA traffic;
  redeemed Demo Invite overlays load fixtures without that flag.
