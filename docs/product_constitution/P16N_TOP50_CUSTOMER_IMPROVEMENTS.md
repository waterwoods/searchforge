# P16-N Phase 9 — Top 50 Customer Improvements

**Date:** 2026-06-01  
**Constraints:** UI/copy/layout only — no features, no Constitution, no capabilities  
**Ranked by:** ROI (1–5) · Effort (S/M/L) · Risk (Low/Med/High)  
**Baseline score:** Customer entry ~50 · Target: **75+**

---

## Top 10 — Under 1 Hour Each

| # | Improvement | ROI | Effort | Risk | Screen |
|---|-------------|-----|--------|------|--------|
| 1 | Message-first headline: 「请把车险需求发给我们」replace product H2 subcopy | 5 | S | Low | Landing |
| 2 | Demote 联系人工 to footer link (remove equal button) | 5 | S | Low | Landing |
| 3 | Remove ①②③ from portal_empty_secondary | 5 | S | Low | Landing |
| 4 | Remove 场景仿真 link from customer tab | 4 | S | Low | Landing |
| 5 | Delete UTC timing footnote (portalSubmittedAtTimingTruthNote) | 4 | S | Low | Post-handoff |
| 6 | Remove AddCarFlowExplanation from post-handoff render | 4 | S | Low | Post-handoff |
| 7 | Hide bubble micro-tags (urgency, lifecycle, follow_up) | 4 | S | Low | Mid-flow |
| 8 | Remove 查看工作台 button from customer post-handoff | 4 | S | Low | Post-handoff |
| 9 | Single trust line at bottom; delete tagline paragraph | 5 | S | Low | Landing |
| 10 | Post-handoff one-line wait CTA above fold | 4 | S | Low | Post-handoff |

**Batch impact:** Landing −30% objects; 5s score 33 → ~55 in <1 day copy pass

---

## Top 10 — Under 1 Day Each

| # | Improvement | ROI | Effort | Risk | Screen |
|---|-------------|-----|--------|------|--------|
| 11 | Hero textarea above buttons; flip empty-state component order | 5 | M | Med | Landing |
| 12 | Hide IntakeFlowStepTrack until turns.length > 0 | 5 | M | Low | Landing → active |
| 13 | Remove quick-start button row; keep textarea + 发送 only | 5 | M | Med | Landing |
| 14 | Structured add-car: link only 「逐项填写加车信息」 | 4 | M | Low | Landing |
| 15 | Merge handoff-pending alerts into one (phone + confirm) | 5 | M | Med | Handoff |
| 16 | Collapse AddCarRecordSummaryRail to 「已记录 N 项」 | 4 | M | Low | Mid-flow |
| 17 | Remove transaction gradient banner | 4 | M | Low | Mid-flow |
| 18 | Post-handoff: single result card; hide progress card duplicate | 4 | M | Med | Post-handoff |
| 19 | Customer portal separate route; hide broker/sim tabs | 5 | M | Med | Global |
| 20 | Placeholder with 3 inline examples (remove toggle card) | 4 | M | Low | Landing |

---

## Top 10 — Under 1 Week Each

| # | Improvement | ROI | Effort | Risk | Screen |
|---|-------------|-----|--------|------|--------|
| 21 | Full message-first empty state (P16N_SINGLE_TASK_FLOW Step 1) | 5 | L | Med | Landing |
| 22 | One-question viewport mid-flow (show only next_best_question + input) | 5 | L | Med | Mid-flow |
| 23 | Handoff Step 3: inline phone/name fields + single confirm | 5 | L | Med | Handoff |
| 24 | Confirmation screen Stripe-style (P16N Step 5) | 4 | L | Med | Post-handoff |
| 25 | Progressive intent reveal after triage (hide category UI) | 5 | L | Med | Landing → active |
| 26 | My requests: collapse collected field chips to count | 3 | L | Low | Status |
| 27 | Mobile: textarea above fold at 390×844 | 4 | L | Med | Landing |
| 28 | Remove light identity / WeChat strip from customer path | 3 | L | Low | Handoff |
| 29 | Typography pass: 14px body minimum on customer surfaces | 3 | L | Low | All |
| 30 | Success animation on formal submit (check + toast) | 4 | L | Low | Handoff → confirm |

---

## Next 20 (31–50) — Backlog by ROI

| # | Improvement | ROI | Effort | Bucket |
|---|-------------|-----|--------|--------|
| 31 | Remove portalChoosePathLabel | 4 | S | <1h |
| 32 | Remove 推荐主路径 badge | 3 | S | <1h |
| 33 | Flatten nested hero grey card | 3 | M | <1d |
| 34 | Hide monospace case ID until post-handoff | 3 | M | <1d |
| 35 | Collapse broker_next_step on customer result | 4 | M | <1d |
| 36 | Merge boundary hint triple into one line | 3 | S | <1h |
| 37 | Remove tab suffix micro-copy (customer tabs) | 3 | S | <1h |
| 38 | 上传材料 → copy fix 「描述您要补的材料」 | 4 | S | <1h |
| 39 | Empty placeholder: stop saying "don't use for add-car" | 5 | S | <1h |
| 40 | Collapse structured snapshot post-handoff default | 4 | M | <1d |
| 41 | Remove portalProgressNote annotation | 2 | S | <1h |
| 42 | Thread bubble role labels hidden | 3 | S | <1h |
| 43 | Alert stack limit: max 1 above input | 4 | M | <1d |
| 44 | customer toast: 已整理成 case → 已收到 | 3 | S | <1h |
| 45 | Resume hint promoted when single in-progress | 3 | M | <1d |
| 46 | My requests: hide 刷新 (auto on tab focus) | 2 | M | <1d |
| 47 | Post-handoff append: link not collapse panel | 3 | M | <1d |
| 48 | Remove duplicate broker_next_step (add-car handoff) | 3 | S | <1h |
| 49 | English field labels in examples → Chinese | 2 | S | <1h |
| 50 | Print-friendly confirmation (customer receipt) | 1 | L | <1wk |

---

## ROI × Effort Matrix (Top 15)

```
High ROI │ #11 #12 #13 #21 #22 #23 #1 #2 #15 #19
         │ #9 #25 #3
         ├──────────────────────────────────────
Med ROI  │ #24 #27 #30 #16 #20
         │
Low ROI  │ #50 #46 #41
         └──────────────────────────────────────
           S (<1h)      M (<1d)       L (<1wk)
```

**Recommended sprint order:** 1 → 2 → 9 → 3 → 11 → 12 → 13 → 15 → 19 → 21

---

## Expected Cumulative Impact

| Milestone | UI reduction | 5s landing score | Overall customer |
|-----------|--------------|------------------|----------------|
| Current | — | 33 | **~50** |
| After top 10 (<1h) | −25% landing | 55 | **~58** |
| After top 20 (<1d) | −40% landing | 70 | **~68** |
| After top 30 (<1wk) | −45% all screens | 78 | **~76** |

**75+ target achieved at:** Top 20–25 implemented (message-first + one primary + handoff merge + separate URL)

---

## P16-M vs P16-N Overlap

| P16-M item | P16-N customer priority |
|------------|------------------------|
| #9 Demote 联系人工 | ✅ #2 |
| #17 Customer empty single primary | ✅ #13 |
| #18 Remove UTC footnote | ✅ #5 |
| #27 Post-handoff single result card | ✅ #18 |
| #23 Customer separate route | ✅ #19 |
| #40 Remove 场景仿真 | ✅ #4 |
| #46 Remove AddCarFlowExplanation | ✅ #6 |

P16-N adds **message-first reorder** (#11, #21) as the customer-specific unlock P16-M implied but didn't fully specify.

---

*End of P16-N Phase 9 — Top 50 Customer Improvements*
