# P16-Z8 Phase 9 — Execution Plan

**Date:** 2026-06-02  
**Sprint:** P16-Z8 Memory Hardening Archaeology  
**Principle:** Reuse first · Build second · No new services · No SimulationAssistant duplication  
**Target:** Role D reread ≥80 · needs WeChat ≤2/10  
**Estimate:** **3 engineer-days** to Role D target

---

## Smallest implementation plan

### Day 0 — Deploy & measure (no new code)

| Step | Action | Owner |
|------|--------|-------|
| 0.1 | Deploy P16-Z6 to preview (thread card + append CTA + Y44/Y45 merge) | Eng |
| 0.2 | Run `scripts/run_role_d_memory_battery.py` post-deploy | Eng |
| 0.3 | Log 1 real 3-day case in observation log | Founder |
| 0.4 | Confirm append habit taught on Day 0 | Founder |

**Gate:** If reread ≥75 post-deploy alone, proceed to engine slice.

---

### Day 1 — Engine slice A (lane guards + merge core)

**Files:** `services/fiqa_api/inbox_triage/triage.py` only

| # | Task | Reuses | Acceptance |
|---|------|--------|------------|
| 1.1 | `_thread_is_remove_car_lane(merged_text)` | `_thread_is_premium_review_lane` pattern | D07 T3 summary ≠ "New quote" |
| 1.2 | Block add-car in `_effective_add_car_lane_active` when remove lane | Y45 premium block | D07 collected ≠ add-car slots |
| 1.3 | `_remove_car_structured_fields()` + branch before else | `_renewal_structured_fields` | D07 collected has vehicle/sale/transfer |
| 1.4 | `_merge_persisted_collected(prior, new)` generic helper | `_augment_add_car_fields_from_persisted_collected` | D03 zip persists |
| 1.5 | Guard else-branch wipe when prior collected non-empty | 5-line change L6346 | D10 fields not `[]` |
| 1.6 | Chinese 分期/installment markers → `payment_lapse_expiration` boost | existing markers | D10 ≠ unclear |
| 1.7 | `_payment_amount_hint()` → `payment_amount` collected token | deadline hint pattern | D01 $420 in collected |

**Test:** Role D battery — D07, D03, D10 must improve.

---

### Day 2 — Engine slice B (waiting + claims)

| # | Task | Reuses | Acceptance |
|---|------|--------|------------|
| 2.1 | `_suggest_waiting_on(text, still_needed, category)` → optional triage field | new heuristic | 5/9 carrier phrases suggest carrier |
| 2.2 | Wire suggest to case PATCH on append (auto or broker confirm) | `update_case_follow_up` | API test |
| 2.3 | Extend `_extract_claim_fields()`: plate, claim_amount, total_loss | existing booleans | CL01 plate in collected |
| 2.4 | Claim lane guard: missing_doc doesn't beat active claim thread | boundary logic | CL03 ≠ missing_document |
| 2.5 | Prior-turn prepend for claim correction | Z6 prepend | CL02 retention >0% |
| 2.6 | `confirmation_number` separate from policy_number | policy hint | D02 #88291 retained |

**Test:** Role D + claims battery CL01–CL10 avg retention ≥50%.

---

### Day 3 — Validation & polish

| # | Task | Acceptance |
|---|------|------------|
| 3.1 | Full Role D battery re-run | reread ≥80, needs_wechat ≤2/10 |
| 3.2 | P16-Y Y41–Y45 spot check | No regression |
| 3.3 | `guardrail_inbox_triage.sh` green | CI |
| 3.4 | Founder 3× real cases in observation log | Commercial proof |
| 3.5 | Update ROLE_D_FOUNDER_SUMMARY with post-Z8 scores | Docs |

---

## What we explicitly do NOT build

| Item | Why |
|------|-----|
| PaymentMemoryService | Exists in triage.py |
| WaitingOnEngine microservice | case_store + heuristic sufficient |
| ClaimsIntakeService | FNOL works; tune extractors |
| CollectedFieldsMergeService | Generalize add-car function |
| SimulationAssistant v2 | Orphan — wire Role D battery instead |
| CRM / Stripe / WeChat integration | Out of scope |
| Outcome / resolution UI | Deferred per constitution |
| LLM path rewrite | Rules at 88.6 sufficient |

---

## Dependency graph

```
Deploy Z6 ──────────────────────────────┐
                                        ▼
                    ┌── remove lane guard ──┐
                    │                       │
prior docs Z0-Z7 ───┼── collected merge ────┼──► Role D battery ──► GO/NO-GO
                    │                       │
                    └── payment Chinese ────┘
                              │
                              ├── waiting_on heuristic
                              └── claim field extensions
```

---

## Success criteria (Role D)

| Metric | Before Z8 | Target |
|--------|-----------|--------|
| Avg reread | 68.9 | **≥80** |
| Needs WeChat | 4/10 | **≤2/10** |
| D07 lane | add-car fail | remove_car stable |
| D10 | unclear ×3 | payment_lapse + fields |
| Claims retention | 36% | **≥50%** |
| waiting_on auto | 0/9 | **≥5/9 suggest** |

---

## Rollback plan

All changes isolated to `triage.py` + optional UI flag. Revert single commit if P16-Y regresses below 85 avg.

---

## Phase 9 verdict

**3 engineer-days** after Z6 deploy reaches Role D target. **No new modules.** Extend existing extractors, merge helper, and lane guards — the archaeology proves the architecture is correct; execution is tuning.
