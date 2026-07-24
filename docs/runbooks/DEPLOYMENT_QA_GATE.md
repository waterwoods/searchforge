# Deployment QA Gate v2

**Purpose:** Prevent deployment/configuration mistakes **before** Founder QA.  
**Not a product feature.** Code can be correct while deploy config is wrong.  
**One command:** `bash scripts/run_deployment_qa_gate.sh`

**Related (do not duplicate):**

| Script / doc | Role |
|--------------|------|
| `scripts/run_deployment_qa_gate.sh` | **This gate** — revision + CORS + Office Queue + Smart Claim Start |
| `scripts/unified_intake_release_gate.sh` | Broader API + triage smoke + CORS (product release slice) |
| `scripts/deploy_cloud_qa.sh` | Cloud QA deploy entry (isolation + safety before gcloud) |
| `scripts/guardrail_cloudrun_runtime.sh` | Read-only memory/concurrency/flag drift |
| `docs/runbooks/CLOUD_QA_RESOURCE_NAMES.md` | Frozen QA names + Founder bookmark |
| `docs/FOUNDER_QA_PLAYBOOK.md` | Founder product QA after this gate PASSes |

---

## Deployment QA Checklist

Run after Cloud QA backend deploy and/or QA Vercel Preview deploy, **before** asking Founder to test.

| # | Check | Pass means |
|---|--------|------------|
| 1 | Cloud Run serving **LATEST** Ready revision at **100%** traffic | Not stuck on old revision |
| 2 | Current Vercel origin allowed by **CORS** | OPTIONS `/api/inbox/cases` ACA = exact origin |
| 3 | **Office Queue** loads | GET `/api/inbox/cases` 200 + browser ACA + usable JSON |
| 4 | **Smart Claim Start** opens | Workbench shell 200; Start Claim CORS OK; `POST /api/h5/customer/start-claim` live (not 404; empty body must not create a case) |

If any check fails → **STOP**. Do not continue to Founder QA.

Manual mirror (same four questions):

- [ ] `gcloud run services describe fiqa-api-qa …` traffic revision == `latestReadyRevisionName` @ 100%
- [ ] Browser DevTools: no CORS error from the exact Vercel host you will open
- [ ] `/workbench/document-intake` list loads (not empty from failed fetch)
- [ ] Start Claim path (`/api/h5/customer/start-claim`) responds on the API you think you deployed (not 404)

---

## One command

```bash
# Cloud QA defaults (Founder bookmark origin + fiqa-api-qa)
bash scripts/run_deployment_qa_gate.sh
```

Overrides:

```bash
CLOUD_RUN_URL='https://fiqa-api-qa-g7zatxrycq-uw.a.run.app' \
FRONTEND_ORIGIN='https://ui-waterwoods-andys-projects-1f411b73.vercel.app' \
SERVICE_NAME=fiqa-api-qa \
REGION=us-west1 \
bash scripts/run_deployment_qa_gate.sh
```

**Defaults** match Founder QA SSOT (`CLOUD_QA_RESOURCE_NAMES.md`).  
Always pass the **exact** origin of the tab you will open (alias or preview hash).

---

## Failure output

On failure the script prints only:

```text
FAILED
Check:      …
Reason:     …
How to Fix: …
```

Then exits `1`. No further checks run after a hard fail path completes (each check fails closed).

### Common fixes

| Symptom | Fix |
|---------|-----|
| Traffic on old revision | `gcloud run services update-traffic fiqa-api-qa --region us-west1 --to-latest` |
| CORS ACA mismatch | Add exact origin to `ALLOWED_ORIGINS` in `.env.cloudrun.qa` → `bash scripts/deploy_cloud_qa.sh` → `--to-latest` |
| Office Queue non-200 | Cloud Run logs + DB secret / intake flags on **fiqa-api-qa** |
| start-claim 404 | Latest code not on serving revision — redeploy Cloud QA + promote traffic |
| Workbench shell non-200 | Redeploy QA Vercel Preview; confirm bookmark host |

---

## How future deployments should use this Gate

```text
1. Deploy Cloud QA backend
     bash scripts/deploy_cloud_qa.sh

2. Deploy / confirm QA Vercel Preview (if UI changed)
     cd ui && vercel --yes
     # Note the exact origin you will open

3. Run Deployment QA Gate (required)
     FRONTEND_ORIGIN='https://<exact-origin>' bash scripts/run_deployment_qa_gate.sh
     → must print READY FOR FOUNDER QA

4. Only then Founder / Golden product QA
     docs/FOUNDER_QA_PLAYBOOK.md
     docs/product/p20_founder_qa_checklist.md
```

**Rules:**

- Gate PASS ≠ product Capability Done. It only means deploy/config is safe to test.
- Do **not** skip the gate after “deploy succeeded” — Cloud Run can leave traffic on an old revision.
- Do **not** use Production (`fiqa-api` / `ui-smoky-beta`) for Golden / Founder QA.
- Prefer this gate over ad-hoc curls; use `unified_intake_release_gate.sh` when you also need triage API smoke.

---

## Success criteria

| Result | Meaning |
|--------|---------|
| `READY FOR FOUNDER QA` + exit 0 | Deployment config safe for Founder QA |
| `FAILED` + exit 1 | Fix Reason / How to Fix; re-run gate; do not hand Founder a link |
