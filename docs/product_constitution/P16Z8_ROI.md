# P16-Z8 Phase 8 — ROI Ranking

**Date:** 2026-06-02  
**Sprint:** P16-Z8 Memory Hardening Archaeology  
**Basis:** P16-Z7 Role D battery, P16-Z8 archaeology, P16-Z6 shipped fixes  
**Target:** Role D reread ≥80, needs WeChat ≤2/10

---

## ROI model

| Metric | Current | Post-fix target |
|--------|---------|-----------------|
| Avg reread | 68.9 | **≥80** |
| Needs WeChat | 4/10 | **≤2/10** |
| Avg memory score | 60.7/75 | **≥65/75** |
| Forced reopen rate | 40% | **≤20%** |

---

## 15-minute fixes

| # | Fix | Domain | Evidence | Impact |
|---|-----|--------|----------|--------|
| 1 | Run Role D battery after Z6 deploy | All | Baseline | Measure only |
| 2 | Founder SOP: set `waiting_on` after carrier ping | Waiting | 0/9 auto | Process |
| 3 | Narrow `policy_bill_sent` to bill-specific phrases | Payment | Y45 pre-fix | Precision |
| 4 | Add D07 to P16-Y regression watch list | Remove | D07 fail | Guard |
| 5 | Default-open follow-up editor on append (flag) | Waiting | Collapsed UX | Visibility |

---

## 2-hour fixes

| # | Fix | Domain | Files | ROI |
|---|-----|--------|-------|-----|
| 1 | `_thread_is_remove_car_lane()` skeleton | Remove | `triage.py` | ★★★★★ D07 |
| 2 | Block add-car when remove lane active | Remove | `_effective_add_car_lane_active` | ★★★★★ |
| 3 | `_remove_car_structured_fields()` | Remove + Collected | `triage.py` | ★★★★☆ |
| 4 | `plate_number` claim extractor | Claims | `_extract_claim_fields` | ★★★★☆ |
| 5 | Carrier-wait phrase → suggest `waiting_on` | Waiting | `triage.py` | ★★★★☆ |
| 6 | Client-wait from `still_needed` suggest | Waiting | `triage.py` | ★★★☆☆ |
| 7 | Don't wipe collected on else if prior non-empty | Collected | L6346 guard | ★★★★★ |
| 8 | Chinese 分期 marker → payment category boost | Payment | classify | ★★★★☆ |
| 9 | Refund follow-up → keep remove domain | Remove | boundary exception | ★★★★☆ |
| 10 | Prior-turn prepend for remove thread | Remove | Z6 pattern | ★★★☆☆ |

---

## 1-day fixes

| # | Fix | Domain | ROI | Role D impact |
|---|-----|--------|-----|---------------|
| 1 | **Generic persisted collected merge** | Collected | ★★★★★ | D03, D10, D02 |
| 2 | **Chinese payment/lapse classification** | Payment | ★★★★★ | D01, D10 |
| 3 | **Payment amount + installment fields** | Payment | ★★★★☆ | D01, D10 |
| 4 | **Claim correction merge** (plate, $, total_loss) | Claims | ★★★★☆ | CL02, CL10 |
| 5 | **Claim lane guard** vs missing_document | Claims | ★★★★☆ | CL03 |
| 6 | **`waiting_on` heuristic suite** (carrier/client/office) | Waiting | ★★★★☆ | All Day 3 |
| 7 | **Deploy Z6 thread + append CTA** | UI | ★★★★★ | +8 reread est. |
| 8 | **Day 3 broker_next_step refresh** on status ping | All | ★★★☆☆ | D01 |
| 9 | **Confirmation # field** separate from policy | Payment | ★★★☆☆ | D02 |
| 10 | **Injury markers stable** | Claims | ★★★☆☆ | CL06 |

---

## 3-day fixes

| # | Fix | Domain | Notes |
|---|-----|--------|-------|
| 1 | Full memory hardening slice (items 1–6 above) | All | **Minimum for Role D target** |
| 2 | Turn-delta block on broker workbench | UI | Generalize add-car rail |
| 3 | Per-message timestamp in 对话记录 | UI | Timeline gap |
| 4 | Claim battery hardening CL01–CL10 pass ≥60% | Claims | Regression suite |
| 5 | 3 founder-logged real 3-day cases | Process | Commercial proof |
| 6 | Default-open activity after append | UI | P16-Z5 deferred |
| 7 | Observation log outcome rows | Process | Outcome layer |
| 8 | Assist layer trial for gap-fill suggest | Hidden | Env-gated only |
| 9 | LLM path parity check | Engine | Unverified P16-Y |
| 10 | P16L payment evidence wiring | Payment | Lower priority |

---

## Ranked by ROI × effort

| Rank | Fix | Effort | ROI | Cumulative reread gain (est.) |
|------|-----|--------|-----|-------------------------------|
| 1 | Deploy Z6 thread + append CTA | deploy | ★★★★★ | +8 |
| 2 | Generic collected merge | 1 day | ★★★★★ | +6 |
| 3 | Remove-car lane guard | 0.5 day | ★★★★★ | +5 |
| 4 | Chinese payment/lapse | 1 day | ★★★★★ | +6 |
| 5 | waiting_on heuristic | 0.5 day | ★★★★☆ | +3 |
| 6 | Claim field extensions | 1 day | ★★★★☆ | +4 |
| 7 | else-branch wipe guard | 2 hr | ★★★★★ | +3 |
| 8 | Claim lane guard | 2 hr | ★★★★☆ | +2 |
| 9 | Founder 3× logged cases | 1 hr | ★★★★★ | commercial |
| 10 | Turn-delta UI | 0.5 day | ★★★☆☆ | +2 |

**Projected after fixes 1–7:** reread **~82**, needs WeChat **~2/10**.

---

## Phase 8 verdict

**Break-even:** 5 multi-day cases/month × 7 min saved = 35 min (P16-Z7).  
**Full ROI:** 3 engineer-days fixes → **~27 min/broker/week** at 60% pass band rising to 85%.
