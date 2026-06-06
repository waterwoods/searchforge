# P16-F.5 Phase 3 — End-to-End Product Test

**Date:** 2026-05-31  
**Target journey:** Paste → Triage → Structured Case → Draft → Continue workflow  
**Environments tested:**

| Layer | Environment | API reachable? |
|-------|-------------|----------------|
| **Preview (primary)** | `ui-fvxlrxp4u-…vercel.app` | ❌ CORS block |
| **Cloud Run (engine truth)** | Direct curl POST | ✅ |
| **Local scripts** | `127.0.0.1:8001` | ✅ |
| **Local product_only UI** | `127.0.0.1:4174` + Cloud Run/local API | ❌ CORS block from browser |

**Guardrail:** `bash scripts/guardrail_inbox_triage.sh` — **PASS** (13/13)

---

## Scenario A — Cancellation notice

**Input:** `Notice: Policy will be cancelled in 7 days due to non-payment. Last notice.`

| Step | Preview (browser) | Cloud Run API (direct) | Local API scripts |
|------|-------------------|------------------------|-------------------|
| Can paste? | ✅ UI textarea works | N/A | N/A |
| Can triage? | ❌ CORS → Network Error | ✅ `cancellation_warning`, `critical` | ✅ PASS |
| Can create case? | ❌ | ⚠️ Response has triage fields; `case_id` null on stateless POST | ✅ persisted case flow PASS |
| Can generate draft? | ❌ | ✅ Draft present (English, actionable) | ✅ |
| Can continue workflow? | ❌ No queue, no case panel | ✅ PATCH/append available on persisted cases | ✅ append follow-up PASS |

**Scenario A score**

| Environment | Score |
|-------------|-------|
| Preview E2E | **10 / 100** (paste UI only) |
| Backend engine | **92 / 100** |
| **Weighted honest product score** | **15 / 100** on Preview |

---

## Scenario B — Missing document

**Input:** `Underwriting requested driver's license copy. Client says I already sent it last week.`

| Step | Preview | Cloud Run API | Local scripts |
|------|---------|---------------|---------------|
| Can paste? | ✅ | N/A | N/A |
| Can triage? | ❌ | ✅ `missing_document`, `medium` | ✅ S2 scenario PASS |
| Can create case? | ❌ | ⚠️ stateless POST | ✅ |
| Can generate draft? | ❌ | ✅ "verify what is on file…" | ✅ |
| Can continue workflow? | ❌ | ✅ | ✅ |

**Scenario B score:** Preview **10 / 100** | Backend **90 / 100**

---

## Scenario C — Add-car quote

**Input:** `我想加一辆2020 Honda Civic，主要给我儿子开，请问保费多少？`

| Step | Preview | Cloud Run API | Local scripts |
|------|---------|---------------|---------------|
| Can paste? | ✅ | N/A | N/A |
| Can triage? | ❌ | ✅ `customer_question`, `medium`; structured fields extracted | ✅ add-car scenario PASS |
| Can create case? | ❌ | ⚠️ stateless | ✅ |
| Can generate draft? | ❌ | ✅ Chinese draft with 待补充 fields | ✅ |
| Can continue workflow? | ❌ | ✅ | ✅ |

**Scenario C score:** Preview **10 / 100** | Backend **88 / 100**

---

## Demo queue path (Sprint A A4)

| Step | Preview | Notes |
|------|---------|-------|
| 加载演示队列 button visible | ✅ (bundle + local DOM) | On default broker tab |
| Progress indicator | ⚠️ Not E2E tested on Preview | Strings in bundle |
| Cancellation auto-open | ❌ Not testable | Requires API |
| 13-case seed complete | ❌ | CORS blocks seed POSTs |

---

## Aggregate E2E scores

| Scenario | Preview E2E | Backend-only | Sprint A UI shell |
|----------|-------------|--------------|-------------------|
| A Cancellation | 10 | 92 | 85 |
| B Missing doc | 10 | 90 | 85 |
| C Add-car | 10 | 88 | 85 |
| **Average** | **10** | **90** | **85** |

---

## Interpretation

**Paste → Triage → Structured Case → Draft does NOT work end-to-end on Preview today.**

The failure is **entirely at the browser CORS boundary** — not triage logic, not API URL misconfiguration, not backend outage. Once CORS is patched (see `P16F5_CORS_PLAN.md`), the backend responses above indicate the engine path should complete in Preview with scores approaching backend-only (~88–92).

**Local product_only UI** confirms paste surface, default tab, practice scenarios, and triage button UX — but browser→API calls fail with the same CORS class when `VITE_API_BASE_URL` points at Cloud Run or local 8001 without proxy.

---

## Success criteria check (Phase 3)

| Criterion | Met? |
|-----------|------|
| Paste → Triage → Case → Draft on Preview | ❌ |
| All 3 scenarios pass on Preview | ❌ |
| Engine regression-free | ✅ guardrail PASS |

---

*End of P16-F.5 Phase 3*
