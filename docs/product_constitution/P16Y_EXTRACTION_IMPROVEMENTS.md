# P16-Y Phase 6 — Extraction Improvements

**Date:** 2026-06-01  
**Sprint:** P16-Y Case Intelligence Hardening  
**Scope:** Safe logic-only changes in `services/fiqa_api/inbox_triage/triage.py` — no UI, no architecture  
**Guardrail:** `64/64` inbox triage scenarios still PASS after changes

---

## Changes implemented

### 1. Address change detection

**Function:** `_is_address_change_request()`  
**Markers:** 搬家, moved to, update garaging, 地址要改, 地址不对  
**Classifier:** Routes to `customer_question` before `unclear` fallback  
**Summary:** Intent hint “Address / garaging change.”  
**Broker step:** Confirm new garaging + effective date; update policy  

**Fixes:** Y11, Y12, Y13

---

### 2. Coverage question lane

**Function:** `_is_coverage_question()`  
**Markers:** liability, umbrella, comprehensive, windshield, deductible, 玻璃, 走保险  
**Question detection:** Includes full-width `？` and 还是 (claim vs self-pay)  
**Broker step:** Review limits/deductible; explain claim trade-off  

**Fixes:** Y27, Y28, Y37

---

### 3. Add-driver before missing-document

**Classifier reorder:** `_is_add_driver_request()` checked before missing-document object+request match  
**Prevents:** 驾照 + 需要 on “我儿子刚拿驾照…需要准备什么” → missing_document  

**Fixes:** Y14

---

### 4. Underwriting follow-up priority

**Function:** `_is_underwriting_followup_request()`  
**Markers:** questionnaire, 核保, respond within, prior claims, incomplete, deadline  
**Classifier:** Runs before missing_signature (“signed form” in UW context)  

**Fixes:** Y30, Y31

---

### 5. Renewal shop-around

**Rule:** renew + (shop / 涨 / premium review) → `customer_question`, not passive `renewal_reminder`  

**Fixes:** Y34

---

### 6. Deadline extraction

**Function:** `_extract_deadline_hint()`  
**Patterns:** “in N days”, “N 天”, “by MM/DD/YYYY”, “deadline Friday”, “today” + cancel/due  
**Output:** Summary suffix “Deadline: …”; `collected_fields` += `deadline_mentioned`  

**Improves:** Y01, Y10, Y29–Y31, cancellation/UW cases

---

### 7. Policy number extraction

**Function:** `_extract_policy_number_hint()`  
**Patterns:** Policy #CA-8829101, 保单号, 7–10 digit with policy/claim context  
**Output:** Summary “Policy #: …”; `collected_fields` += `policy_number`  

**Improves:** Y34, Y35

---

### 8. Notice image gap

**Function:** `_message_needs_notice_image()`  
**Rule:** Screenshot/截图 mentioned + confusion or no notice body → `still_needed_fields` += `notice_image`  

**Fixes:** Y38

---

### 9. Multi-turn correction

**Rule:** 不是…是 / 不是payment / 地址不对 + UW/address markers → customer_question or underwriting_followup  

**Fixes:** Y44 (partial — category; summary merge still weak)

---

### 10. Marker pack extension

**Added to `_FALLBACK_MARKERS`:** `address_change`, `coverage_question`, `underwriting_uw`

---

## Not changed (intentionally)

| Area | Reason |
|------|--------|
| UI / glance layout | Sprint scope |
| LLM prompts | Quota exhausted; rules path is production fallback |
| Add-car entity / PG lane | High blast radius |
| Append / session architecture | Out of scope |
| New issue_category values | Would break scenario contract |

---

## Validation

```bash
PYTHONPATH=. python3 scripts/run_inbox_triage_scenarios.py   # 64/64 PASS
PYTHONPATH=. python3 scripts/run_p16y_case_battery.py --label after
```

---

*End of P16-Y Phase 6 — Extraction Improvements*
