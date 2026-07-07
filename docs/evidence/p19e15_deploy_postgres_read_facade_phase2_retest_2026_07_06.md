# P19E-1.5 Deploy — Postgres Read Facade Hardening + Phase 2 Retest Prep

**Date:** 2026-07-06  
**Branch:** `sprint/p16-trust-layer`  
**Verdict:** **DEPLOY PASS** · **QA gate PASS** · **Andy Phase 2 phone retest PENDING**

---

## Deployed commits (pushed)

| Commit | Message |
|--------|---------|
| `9cb7e5f` | fix: route Phase 2 text via Postgres case read facade |
| `e7a64d4` | docs: add Phase 2 routing bug diagram and live debug evidence |
| `0a2ff1f` | fix: harden production case reads through Postgres facade |
| `b104163` | docs: document production case read path hardening |

Pushed: `git push origin sprint/p16-trust-layer` (`9f7e504..b104163`)

---

## Backend deploy

| Field | Value |
|-------|-------|
| Script | `bash scripts/deploy_paid_pilot.sh` |
| Project | `optimal-disk-472305-e2` |
| Service | `fiqa-api` |
| Region | `us-west1` |
| **Revision (prior)** | `fiqa-api-00161-8fs` |
| **Revision (this deploy)** | **`fiqa-api-00162-qhp`** |
| URL | `https://fiqa-api-g7zatxrycq-uw.a.run.app` |
| GIT_SHA | `b104163cb` |
| `/health/live` | 200 |
| `/readyz` | 200 (`intake_core_readiness: true`) |
| `WECOM_SLICE_SEND_REPLY` | `1` |
| `H5_TASK_TOKEN_SECRET` | Secret Manager `fiqa-h5-task-token-secret` — unchanged |
| DB secret | `fiqa-service-record-database-url-cloudsql-private` — unchanged |
| Cloud SQL | `caseiq` @ `10.73.0.3` — unchanged |
| VPC / NAT / WeCom callback | unchanged |

---

## Read path hardening (live)

Production WeCom modules now hydrate cases via `get_case_for_read` / `list_all_cases_for_read` (Postgres-first). Zero direct `get_case_by_id` call sites in `services/fiqa_api/wecom/*`.

**Fixes live bug:** Postgres binding found `case_id` but JSON-only `get_case_by_id` returned `None` → `stale_draft_binding_cleared` → greeting menu → Phase 2 skipped.

---

## Frontend deploy

| Field | Value |
|-------|-------|
| **Action** | **Skipped** — P19E-1.5 is backend read-path hardening only |
| **Alias** | `https://ui-smoky-beta.vercel.app` (unchanged) |
| Rationale | No `ui/` changes in `0a2ff1f` / `b104163` |

---

## Post-deploy QA gate

`bash scripts/check_chen_kui_demo_environment.sh --cloud-api` → **PASS** (revision `fiqa-api-00162-qhp`)

---

## Andy phone retest — P19E-1 Phase 2 text

### Path A — existing Phase 1 complete case

If Andy already has an add_car case with H5 photos complete and End Card (S1) received, send **exactly**:

```
7月10号提车，zip. 92705。电话2031234567
```

**Expected:**

- No generic greeting menu
- **Stage Complete S2** in WeChat:
  - `【第 2 阶段完成 ✅ · 文字信息】`
  - `下一步 · 第 3 步：陈总人工确认`
- Workbench / API case shows:
  - `collected_fields`: `delivery_date`, `zip` (`92705`), `phone` (`2031234567`)
  - `guided_workflow_state` = `ready_for_broker_review`
  - `add_vehicle_phase` = `phase_3_broker_review`

### Path B — no active Phase 1 complete case

Full flow:

1. Send `重新加车`
2. H5: upload VIN / registration / insurance (or skip insurance)
3. Return WeChat → receive **Stage Complete S1** (End Card)
4. Send: `7月10号提车，zip. 92705。电话2031234567`
5. Expect **S2** (not greeting menu)

Reply: **`P19E-1.5 Phase2 done`** with S1/S2 screenshots or text snippet (no sensitive IDs).

---

## Logs to check after Andy retest

```bash
gcloud run services logs read fiqa-api \
  --region us-west1 \
  --project optimal-disk-472305-e2 \
  --limit 1000
```

Look for:

- `wecom_phase2_text_ingest_v1` / `phase2_text_collection_v1`
- extracted `delivery_date` / `zip` / `phone`
- `stage_complete_s2_sent` / `phase2_complete_s2_sent`
- **No** `stale_draft_binding_cleared_v1` for the Phase 2 message
- **No** generic greeting route for Phase 2 text

---

## Andy retest result

| Item | Status |
|------|--------|
| Phase 2 text message | **PENDING** |
| S2 card received | **PENDING** |
| Workbench field state | **PENDING** |

---

## Guardrails

| Item | Status |
|------|--------|
| OCR / LLM / vision extraction | ❌ |
| Schema migration | ❌ |
| Cloud callback / VPC / NAT / Secret change | ❌ |
| Neon as QA truth | ❌ |
| Full external_userid / tokens in this doc | ❌ |

---

## Known limitations

- Phase 2 depends on Postgres-hydrated case with completed H5 photo flow (`h5_photo_flow_is_complete`).
- Restart (`重新加车`) creates a new case — use Path B if prior case is stale.
- Workbench pagination may hide demo rows; QA gate merges `chen_kui_p18` from Cloud SQL.

---

## GO / HOLD

| Gate | Verdict |
|------|---------|
| Push + backend deploy + QA | **GO** |
| Andy phone Phase 2 retest | **GO** — ready on `fiqa-api-00162-qhp` |

**STOP** — awaiting Andy phone retest.
