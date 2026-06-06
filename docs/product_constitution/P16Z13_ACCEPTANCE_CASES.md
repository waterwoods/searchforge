# P16-Z13 Phases 6–9 — Acceptance & Founder Mini-Test

**Date:** 2026-06-02  
**Engine:** Cloud Run `LLM_GENERATION_ENABLED=0`, revision `fiqa-api-00083-kng`, git `b0d6073e5`  
**Method:** `POST /api/inbox/triage` with `X-Unified-Intake-Api-Key` (same as Preview bundle)

Local rules-path (`triage_conversation`) at same commit produces **identical** categories — deploy parity achieved; sprint paste wording exposes engine gaps.

---

## Case 1 — Payment / lapse

**Input:** Sprint paste (陈先生, 没有成功扣款, 420美元, 取消保险)

| Criterion | Result |
|-----------|--------|
| payment category | ❌ `customer_question` / `general_inquiry` |
| lapse risk | ❌ no `payment_lapse_expiration`; office title null |
| amount 420 | ✅ `classification_signals` includes 提到420美元 |
| waiting_on | ❌ `suggested_waiting_on` null |
| office next step | ❌ null |

**Contrast:** Battery paste `保费420美元没扣成功` → `payment_lapse_expiration`, office title 客户保费未成功扣款…

**CASE 1: FAIL**

---

## Case 2 — Remove vehicle

**Input:** Sprint paste (卖掉 Camry, 移除)

| Criterion | Result |
|-----------|--------|
| remove vehicle | ✅ `service_type: remove_car` |
| not add car | ✅ |
| asks sale proof/date | ✅ signals + broker next step 补销售证明和卖车日期 |
| clear next step | ✅ |

**CASE 2: PASS**

---

## Case 3 — Claim

**Input:** Sprint paste (追尾, 8ABC123, John, 8500, 全损)

| Criterion | Result |
|-----------|--------|
| claim | ❌ `service_type: add_car` (office layer shows claim copy) |
| not add car | ❌ mis-tagged `add_car` |
| preserve plate 8ABC123 | ⚠️ not in collected_fields (in narrative) |
| preserve 8500 | ✅ signal |
| preserve adjuster John | ✅ signal 提到理赔员 |
| waiting_on carrier | ✅ `suggested_waiting_on: carrier` |

**Contrast:** Short battery `追尾/理赔员/8500/全损` → `claim_intake`.

**CASE 3: FAIL**

---

## Founder mini-test (5-second scan)

| Case | Office headline | Understand in 5s? |
|------|-----------------|-------------------|
| A. Missing document | 客户需补交材料 | **YES** |
| B. UW follow-up | 客户咨询加车报价 (mis-route) | **NO** |
| C. Premium renewal | 客户咨询保费/续保 | **YES** |

**FOUNDER SCORE: 2/3 YES**

---

## Parity note

Preview (new URL) + Cloud Run + local module at `b0d6073` **match** on these pastes. Remaining failures are **classification wording**, not deploy drift.
