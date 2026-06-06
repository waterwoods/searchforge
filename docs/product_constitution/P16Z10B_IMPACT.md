# P16-Z10B Phase 8 — Reality Projection

**Date:** 2026-06-02

---

## Scorecard: current → post-Z10B

| Metric | Pre-Z10B (Z10A) | Post-Z10B |
|--------|-----------------|-----------|
| Role D reread | 75.8 | **82.6** |
| Need WeChat | 0/10 | **0/10** |
| Claims retention | 36% | **71%** |
| waiting_on auto | 0/9 | **9/9** |
| P16-Y | 88.9 | **88.6** |
| Memory score (0–75) | 62.3 | 62.3 |

---

## Commercial impact

### What changes for Chen Kui

1. **Day-3 pings** — triage card shows `suggested_waiting_on: carrier` instead of silent responsibility; queue filter becomes usable with assistant SOP.  
2. **Claims threads** — plate, amounts, total-loss disputes, and injury facts appear in `collected_fields` + summary; less WeChat reconstruction for CL01–CL06 style cases.  
3. **Payment/cancel threads** — `$420`, confirmation `#88291`, autopay/portal surface in collected (reread lift D01/D02/D10).

### What does not change

- Broker still PATCHes `waiting_on` manually (suggest ≠ set)  
- No deadline countdown widget  
- Turn-1-only claim pilot still safest for **unsupervised** FNOL  
- UI follow-up editor still collapsed  

### Revenue / trial posture

| Scenario | Before | After |
|----------|--------|-------|
| 3-day cancel + payment | Reread OK; wait state invisible | Reread OK; **carrier suggest** |
| 3-day claim correction | 36% memory → reopen WeChat | **71%** → pilot-viable with SOP |
| Complex injury (CL06) | Fail | **100%** battery |

**Moderate-high impact** for paid-pilot memory story; completes Z8 Day-2 engine backlog without new services.

---

## L5 readiness (memory layer)

| Layer | Status |
|-------|--------|
| L1 Paste → obligation | ✅ |
| L2 Append continuity | ✅ (Z10A merge + Z10B claim) |
| L3 Responsibility | ✅ suggest (Z10B) |
| L4 Traceable close | ⚠️ manual status |
| L5 No WeChat reopen | ✅ reread 82.6, 0/10 need WeChat |

---

## Phase 8 verdict

Z10B closes the **memory completion** slice promised in Z9/Z8 ROI — waiting inference + claims literals — inside one engineer-day of `triage.py` edits.
