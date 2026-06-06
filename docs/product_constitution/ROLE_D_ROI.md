# P16-Z7 Phase 8 — ROI Estimate

**Date:** 2026-06-02  
**Basis:** Role D battery (10 journeys) + P16-Z6 ROI model + 68.9 avg reread  
**Scope:** Memory validation only — no new features built in Z7

---

## Time savings (3-day case)

| Activity | Before (min) | After (current) | Savings | Applies when |
|----------|--------------|-----------------|---------|--------------|
| Re-read WeChat for last 2–3 bubbles | 3–5 | 0.5 (对话记录) | **~3 min** | Append used + thread visible |
| Re-derive payment/cancel facts | 4–6 | 2 | **~3 min** | D08, D09 only |
| Wrong lane decode (remove→add-car) | 5–8 | 5–8 | **0** | D07 — still fails |
| Day 3 “what are we waiting for?” | 2–3 | 2–3 | **0** | waiting_on manual |
| Re-paste as duplicate case | 5–10 | 1 | **~6 min** | If append habit (Z6 CTA) |

**Per 3-day case (weighted):** **~4–8 min saved** on pass band (6/10); **~0–2 min** on fail band (4/10).

---

## Volume model (pilot office)

| Assumption | Value |
|------------|-------|
| Multi-day cases / broker / week | 6 |
| Pass-band share | 60% |
| Minutes saved / pass case | 7 |
| Minutes saved / fail case | 1 |

**Weekly:** 6 × (0.6×7 + 0.4×1) ≈ **27 min/broker/week**  
**Monthly (4 brokers):** ≈ **7 hours/office**

---

## Messages avoided

| Type | Est./week/broker | Mechanism |
|------|------------------|-----------|
| “What did client say again?” internal pings | 3–5 | Thread + summary |
| Client re-asks for same checklist | 1–2 | Better draft on D04, D08 |
| Duplicate case cleanup | 0.5–1 | Append vs re-paste |

**Not avoided:** Attachment resend, carrier portal checks, payment verification — engine gaps.

---

## Re-reads avoided

| Signal | Role D measurement |
|--------|-------------------|
| Forced WeChat reopen | **4/10** journeys (40%) |
| Implied re-reads avoided | **6/10** (60%) |
| Best journey (D08) | **1 re-read avoided** (draft + summary sufficient) |
| Worst (D10) | **3+ re-reads** still required |

**vs P16-Z6 pre-thread estimate (50% reopen):** Z7 shows **40% mandatory reopen** on stricter 3-day battery — modest improvement.

---

## TOP 10 highest ROI fixes (from Z7 evidence)

| Rank | Fix | Effort | ROI | Z7 evidence |
|------|-----|--------|-----|-------------|
| 1 | Chinese payment/lapse classification | 1 day | ★★★★★ | D10, D01 fail |
| 2 | Remove-car lane guard (no add-car eat) | 0.5 day | ★★★★★ | D07 trust break |
| 3 | Persist collected on all append paths | 1 day | ★★★★★ | D03, D10 fields empty |
| 4 | `waiting_on` heuristic from triage | 0.5 day | ★★★★☆ | Phase 6: 0/9 auto |
| 5 | Claim plate/$/police in collected merge | 1 day | ★★★★☆ | Claims 36% retention |
| 6 | Deploy Z6 thread + append CTA | deploy | ★★★★★ | +8 reread pts est. |
| 7 | Per-message date in thread UI | 0.5 day | ★★★☆☆ | Timeline gap #1 |
| 8 | Turn-delta on broker workbench | 0.5 day | ★★★☆☆ | Activity collapsed |
| 9 | Day 3 generic broker step refresh | 0.5 day | ★★★☆☆ | D01 same step ×3 |
| 10 | Founder 3× logged 3-day cases | 1 hr | ★★★★★ | Commercial proof |

---

## Investment vs return (Z7)

| Input | Output |
|-------|--------|
| Z7 validation sprint (docs + battery) | Clear NO-GO list for 3-day unsupervised |
| ~3 engineer-days (fixes 1–5) | Projected 40% → **15%** forced WeChat reopen |
| Z6 already shipped | D08, D09 prove merge ROI |

---

## Phase 8 verdict

**ROI positive for pilot** on renewal + correction + UW threads.  
**ROI negative risk** if broker hits D07/D10/claims correction without training — time lost to wrong lane > time saved.

**Break-even:** ~**5 multi-day cases/month** saved at 7 min each ≈ **35 min** — achievable at current pass band.
