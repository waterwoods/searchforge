# P16-U Phase 6 — Reality Revalidation

**Date:** 2026-06-01  
**Rule:** Deployed URLs only — no localhost scoring  
**Method:** curl + vercel curl + API probes on live endpoints

---

## URLs tested

| Role | Primary URL | Fallback |
|------|-------------|----------|
| Andy / Broker trial | Preview alias | Production (wrong UI) |
| Role C cold user | Production | Preview (401) |
| Customer | Production | N/A (no customer route on product_only Preview) |
| Assistant (API) | Cloud Run | — |

---

## Andy (Founder)

| Check | URL | Result | Score est. |
|-------|-----|--------|------------|
| Cold open Preview (incognito) | `ui-waterwoods` | **FAIL** — HTTP 401, Vercel SSO | 12/100 |
| Logged-in / vercel curl Preview | `ui-iwnyo9ufa` | **PASS** — bundle has P16-O + product_only | ~74/100 |
| Cold open Production | `ui-smoky-beta` | **PASS** HTTP 200 — **wrong UI** (pre-P16-O) | ~52/100 |
| 15-min E2E log published | — | **FAIL** — not on deployed URL | — |
| API triage (curl) | Cloud Run | **PASS** — Chinese draft returned | engine OK |

**Andy verdict:** Can certify engine via API; **cannot certify broker loop on shareable Preview URL.**

---

## Role C (Skeptical broker, no context)

| Check | URL | Result | Score est. |
|-------|-----|--------|------------|
| Cold open documented Preview | `ui-waterwoods` | **FAIL** — login wall, never sees product | 12/100 |
| Cold open Production | `ui-smoky-beta/workbench/unified-intake` | **FAIL** — customer-portal shape, 4 tabs, add-car default (P16-Q pattern on stale bundle) | ~35/100 |
| Trust / engineer chrome | Production bundle | **FAIL** — full dev UI signals (no product_only) | — |
| Paste path visible | Preview bundle (authenticated path only) | **PASS** in bundle | not reachable cold |

**Role C verdict:** **Would not trust or use.** Link reads broken (Preview) or wrong product (Production).

---

## Broker (Chen Kui trial persona)

| Check | URL | Result | Score est. |
|-------|-----|--------|------------|
| Day 0 — open trial link | Preview alias | **FAIL** — SSO | 12/100 |
| Day 0 — paste box | Preview | **Blocked** | — |
| Demo queue load | Preview + API | **Blocked** at browser (SSO); API `/api/inbox/cases` **PASS** via curl | — |
| 5-min paste loop | Preview | **FAIL** — cannot start | — |

**Broker verdict:** **Trial cannot start.** Same blocker as P16-Q/R/T.

---

## Customer

| Check | URL | Result | Score est. |
|-------|-----|--------|------------|
| Public entry | Production | HTTP 200 — legacy customer-portal UI | ~33/100 (P16-N baseline) |
| product_only customer path | Preview | Tab hidden in bundle design; **URL not shareable** (401) | N/A |
| Trust copy P16-O | Production | **Missing** — stale bundle | FAIL |

**Customer verdict:** **No validated customer path on deployed URLs.**

---

## Assistant (API / triage layer)

| Check | Endpoint | Result |
|-------|----------|--------|
| `/readyz` | Cloud Run | **PASS** — `intake_path_ready: true` |
| CORS preflight | OPTIONS `/api/inbox/cases` | **PASS** — origin `ui-iwnyo9ufa` |
| GET cases | `/api/inbox/cases?limit=1` | **PASS** — returns case list |
| POST triage (Chinese input) | `/api/inbox/triage` | **PASS** — Chinese draft: `这段内容还不够完整。把完整通知或前后内容再发我一下...` |
| Draft language | — | **PASS** — Chinese output (FP-018 not triggered on this probe) |

**Assistant verdict:** **Engine healthy on deployed API.** UI path to reach it blocked by FP-004.

---

## Role summary matrix

| Role | Deployed URL usable? | Primary blocker | Score |
|------|---------------------|-----------------|-------|
| Andy | Partial (API yes; cold Preview no) | FP-004, FP-015 | ~25–74 |
| Role C | No | FP-004 / FP-013 / FP-016 | ~12–35 |
| Broker | No | FP-004 | 12 |
| Customer | No (wrong/stale UI) | FP-013, FP-016 | ~33 |
| Assistant | Yes (API) | UI access only | ~85 API |

**Weighted reality readiness (deployed):** **~28/100** for trial wedge (broker cold path) · **~85/100** for API engine

---

## Challenge to prior assumptions

| Assumption | Reality check |
|------------|---------------|
| "80% health = almost ready" | **False** — 2 FAILs are the trial entry point |
| "Production works because 200" | **False** — wrong 41-day bundle |
| "Preview bundle PASS = broker ready" | **False** — vercel curl ≠ cold user |
| "Local commit d05e94d = shipped" | **Partial** — Preview yes, Production no, access no |

---

*End of P16-U Phase 6 — Reality Revalidation*
