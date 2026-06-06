# P16-Z12 Phase 5 — Preview Acceptance Cases

**Date:** 2026-06-02  
**Target:** Deployed backend `https://fiqa-api-g7zatxrycq-uw.a.run.app` (browser Preview blocked by CORS — API direct)

**Method:** `POST /api/inbox/triage` with sprint case text (no API key — perimeter unset on live service).

---

## Case 1 — Payment / lapse

**Input:** (sprint payment letter — 没有成功扣款, 420美元, 换银行卡, 取消风险)

| Field | Result |
|-------|--------|
| **Category** | `customer_question` ❌ (expected `payment_lapse_expiration`) |
| **Office title** | *(empty)* |
| **Missing info** | not surfaced in API response |
| **Waiting on** | none |
| **Next action** | Generic English: "Read the notice in plain language…" |
| **Classification signals** | `[]` |
| **Service type** | `general_inquiry` ❌ |

**Notes:** Stale backend + marker gap: text uses **没有成功扣款** (no substring **没扣**). Z11 markers expect 没扣 / 未成功扣款 / etc.

**PASS / FAIL:** **FAIL**

**Screenshot:** N/A (CORS blocks browser triage from Preview)

---

## Case 2 — Remove vehicle

**Input:** (sold 2018 Camry, still on policy, 补材料, 移除)

| Field | Result |
|-------|--------|
| **Category** | `missing_document` ⚠️ (expected remove-vehicle lane; service correct) |
| **Office title** | *(empty on HTTP)* |
| **Missing info** | not in top-level response |
| **Waiting on** | none |
| **Next action** | "Verify whether customer-resubmitted items were received…" |
| **Classification signals** | `[]` |
| **Service type** | `remove_car` ✅ |

**PASS / FAIL:** **FAIL** (category + office surface + waiting)

**Screenshot:** N/A

---

## Case 3 — Claim / total-loss dispute

**Input:** (101高速追尾, 8ABC123, 全损, John adjuster, 8500美元)

| Field | Result |
|-------|--------|
| **Category** | `customer_question` ❌ |
| **Office title** | *(empty)* |
| **Missing info** | `year`, `make_model`, `vin`, `zip`, `delivery_date`, `primary_driver` (add-car still_needed) ❌ |
| **Waiting on** | none |
| **Next action** | Add-car style: "Guide client to collect evidence and start claim reporting…" ❌ |
| **Classification signals** | `[]` |
| **Service type** | `add_car` ❌ (expected claim) |
| **Plate / amount retained** | Not in structured fields on HTTP response |

**PASS / FAIL:** **FAIL**

**Screenshot:** N/A

---

## Local parity check (same HTTP path :8001)

Same three cases on **local** running server (`b0d6073` tree) returned **identical** categories/service types — office fields not exposed on simple triage POST. Role D module battery still passes (82.6 reread) on **journey fixtures**, not these sprint paste texts.

---

## Summary

| Case | PASS/FAIL |
|------|-----------|
| 1 Payment | **FAIL** |
| 2 Remove | **FAIL** |
| 3 Claim | **FAIL** |

**Root cause:** Backend not redeployed; live revision `0c2ed6d59`. Secondary: payment acceptance wording vs Z11 markers; claim route ordering on full HTTP path.
