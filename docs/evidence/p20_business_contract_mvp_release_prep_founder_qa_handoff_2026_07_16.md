# P20 Business Contract MVP — Release Prep Loop #1 Founder QA Handoff

**Date:** 2026-07-16  
**Loop:** Release Preparation Loop #1  
**Objective:** Take Business Contract MVP from local PASS to founder-testable QA RC  
**Release:** NO — pending manual Founder QA  
**Capability 4 started:** NO

## Verdict (automated gates only)

| Gate | Result |
|---|---|
| Business Contract compliance | PASS (automated / code review) |
| North Star / UX compliance | PASS (automated / screen review) |
| Regression + E2E consistency | PASS (focused suite) |
| Automated main-chain smoke | See § Smoke below (filled after QA deploy) |
| Manual Founder QA | PENDING |

## Surfaces for Founder QA

| Surface | Value |
|---|---|
| Workbench alias | https://ui-smoky-beta.vercel.app/workbench/document-intake |
| Backend | https://fiqa-api-g7zatxrycq-uw.a.run.app |
| Mini Program AppID | `wxa610932351416622` |
| apiProfile | `qa` |
| API base | `https://fiqa-api-g7zatxrycq-uw.a.run.app` |

### Obtain Preview / Experience QR

1. Open WeChat DevTools → this repo `miniapp/`.
2. Confirm AppID `wxa610932351416622`.
3. Confirm `config.local.ts` selects `apiProfile: "qa"` (HTTPS Cloud Run base above).
4. Run `cd miniapp && npm run preview:preflight` (must PASS).
5. In DevTools: **Preview** (or upload **Experience Version**) → scan QR on iPhone.
6. Do **not** claim phone QA was performed by automation.

## Founder QA checklist (max 10)

| # | Step | Expected screen | Primary CTA | Authoritative result | Screenshot |
|---|---|---|---|---|---|
| 1 | Open Mini Program Preview on iPhone | Start Claim home | 告诉陈总发生了什么 / enter | No VIN-first teaching | Home |
| 2 | Start a new claim | Must Have intake | Fill 经过 / 时间 / 地点 / 受伤 | Submit enabled only when Must Have complete | Intake filled |
| 3 | Submit Must Have | Success receipt | 提交给陈总 | “已收到您的事故说明”; VIN framed as later Request More | Success |
| 4 | Refresh Workbench; find TEST claim by title/time | Document Intake queue | Open the new TEST claim | Same case as customer submit (title/time) | Queue |
| 5 | Open Case Brief | 事故摘要 · 先看发生了什么 | Read summary | Description, date, location, injury visible | Case Brief |
| 6 | Confirm VIN is Request More | 请客户补充 | Select VIN only | VIN not an initial-intake blocker | Request More |
| 7 | Send VIN request once | Waiting for customer / QR | Send Request (one click) | Progress 0/1; customer access ready | Sent |
| 8 | Open customer access; submit valid VIN | Customer VIN task | Submit VIN | Accepted; no duplicate command | Customer done |
| 9 | Broker refresh / detail | Customer replied | Review VIN | Exact VIN, 1/1, Ready for Review | Broker VIN |
| 10 | Stop | — | — | Do **not** Confirm/Apply (Cap 4) | — |

## Smoke fixture (filled after automated Phase 7)

- **TEST title:** _(pending smoke)_
- **Created (UTC):** _(pending smoke)_
- **Commit SHA:** _(pending commit)_
- **Backend revision:** _(pending deploy)_

## Rollback

1. Cloud Run: `gcloud run services update-traffic fiqa-api --to-revisions=<previous>=100 --region us-west1`
2. Vercel: promote prior production deployment in Vercel dashboard for `ui-smoky-beta`
3. Mini Program: do not promote Experience; keep previous uploaded version
