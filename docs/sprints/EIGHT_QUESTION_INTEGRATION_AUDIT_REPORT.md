# Eight-Question Integration Audit + Fix Report

**Sprint:** Eight-Question Integration Audit + Fix Sprint  
**Date:** 2026-03-14  
**Execution:** ~35 minutes

---

## 1. Sprint Theme

**What was audited:** Whether the 8 selected high-value auto-insurance question types (new_car_quote, cancellation_warning, payment_failed, missing_document, already_sent_followup, notice_confusion, premium_too_high, claim_intake) have been integrated into the product in a meaningful way.

**Why now:** Founder wants to know what is actually visible and demo-ready vs docs-only. Before claiming "integrated," we must verify product surfaces.

---

## 2. Control Docs Created

| Doc | Path | Purpose |
|-----|------|---------|
| Sprint Blueprint | `docs/sprints/EIGHT_QUESTION_INTEGRATION_AUDIT_BLUEPRINT.md` | Why audit, what "integrated" means, partial vs missing |
| Execution Outline | `docs/sprints/EIGHT_QUESTION_INTEGRATION_AUDIT_EXECUTION_OUTLINE.md` | Workstreams, asset surfaces, 8-type → backend/SA mapping |
| Acceptance Criteria | `docs/sprints/EIGHT_QUESTION_INTEGRATION_AUDIT_ACCEPTANCE_CRITERIA.md` | Truly integrated vs docs-only vs config-only vs frontend-visible |

---

## 3. Full Asset Audit

### Surfaces Inspected

| Surface | Path | Findings |
|---------|------|----------|
| Docs / handling matrix | `configs/docs/faq_handling_matrix.md`, `configs/auto_insurance_faq_intake_corpus.json` | All 8 present with handling framework |
| Backend triage | `services/fiqa_api/inbox_triage/triage.py` | 8 types mapped: direct categories (cancellation_warning, payment_lapse_expiration, missing_document) or customer_question sub-types (_is_add_vehicle_request, _is_premium_review_request, _is_claim_intake_request, _is_english_notice_confusion) |
| Inbox triage scenarios | `configs/inbox_triage_scenarios.json` | 53 scenarios; all 8 types covered (expected_category or customer_question with sub-type) |
| Multi-turn simulations | `configs/customer_entry_multi_turn_simulations.json` | 38 scenarios; categories: add_car_quote, payment_failed_cancellation_risk, english_notice_confusion, missing_document, claim_intake, premium_review |
| Simulation Assistant | `configs/simulation_assistant_scenarios.json` | flow_types: add_car, notice_cancellation, missing_document, claim, renewal_premium, remove_car, dmv_sr22; **notice_confusion was missing** before fix |
| Frontend | `UnifiedIntakePage.tsx`, `SimulationAssistant.tsx` | Category labels, case focus, scenario groups; faq_corpus scenarios not in visible groups (FAQ-RM1, FAQ-SR1, FAQ-W1) |

### Strongest Findings

- **Backend logic:** All 8 types have detection (direct or sub-type). Reply templates, structured fields, handoff logic all wired.
- **Inbox triage:** 53/53 scenarios pass. Coverage for all 8.
- **Multi-turn:** 38/38 pass. Strong coverage for add_car, payment/cancel, notice confusion, missing_doc, claim, premium.
- **Simulation Assistant:** 27 scenarios (after fix). add_car, notice_cancellation, missing_document, claim, renewal_premium all well represented.

### Weakest Findings

- **notice_confusion:** Had no dedicated Simulation Assistant scenario before fix. Inbox R19 exists; multi-turn MT7/MT8/MT24 exist; backend handles it. Gap: SA visibility.
- **already_sent_followup:** No standalone flow_type. Embedded in missing_document (SIM8, SIM10, R2, R8, FAQ-AS1). By design (FAST path, minimal); acceptable.
- **faq_corpus visibility:** FAQ-RM1, FAQ-SR1, FAQ-W1 exist but `groupScenarios()` does not include `faq_corpus` section — they are run by script but not shown in UI groups.

---

## 4. Eight-Question Integration Matrix (REQUIRED)

| # | Question Type | Docs | Handling Matrix | Backend Logic | Scenario | SA Visible | Frontend/Demo | Realism | Integration Level |
|---|---------------|------|-----------------|---------------|----------|------------|---------------|---------|-------------------|
| 1 | new_car_quote | ✓ | ✓ | ✓ (add_vehicle) | ✓ | ✓ (add_car) | ✓ | Strong | **Fully integrated** |
| 2 | cancellation_warning | ✓ | ✓ | ✓ (direct) | ✓ | ✓ (notice_cancellation) | ✓ | Strong | **Fully integrated** |
| 3 | payment_failed | ✓ | ✓ | ✓ (payment_lapse_expiration) | ✓ | ✓ (notice_cancellation) | ✓ | Strong | **Fully integrated** |
| 4 | missing_document | ✓ | ✓ | ✓ (direct) | ✓ | ✓ | ✓ | Strong | **Fully integrated** |
| 5 | already_sent_followup | ✓ | ✓ | ✓ (FAST/Turn 2+) | ✓ | Partial (embedded in missing_document) | ✓ | Acceptable | **Partially integrated** |
| 6 | notice_confusion | ✓ | ✓ | ✓ (_is_english_notice_confusion) | ✓ | ✓ (after fix: FAQ-NC1) | ✓ | Strong | **Fully integrated** |
| 7 | premium_too_high | ✓ | ✓ | ✓ (premium_review) | ✓ | ✓ (renewal_premium) | ✓ | Strong | **Fully integrated** |
| 8 | claim_intake | ✓ | ✓ | ✓ (_is_claim_intake_request) | ✓ | ✓ (claim) | ✓ | Strong | **Fully integrated** |

**Summary:** 7 fully integrated, 1 partially (already_sent_followup — embedded in missing_document, no standalone SA flow_type; by design).

---

## 5. Iteration Loop 1

### What Was Verified

- `run_inbox_triage_scenarios.py`: 53/53 passed
- `run_multi_turn_simulations.py`: 38/38 passed (Strong: 38)
- `audit_state_field_accuracy.py`: 7/7 passed
- `verify_speed_routing.py`: 9/9 OK
- `guardrail_inbox_triage.sh`: PASS
- `ui && npm run build`: Success

### What Increased Confidence

- Backend triage logic correctly routes all 8 types.
- Inbox and multi-turn scenario packs pass.
- Simulation Assistant scenarios (26 at start) all Normal.

### What Reduced Confidence

- notice_confusion had no SA scenario — founder could not run a pure "英文 notice 看不懂" flow from SA.
- already_sent_followup has no standalone visibility (acceptable by design).

### How Many of the 8 Truly Integrated (Before Fix)

- **Fully:** 6 (new_car_quote, cancellation_warning, payment_failed, missing_document, premium_too_high, claim_intake)
- **Partially:** 2 (notice_confusion — SA gap; already_sent_followup — embedded)

### Was Loop 1 Worth It?

Yes. Identified the notice_confusion SA gap and validated the rest.

---

## 6. Iteration Loop 2

### Small Fixes Applied

1. **Added FAQ-NC1 (notice_confusion) to Simulation Assistant**
   - flow_type: `notice_confusion`
   - title: "Notice confusion — 这个英文 notice 看不懂"
   - section: edge_cases (visible in UI)
   - turns: 2 (Turn 1: "这个英文 notice 看不懂"; Turn 2: "发你微信了，你看下什么意思")
   - expected_handoff_after_turn: 2

### What Changed

- `configs/simulation_assistant_scenarios.json`: +1 scenario
- `ui/src/config/simulation_assistant_scenarios.json`: synced

### What Improved

- notice_confusion now has a dedicated SA scenario. Founder can run it from Edge cases / QA.
- All 8 question types now have SA representation (7 with explicit flow_type, 1 embedded).

### Redeploy Needed?

- **Frontend:** Yes, if deploying to Vercel — `ui/src/config/simulation_assistant_scenarios.json` changed.
- **Backend:** No.

---

## 7. Optional Loop 3

**Used?** No. Loop 2 addressed the main gap. faq_corpus visibility (FAQ-RM1, FAQ-SR1, FAQ-W1 not in UI groups) is a lower-priority polish; did not expand scope.

---

## 8. Validation Summary

| Check | Result |
|-------|--------|
| run_inbox_triage_scenarios.py | 53/53 passed |
| run_multi_turn_simulations.py | 38/38 passed |
| audit_state_field_accuracy.py | 7/7 passed |
| verify_speed_routing.py | 9/9 OK |
| guardrail_inbox_triage.sh | PASS |
| run_simulation_assistant_scenarios.py | 27/27 Normal (after fix) |
| ui npm run build | Success |

**Limitations:** unified_intake_smoke_check.sh requires live server; not run. API test passed when server was on 8001 (guardrail run).

---

## 9. Final Founder Judgment

### 1. Have the 8 selected question types really been integrated?

**Yes.** All 8 are present in docs, handling matrix, backend logic, and scenario configs. 7 have explicit Simulation Assistant scenarios; 1 (already_sent_followup) is embedded in missing_document by design.

### 2. Which are fully integrated right now?

**7:** new_car_quote, cancellation_warning, payment_failed, missing_document, notice_confusion (after fix), premium_too_high, claim_intake.

### 3. Which are only partially integrated?

**1:** already_sent_followup — no standalone SA flow_type; embedded in missing_document. Minimal by design (FAST path).

### 4. Which are still mostly docs-only or weakly surfaced?

**None.** All 8 have backend handling and scenario coverage.

### 5. If the founder opens the frontend tonight, how much of the 8-question work is actually visible?

**All 8 are testable:**
- **Recommended trial:** Cancellation risk, Missing document, Add-car quote, Premium review, Claim intake (5 of 8)
- **Real customer:** Notice+cancel, Doc frustrated, Add-car, Claim, Renewal, Payment+dec, Doc vague (covers cancellation, payment, missing_doc, add_car, claim, premium)
- **Edge cases:** AutoPay failed, Missing DL, Notice correction, Vague "already sent", Add car partial, Claim hit-and-run, Renewal indirect, Notice minimal, **Notice confusion (FAQ-NC1 — new)**
- **FAQ corpus:** Remove car, SR-22/DMV, What to send (garaging) — these run in script but faq_corpus section is not in UI groups (known gap)

### 6. What should be fixed next if the goal is stronger realism and product readiness?

1. **Add faq_corpus to Simulation Assistant UI groups** — FAQ-RM1, FAQ-SR1, FAQ-W1 exist but are not shown in the scenario picker. Low effort.
2. **Consider a standalone already_sent_followup SA scenario** — Optional; current embedding in missing_document is acceptable.
3. **Redeploy frontend** — To surface FAQ-NC1 (notice_confusion) in production.

---

## 10. 中文宏观总结

**这 8 个问题现在到底融合进去没有？**  
是的，都融合了。文档、处理矩阵、后端逻辑、场景配置都有。

**有几个是真正完整融合了？**  
7 个：new_car_quote、cancellation_warning、payment_failed、missing_document、notice_confusion（本次补上）、premium_too_high、claim_intake。

**有几个只是部分融合？**  
1 个：already_sent_followup，没有独立 SA 场景，嵌在 missing_document 里，设计如此。

**你今晚在前端能看到多少？**  
8 个都能测到。Recommended trial 有 5 个，Real customer 和 Edge cases 覆盖其余。本次新增的「Notice confusion — 这个英文 notice 看不懂」在 Edge cases 里。

**现在最大的缺口是什么？**  
faq_corpus 的 3 个场景（Remove car、SR-22、What to send）在脚本里会跑，但 UI 分组里没显示。

**下一步最该做什么？**  
1）前端重新部署，让 FAQ-NC1 上线；2）可选：把 faq_corpus 加入 UI 分组，让这 3 个场景在界面上可见。

---

## 11. COPY/PASTE DECISION BLOCK

```
EIGHT-QUESTION INTEGRATION AUDIT — FOUNDER SUMMARY
==================================================

Fully integrated: 7 of 8
  new_car_quote, cancellation_warning, payment_failed, missing_document,
  notice_confusion (fixed this sprint), premium_too_high, claim_intake

Partially integrated: 1 of 8
  already_sent_followup — embedded in missing_document, no standalone SA scenario (by design)

Docs/config only: 0

Visible in frontend tonight: All 8 testable
  Recommended trial: 5 flows
  Real customer + Edge cases: rest
  New: "Notice confusion — 这个英文 notice 看不懂" in Edge cases (FAQ-NC1)

Biggest gap: faq_corpus scenarios (Remove car, SR-22, What to send) run in script but not in UI groups

Next step: Redeploy frontend for FAQ-NC1; optionally add faq_corpus to UI scenario groups
```
