# P20 Business Contract MVP — Release Prep Loop #1 Founder QA Handoff

**Date:** 2026-07-16  
**Loop:** Release Preparation Loop #1  
**Objective:** Take Business Contract MVP from local PASS to founder-testable QA RC  
**Verdict (automated):** READY_FOR_FOUNDER_QA  
**Release:** NO — pending manual Founder QA  
**Capability 4 started:** NO

## Git / deploy

| Item | Value |
|---|---|
| Branch | `sprint/p16-trust-layer` |
| Commit | `ef503a21ccc3bc94512eb97730ccb9bb874f8146` |
| Backend revision | `fiqa-api-00218-nhg` |
| Backend GIT_SHA | `ef503a21c` |
| Office preserved | `UNIFIED_INTAKE_CUSTOMER_START_CLAIM_OFFICE_ID=chen-kui` |
| Workbench alias | https://ui-smoky-beta.vercel.app |
| Workbench deploy | https://ui-f1grqj2pp-andys-projects-1f411b73.vercel.app |
| Document Intake | https://ui-smoky-beta.vercel.app/workbench/document-intake |

## Mini Program Preview

| Item | Value |
|---|---|
| AppID | `wxa610932351416622` |
| apiProfile | `qa` |
| API base | `https://fiqa-api-g7zatxrycq-uw.a.run.app` |
| Component gates | PASS |
| Preview preflight | PASS |

### Obtain Preview / Experience QR

1. Open WeChat DevTools → repo `miniapp/`.
2. Confirm AppID `wxa610932351416622`.
3. Confirm `config.local.ts` selects `apiProfile: "qa"`.
4. Run `cd miniapp && npm run preview:preflight` (must PASS).
5. DevTools → **Preview** (or upload **Experience Version**) → scan QR on iPhone.
6. Phone QA is manual — automation did not perform it.

## Automated main-chain smoke

**PASS** (synthetic TEST data on live QA)

| Field | Value |
|---|---|
| Human title | `P20 Business Contract MVP 2026-07-16 22:01 UTC` |
| Created | 2026-07-16 22:01 UTC |
| VIN readback | `1HGCM82633A004352` |
| Progress | 1/1 |
| Workflow | `broker_review_ready` |
| Idempotency | send replayed; VIN submit replayed |

Notes:

- Customer Start Claim accepted Must Have fields (`ok: true`).
- Case Brief showed accident description / date / location / injury; VIN absent from initial missing blockers.
- VIN classified `request_more` / `optional`; only VIN was sendable.
- No Cap 4 confirm/apply invoked.

## Founder QA checklist (max 10) — manual

Create a **new** claim from Mini Program (do not reuse the automated smoke case above).

| # | Step | Expected screen | Primary CTA | Authoritative result | Screenshot |
|---|---|---|---|---|---|
| 1 | Open Mini Program Preview on iPhone | Start Claim | Enter claim | Title: 告诉陈总发生了什么; VIN framed as later | Home |
| 2 | Fill Must Have | Intake form | 提交给陈总 (enabled when complete) | 经过 / 时间 / 地点 / 受伤 required | Filled |
| 3 | Submit | Success receipt | Done | 已收到您的事故说明; VIN as later Request More | Success |
| 4 | Refresh Workbench; find by title/time | Document Intake queue | Open newest TEST/customer claim | Same submission visible | Queue |
| 5 | Read Case Brief | 事故摘要 · 先看发生了什么 | Read | Description, date, location, injury clear in ≤10s | Brief |
| 6 | Open 请客户补充 | Request More | Select VIN only | VIN is Request More, not initial blocker | Checklist |
| 7 | Send once | Waiting / QR | Send Request | Progress 0/1; customer access ready | Sent |
| 8 | Customer access → submit valid VIN | VIN task | Submit | Accepted | Customer |
| 9 | Broker refresh | Customer replied | Review | Exact VIN, 1/1, Ready for Review | Broker |
| 10 | Stop | — | — | Do **not** Confirm / Apply (Cap 4) | — |

## P0 / P1

- **P0:** none
- **P1:** none release-blocking (cosmetic polish deferred)

## Rollback

1. Cloud Run: route traffic to prior revision `fiqa-api-00217-j7t`  
   `gcloud run services update-traffic fiqa-api --region us-west1 --to-revisions=fiqa-api-00217-j7t=100`
2. Vercel: promote previous production deployment for project `ui` / alias `ui-smoky-beta.vercel.app`
3. Mini Program: do not promote Experience; keep prior uploaded version
