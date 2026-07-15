# P20 Slice 1 QA Deployment Readiness Verification

**Date:** 2026-07-15  
**Scope:** Verify-only — no deploy, commit, push, or production-data mutation  
**Subject:** Repaired Slice 1 Request More (`StructuredRequestMorePanel` on `/workbench/document-intake` → `BrokerCaseDetail`)

---

## Verdict

**BLOCKED** for a safe non-production QA deployment of the repaired Request More flow.

UI local production build and focused tests pass. Live shared pilot backend + Cloud SQL are missing Slice 1 code and companion tables. Existing QA claims also need a legal `broker_review` phase for create.

---

## Required checklist results

| # | Item | Result |
|---|------|--------|
| 1 | Verdict | **BLOCKED** |
| 2 | UI production build | **PASS** (`cd ui && npm run build`) |
| 3 | Focused tests | **PASS** |
| 4 | New TypeScript errors caused by this diff | **NO** (panel / client / DocumentIntake mount introduce none; `inboxTriage.requestMore.test.ts` has TS5097 `.ts` import extension, same pattern as other repo `*.test.ts` files; broad `tsc` still fails historically) |
| 5 | QA backend endpoints verified | **YES** — live OpenAPI has **no** `/request-more` |
| 6 | QA migration status verified | **YES** — all five Slice 1 tables **absent** |
| 7 | Feature flags/env verified | **YES** — `P20_SLICE1_REQUEST_MORE` **not** set on Cloud Run |
| 8 | Single QA claim plan safe and reversible | **YES** (documented only; not executed) |
| 9 | Exact blockers | See below |
| 10 | Ordered deployment runbook | See below |
| 11 | Files changed | This verification doc only |
| 12 | Production code changed | **NO** |
| 13 | Commit | **NO** |
| 14 | Deploy | **NO** |

---

## 1. Non-production deployment topology (verified)

There is **no separate QA Cloud Run service**. Founder/QA surfaces share one pilot stack. Do not treat unrelated Vercel preview aliases as the QA target.

| Layer | Exact target | Notes |
|-------|----------------|-------|
| **Workbench UI** | Vercel project hosting **`https://ui-smoky-beta.vercel.app`** | Build: `ui/vercel.json` → `NODE_OPTIONS=--max-old-space-size=6144 npm run build`, output `dist`. Live bundle asset `index-DyQovF8y.js` does **not** contain Request More strings. |
| **UI → API** | Live UI embeds `https://fiqa-api-1013093472160.us-west1.run.app` | Same service as short URL below. |
| **Backend** | Cloud Run service **`fiqa-api`**, region **`us-west1`**, project **`1013093472160` / `optimal-disk-472305-e2`** | URLs: `https://fiqa-api-g7zatxrycq-uw.a.run.app` and `https://fiqa-api-1013093472160.us-west1.run.app` (identical revision). |
| **Revision** | **`fiqa-api-00203-mfm`** | `GIT_SHA` / `SOURCE_REV` = **`f208a3006`** (pre–Slice 1; local HEAD `0ea4b72` + uncommitted Slice 1). |
| **Env label** | Cloud Run `ENV=prod` | Label is prod; this is still the founder/QA shared pilot backend, not a second stack. |
| **Database** | GCP Cloud SQL instance **`caseiq-pilot-pg`**, database **`caseiq`** | Bound via secret **`fiqa-service-record-database-url-cloudsql-private`**. Persistence: `STRICT_PG_ONLY`. |
| **Mini Program QA API** | `apiProfile: "qa"` → `https://fiqa-api-g7zatxrycq-uw.a.run.app` | From `miniapp/utils/config.ts` `QA_API_BASE_URL`. |

### Required flags / env for Slice 1

| Variable / capability | Required for QA? | Live status |
|----------------------|------------------|-------------|
| `SERVICE_RECORD_DATABASE_URL` (Cloud SQL secret) | Yes | Present |
| `UNIFIED_INTAKE_*` PG-primary + intake API key | Yes (existing) | Present |
| `P20_SLICE1_REQUEST_MORE` | Optional if case-level capability is set | **Absent** (prefer case-level for reversible QA) |
| Case `extra.slice1_capability_version = 1` | Yes for single-claim QA | Not set on any case |
| Companion migration `002_p20_slice1_request_more.sql` | Yes before commands | **Not applied** |
| UI `VITE_API_BASE_URL` | Points at Cloud Run above | Live UI uses `…us-west1.run.app` |

---

## 2. Backend readiness (read-only)

### Migration

File exists locally: `services/fiqa_api/db/schema/migrations/002_p20_slice1_request_more.sql`.

Read-only check against `caseiq` (2026-07-15):

| Table | Present |
|-------|---------|
| `claim_slice1_aggregates` | **NO** |
| `claim_request_groups` | **NO** |
| `claim_request_items` | **NO** |
| `claim_slice1_events` | **NO** |
| `claim_slice1_command_outcomes` | **NO** |

**Migration applied in QA DB: NO.**

### Endpoints

Local route (uncommitted): `POST /api/inbox/cases/{case_id}/request-more` in `services/fiqa_api/routes/inbox_triage.py`.

Live OpenAPI case paths: attachments, broker-done, confirm, customer, follow-up, notes, status, workbench — **no `request-more`**, no `slice1`/`p20` strings.

**QA backend endpoints present: NO** (verified absent).

### Capability / projection contract (local UI vs local backend)

| Contract field | UI (`StructuredRequestMorePanel`) | Backend (`p20_slice1_command_service`) | Match |
|----------------|-----------------------------------|----------------------------------------|-------|
| Capability | `slice1_capability_version` / `p20_slice1_capability_version` ≥ 1 or existing projection | `P20_SLICE1_REQUEST_MORE` **or** capability ≥ 1 | Yes |
| Projection | `slice1_projection` / `p20_slice1_projection` | writes `p20_slice1_projection` + companion tables | Yes |
| Create gate | `broker_next_action.action_type === "create_request"` **or** no open request and `workflow_phase`/`claim_phase` === `broker_review` | Canonical state must be **`broker_reviewing`** (from `claim_phase=broker_review` or derived) | Yes when phase is `broker_review` |
| Mismatch on live QA rows | Most ready claims store `claim_phase=intake_ready_for_broker` with `guided_workflow_state=ready_for_broker_review` | Explicit `intake_ready_for_broker` maps to `broker_review_ready` → create **`illegal_state`** | **Mismatch unless enable SQL also sets `broker_review`** |

---

## 3. UI release readiness

| Check | Result |
|-------|--------|
| Production build (`source scripts/with_node22_path.sh` → `cd ui && npm run build`) | **PASS** (~22s); local `dist` contains Request More strings |
| `npx tsx src/api/inboxTriage.requestMore.test.ts` | **PASS** |
| `npx tsx src/features/intake/components/StructuredRequestMorePanel.test.ts` | **PASS** |
| IDE diagnostics on changed UI files | Clean |
| Scoped `tsc` attribution | No errors in `StructuredRequestMorePanel.tsx`, `inboxTriage.ts`, `config.ts`. `DocumentIntakeInboxPage.tsx` shows pre-existing `SavedCase`/`TriageResult` typing issues also present on HEAD patterns. New test file TS5097 matches other `*.test.ts` files. Broad `tsc` still fails historically. |
| Live Vercel bundle | **Does not** contain repaired UI |

---

## 4. Real BrokerCaseDetail route (code proof)

```text
App.tsx  /workbench/document-intake
  → OfficeReviewShell
  → DocumentIntakeInboxPage
  → Button "Open" → openCase(caseId) → getSavedCase
  → Drawer → BrokerCaseDetail
  → StructuredRequestMorePanel (both full-packet and stub branches)
```

Proven in current working tree:

1. **DocumentIntakeInboxPage opens BrokerCaseDetail** — Drawer renders `<BrokerCaseDetail …>` when `detail` is set (`DocumentIntakeInboxPage.tsx`).
2. **BrokerCaseDetail renders StructuredRequestMorePanel** — mounted under `TopActionBanner` in both render branches.
3. **Eligibility from authoritative Slice 1 projection** — panel reads `slice1_projection` / `p20_slice1_projection`, `broker_next_action`, open request summary; create gated by `slice1CanCreateRequest`.
4. **Projection failures visible and recoverable** — `projectionLoading` / `projectionLoadError` props from drawer detail fetch; error Alert + **Retry** via `refreshCase` → `refreshDrawerCase` / `getSavedCase`.

`BrokerWorkbenchTab` also mounts the same shared panel (non–document-intake path).

---

## 5. Reversible single QA claim enablement plan (DO NOT EXECUTE YET)

### Candidate selection criteria

Prefer **one** row that is:

- `structured_payload.service_lane = 'claim'`
- Not archived (`extra.workbench_archived` is not true)
- Not broker-done / terminal (`claim_broker_done_at` / `broker_done_at` / terminal statuses empty)
- In a legal broker Request More state after enablement: **`claim_phase = broker_review`** (required for backend `broker_reviewing`)
- Prefer `extra.workbench_test = true`
- No open Slice 1 request (after migration: no `claim_request_groups.status = 'open'`)
- Prefer recent, identifiable test claim already used in Workbench

**Recommended candidate (read-only 2026-07-15):** `case_874d750b5d5f`  
- lane `claim`, guided `ready_for_broker_review`, `workbench_test=true`, 11 attachments, not archived/done  
- **Current** structured `claim_phase` = `intake_ready_for_broker` → **must be updated to `broker_review`** as part of enablement or create will be rejected / UI create disabled  

Do **not** set global `P20_SLICE1_REQUEST_MORE=1` for first QA.

### Pre-check SQL (read-only)

```sql
-- Identity + eligibility snapshot for one candidate
SELECT
  sr.record_id,
  srd.structured_payload->>'service_lane' AS service_lane,
  srd.structured_payload->>'claim_phase' AS claim_phase,
  sr.extra->>'guided_workflow_state' AS guided_workflow_state,
  sr.extra->>'workbench_test' AS workbench_test,
  sr.extra->>'workbench_archived' AS workbench_archived,
  sr.extra->>'slice1_capability_version' AS slice1_capability_version,
  COALESCE(sr.extra->>'claim_broker_done_at', sr.extra->>'broker_done_at', '') AS broker_done,
  sr.case_status,
  sr.lifecycle_status,
  sr.updated_at
FROM service_records sr
JOIN structured_record_data srd ON srd.record_id = sr.record_id
WHERE sr.record_id = 'case_874d750b5d5f';

-- After migration only:
SELECT request_id, status, updated_at
FROM claim_request_groups
WHERE case_id = 'case_874d750b5d5f' AND status = 'open';
```

### Enable SQL (single claim — not executed)

```sql
BEGIN;

-- 1) Case-level Slice 1 capability (reversible)
UPDATE service_records
SET extra = jsonb_set(
      COALESCE(extra, '{}'::jsonb),
      '{slice1_capability_version}',
      '1'::jsonb,
      true
    ),
    updated_at = NOW()
WHERE record_id = 'case_874d750b5d5f';

-- 2) Legal broker Request More state (required for create)
UPDATE structured_record_data
SET structured_payload = jsonb_set(
      COALESCE(structured_payload, '{}'::jsonb),
      '{claim_phase}',
      '"broker_review"'::jsonb,
      true
    ),
    updated_at = NOW()
WHERE record_id = 'case_874d750b5d5f';

COMMIT;
```

Capture prior `claim_phase` from pre-check before running (for rollback).

### Verification SQL

```sql
SELECT
  sr.extra->>'slice1_capability_version' AS slice1_capability_version,
  srd.structured_payload->>'claim_phase' AS claim_phase,
  srd.structured_payload->>'service_lane' AS service_lane
FROM service_records sr
JOIN structured_record_data srd ON srd.record_id = sr.record_id
WHERE sr.record_id = 'case_874d750b5d5f';
-- Expect: slice1_capability_version=1, claim_phase=broker_review, service_lane=claim
```

### Rollback SQL

```sql
BEGIN;

UPDATE service_records
SET extra = COALESCE(extra, '{}'::jsonb) - 'slice1_capability_version',
    updated_at = NOW()
WHERE record_id = 'case_874d750b5d5f';

-- Restore prior claim_phase from pre-check (example uses observed prior value)
UPDATE structured_record_data
SET structured_payload = jsonb_set(
      COALESCE(structured_payload, '{}'::jsonb),
      '{claim_phase}',
      '"intake_ready_for_broker"'::jsonb,
      true
    ),
    updated_at = NOW()
WHERE record_id = 'case_874d750b5d5f';

COMMIT;
```

Do **not** DELETE Slice 1 companion rows if a command was accepted; disable capability instead.

---

## 6. Ordered QA deployment runbook

### A. Backend / migration verification or deployment

1. Commit/package Slice 1 backend + migration (currently uncommitted).
2. Apply migration to **caseiq** only after explicit approval:  
   `psql "$SERVICE_RECORD_DATABASE_URL" -v ON_ERROR_STOP=1 -f services/fiqa_api/db/schema/migrations/002_p20_slice1_request_more.sql`
3. Deploy Cloud Run `fiqa-api` with that package (`bash scripts/deploy_paid_pilot.sh` or approved wrapper).  
   Do **not** set `P20_SLICE1_REQUEST_MORE=1` for first QA.
4. Verify: OpenAPI contains `/api/inbox/cases/{case_id}/request-more`; `/health/live` 200; `/readyz` `intake_path_ready: true`; five Slice 1 tables exist.

### B. UI deployment

1. Ensure repaired UI is in the deployable tree (`StructuredRequestMorePanel` + `DocumentIntakeInboxPage` mounts).
2. `source scripts/with_node22_path.sh && cd ui && npm run build`
3. Deploy Vercel production alias for **`ui-smoky-beta.vercel.app`** with `VITE_API_BASE_URL` = Cloud Run URL (no trailing slash).
4. Probe bundle for `Structured Request More` / `Slice 1 enabled`.

### C. Health / API smoke checks

```bash
URL=https://fiqa-api-g7zatxrycq-uw.a.run.app
curl -sf "$URL/health/live"
curl -sf "$URL/readyz" | python3 -m json.tool
# Auth’d GET case (intake key): expect slice1 fields after enablement
# Do not POST request-more until step D + browser smoke intentionally
```

### D. Enable one QA claim

1. Run pre-check SQL; confirm no open request.
2. Run enable SQL for **one** id (default `case_874d750b5d5f`).
3. Run verification SQL.

### E. Browser Workbench smoke

1. Open `https://ui-smoky-beta.vercel.app/workbench/document-intake`
2. Open the enabled claim → drawer shows **Structured Request More**
3. Create VIN request once; confirm progress + no duplicate create
4. Confirm projection error path by forcing refresh if needed

### F. Mini Program DevTools clear-cache full compile

1. `apiProfile: "qa"`; `npm run preview:preflight` from `miniapp/`
2. WeChat DevTools: 清缓存 → 全部清除 → 重新编译 (Gate 3)
3. Open same case task; confirm customer next action for open request

### G. Experience / Preview build

1. Upload Preview/Experience only after F passes
2. Keep prior known-good Mini Program version for rollback

### H. iPhone manual A–G acceptance

Execute `docs/product/p20_slice1_manual_qa_script.md` A–G on device against QA.

### I. Rollback

| Layer | Action |
|-------|--------|
| Claim | Rollback SQL above (capability + prior `claim_phase`) |
| Global flag | Ensure `P20_SLICE1_REQUEST_MORE` stays unset/off |
| UI | Redeploy previous Vercel deployment / revert panel mount |
| Backend | Traffic to previous Cloud Run revision (`fiqa-api-00203-mfm` or last known-good) |
| Migration | Do **not** DROP companion tables if any accepted outcomes exist; rehearsal-only DROP is in migration header |

---

## 9. Exact blockers

1. **Backend not deployed:** live `fiqa-api` revision `f208a3006` / `fiqa-api-00203-mfm` has no Slice 1 routes (OpenAPI verified).
2. **Migration not applied:** all five `claim_slice1_*` / `claim_request_*` tables missing in `caseiq`.
3. **UI not deployed:** `ui-smoky-beta.vercel.app` bundle lacks Request More strings.
4. **Uncommitted Slice 1 package:** backend, migration, shared panel, and mounts are local/uncommitted — Vercel-from-branch cannot ship them until committed/deployed from this tree.
5. **Claim phase gate:** candidate claims use `claim_phase=intake_ready_for_broker`; enablement must also set `broker_review` or create remains illegal / UI create stays closed.
6. **Shared pilot DB:** `caseiq` is the live Cloud Run database (`ENV=prod` label). Treat mutations as pilot-impacting; keep single-claim reversible enablement only.

Non-blockers for this verdict: local UI build PASS; focused tests PASS; no new production TS diagnostics from the panel diff; route wiring correct in working tree.

---

## Files changed (this verification)

- `docs/product/p20_slice1_qa_deployment_readiness_verification.md` (new)

## Production code changed

**NO**

## Commit

**NO**

## Deploy

**NO**
