# P19H-3a — Claim Case Visibility in Workbench

**Date:** 2026-07-09  
**Branch:** `sprint/p16-trust-layer`  
**Verdict:** **LOCAL PASS** · **REGRESSION PASS** · **QA GATE PASS** · **DEPLOYED** · **WORKBENCH SMOKE PASS**

---

## 1. Goal

Make guided Claim cases (`service_lane=claim`) visible on Workbench Document Intake after P19H-2' basics + C1, without OCR, H5 photos, or full Claim drawer.

---

## 2. Root cause — why Claim was not visible

**Verified root cause (frontend filter):**

`DocumentIntakeInboxPage.tsx` function `isP16DocumentCase()` allowed:

- `add_car`, `policy_review`, `claim_lite`, `coverage_risk`

but **not** `claim` (`SERVICE_LANE_CLAIM` from P19H-2').

The page loads `GET /api/inbox/cases` then filters client-side with `isWorkbenchQueueCase()` → `isP16DocumentCase()`. Production Claim cases from WeCom guided basics use `service_lane=claim`, so they were returned by the API but **dropped before render**.

**Backend was not filtering Claim out:** `list_recent_cases_for_read` returns all persisted cases; no `service_lane=add_car` server filter on the list endpoint.

**Example production case (not mutated):** `case_b8d15b3ca59a` — would appear after UI deploy once `claim` lane is included in the queue filter.

---

## 3. Backend changes

| File | Change |
|------|--------|
| `services/fiqa_api/inbox_triage/claim_workbench_display.py` | **NEW** — Claim workbench enrichment: `claim_summary`, `display_title`, `display_status`, `workflow_phase`, `workbench_visible` |
| `services/fiqa_api/inbox_triage/workbench_enrichment.py` | Call `enrich_claim_for_workbench()`; mark `workbench_lane_kind=explicit` for `claim` |

**API behavior (`GET /api/inbox/cases`):**

- Add Vehicle cases unchanged.
- `service_lane=claim` cases enriched with:
  - `workflow_id`: `claim_simplified`
  - `workflow_phase`: derived phase (e.g. `accident_basics_complete`)
  - `display_title`: `Claim · 理赔资料`
  - `display_status`: broker-safe intake copy (no filing language)
  - `claim_summary`: `{ accident_datetime, accident_location, accident_description }` from `known_facts`
  - `workbench_visible`: true when phase ∈ visible set (includes `accident_basics_complete`)

Visible phases: `accident_basics_complete`, `claim_summary_ready`, `intake_ready_for_broker`, `broker_review`, `manual_handle`.

**No schema migration.**

---

## 4. Frontend changes

| File | Change |
|------|--------|
| `ui/src/pages/DocumentIntakeInboxPage.tsx` | Include `claim` in queue filter; Claim badge/label; summary from accident basics; minimal drawer section |
| `ui/src/features/intake/utils/claimWorkbenchDisplay.ts` | **NEW** — pure display helpers |
| `ui/src/api/inboxTriage.ts` | Optional Claim workbench field types |

**List/card:**

- Lane badge: **Claim** (volcano tag)
- Summary: time · location · description
- Status column: `BROKER_REVIEW`

**Drawer (minimal):**

- Card: Claim · Accident Basics
- Fields: Time, Location, Description
- Status line from `display_status`
- Safety note: *This is intake only. Broker must confirm before any filing.*

Add Vehicle / Claim Lite / Policy Review UI unchanged.

---

## 5. Claim display fields

| Field | Source |
|-------|--------|
| `service_lane` | `claim` |
| `workflow_phase` | `accident_basics_complete` (after C1) |
| `display_title` | Claim · 理赔资料 |
| `display_status` | Claim Step 1 complete · Accident basics received |
| `claim_summary.accident_datetime` | `known_facts.accident_datetime` |
| `claim_summary.accident_location` | `known_facts.accident_location` |
| `claim_summary.accident_description` | `known_facts.accident_description` |

---

## 6. Safety copy / no claim filing language

- `display_status` uses intake-only wording.
- Forbidden phrases guarded in tests: `claim filed`, `liability determined`, `coverage confirmed`, `正式报案`.
- Drawer safety note explicitly states broker must confirm before filing.

---

## 7. Tests

**Backend** (`tests/test_p19h3a_claim_workbench_visibility.py`):

1. Claim `accident_basics_complete` appears in `GET /api/inbox/cases`
2. `service_lane=claim`
3. Accident datetime / location / description in `claim_summary`
4. `display_status` does not imply claim filed
5. Add Vehicle cases unchanged
6. Partial Claim case does not break API

**Frontend** (`ui/src/features/intake/utils/claimWorkbenchDisplay.test.ts`):

1. Claim lane detection
2. Summary fields render from `claim_summary`
3. Add Vehicle not treated as Claim

**Regressions (PASS):**

- `test_p19h2_simplified_claim_wecom_basics.py`
- `test_p19h21_claim_interrupt_lane_switch.py`
- `test_p19j1a_routing_decision_log.py`
- `test_p19j1c_workflow_scenario_simulator.py`

---

## 8. QA gate

```bash
bash scripts/check_chen_kui_demo_environment.sh --cloud-api
```

**Result: PASS** (pre-deploy 2026-07-08) — Cloud Run `fiqa-api-00169-wjc`.  
**Post-deploy: PASS** (2026-07-08) — Cloud Run `fiqa-api-00170-lgk`, alias `ui-smoky-beta`.

Note: QA gate still validates seeded `claim_lite` demo row (王女士); guided `claim` lane verified separately in Workbench smoke below.

---

## Deploy Evidence

| Field | Value |
|-------|-------|
| Branch | `sprint/p16-trust-layer` |
| Deployed commit | `29b57fe` (`29b57fe92`) |
| Backend revision | **`fiqa-api-00170-lgk`** |
| Backend URL | `https://fiqa-api-g7zatxrycq-uw.a.run.app` |
| Backend GIT_SHA | `29b57fe92` (`GET /version`) |
| Deploy script | `bash scripts/deploy_paid_pilot.sh` |
| Deploy time (UTC) | 2026-07-08 ~16:28 UTC |
| Frontend command | `vercel deploy --prod --yes` with `VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1`, `VITE_API_BASE_URL`, `VITE_UNIFIED_INTAKE_INTAKE_API_KEY` |
| Frontend deployment | `https://ui-p3mu44ye9-andys-projects-1f411b73.vercel.app` |
| **Stable alias** | **`https://ui-smoky-beta.vercel.app`** |
| `/health/live` | 200 |
| `/readyz` | 200 (`intake_core_readiness: true`) |
| Frontend build (local) | PASS (~20s) |
| Frontend build (Vercel) | PASS (~35s) |
| Frontend unit test | PASS (`claimWorkbenchDisplay.test.ts`) |
| Backend targeted tests | PASS (P19H-3a + regressions) |
| Scenario CLI | PASS (6/6) |
| Pre-deploy QA gate | PASS |
| Post-deploy QA gate | PASS |
| DB secret | `fiqa-service-record-database-url-cloudsql-private` — unchanged |
| Cloud SQL | `caseiq` @ `10.73.0.3` private VPC — unchanged |
| `WECOM_SLICE_SEND_REPLY` | `1` — unchanged |
| `H5_TASK_TOKEN_SECRET` | configured — unchanged |
| WeCom callback / VPC / NAT | unchanged |
| Schema changed? | **No** |
| OCR? | **No** |
| H5 Claim photos? | **No** |
| Full Claim drawer? | **No** (minimal basics card only) |
| Carrier filing? | **No** |

### Log check (post-deploy)

Revision `fiqa-api-00170-lgk` (~80 lines):

- **No** `claim_workbench_display` / `workbench_enrichment` import errors
- **No** `/api/inbox/cases` failures
- **No** Postgres read facade errors
- Expected optional warnings only: Qdrant unreachable, Redis optional, embedding warmup deferred

---

## Workbench Smoke Evidence

**URL:** https://ui-smoky-beta.vercel.app/workbench/document-intake

| Check | Result |
|-------|--------|
| Page loads | **YES** (HTTP 200) |
| Claim case visible in list | **YES** |
| Known case checked | `case_b8d15b3ca59a` (API + UI) |
| Claim badge (`Claim`) | **YES** |
| `accident_datetime` visible | **YES** — 今天上午10点 |
| `accident_location` visible | **YES** — Irvine Blvd 和 Culver |
| `accident_description` visible | **YES** — 对方变道刮到我左前门 (full line in list) |
| Drawer minimal Claim card | **YES** — Claim · Accident Basics |
| Safety note visible | **YES** — *This is intake only. Broker must confirm before any filing.* |
| Add Vehicle still visible | **YES** — 陈女士 Add Car READY, 李先生 NEED_INFO, etc. |
| Claim Lite demo unchanged | **YES** — 王女士 Claim Lite |

### Production API smoke (`GET /api/inbox/cases`)

- `claim_lane=1` in first page (25 cases)
- `case_b8d15b3ca59a`: `service_lane=claim`, `workflow_phase=accident_basics_complete`, `workbench_visible=true`
- `display_status`: *Claim Step 1 complete · Accident basics received*
- No claim-filed language in API response

### Deployed bundle check

- Vercel asset `index-DjqlyphZ.js` contains `Claim Step 1 complete`, `Accident Basics`

---

## 9. Constraints honored

| Constraint | Status |
|------------|--------|
| No OCR | ✅ |
| No H5 Claim photos | ✅ |
| No full Claim drawer | ✅ (minimal basics card only) |
| No schema migration | ✅ |
| No deploy (implementation sprint) | ✅ (deploy done in follow-up) |
| No WeCom callback change | ✅ |
| Add Vehicle Workbench unchanged | ✅ |

---

## 10. Known limitations

- Document Intake list filter is still client-side; relies on `service_lane=claim` (not phase filter on frontend — all non-archived `claim` lane cases show).
- No Claim photo / Evidence Pack UI.
- No carrier filing actions.
- `case_b8d15b3ca59a` verified on production API + Workbench UI post-deploy.
- Customer name empty on production Claim case (WeCom default label 企业微信客户) — cosmetic only.

---

## 11. Next recommended step

1. **P19H-3b Claim Evidence Pack** (H5 photos) — separate sprint
2. Optional Andy phone retest: fresh Claim flow → confirm Workbench row after C1

---

## 12. GO / HOLD

| Gate | Verdict |
|------|---------|
| Code + tests | **GO** |
| Deploy | **GO** |
| Workbench smoke | **GO** |

**STOP** — P19H-3a deployed and Workbench Claim visibility verified.
