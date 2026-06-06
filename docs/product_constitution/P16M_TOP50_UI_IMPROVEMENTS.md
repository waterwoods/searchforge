# P16-M Phase 9 — Top 50 UI Improvements

**Date:** 2026-06-01  
**Constraints:** UI/copy/layout only — no features, no business logic, no Constitution edits  
**Ranked by:** ROI (1–5) · Effort (S/M/L) · Risk (Low/Med/High)

---

## Top 10 — Under 1 Hour Each

| # | Improvement | ROI | Effort | Risk | Screen |
|---|-------------|-----|--------|------|--------|
| 1 | Merge trust into one line (remove subtitle duplicate) | 5 | S | Low | Broker |
| 2 | Demote 快速体验 to link under empty textarea | 5 | S | Low | Broker |
| 3 | Wayfinding Alert → single line, no description body | 4 | S | Low | Broker |
| 4 | Remove label "粘贴您收到的客户消息" | 4 | S | Low | Broker |
| 5 | Remove 整理结果 sub-caption paragraph | 4 | S | Low | Case |
| 6 | Hide dark header title when brand card shows same | 4 | S | Low | Global |
| 7 | product_only: hide queue section when empty | 4 | S | Low | Broker |
| 8 | Tab suffix text removal (full UI) | 3 | S | Low | Global |
| 9 | Customer: demote 联系人工 to outline button | 4 | S | Low | Customer |
| 10 | Post-handoff one-line CTA ("请等待办公室联系…") | 4 | S | Low | Customer |

**Batch impact:** ~25% empty-state noise reduction in <1 day total.

---

## Top 10 — Under 1 Day Each

| # | Improvement | ROI | Effort | Risk | Screen |
|---|-------------|-----|--------|------|--------|
| 11 | Collapse paste card when case open → "整理新消息" link | 5 | M | Low | Broker |
| 12 | Auto-open cancellation case after demo queue completes | 5 | M | Med | Broker |
| 13 | Flatten glance card (remove gradient, one accent border) | 4 | M | Low | Case |
| 14 | Sticky 复制客户草稿 on scroll | 4 | M | Low | Case |
| 15 | Queue row product_only: urgency + preview only (already mostly done — enforce max 2 tags) | 4 | M | Low | Broker |
| 16 | Empty paste state: 3-step bullets (粘贴→整理→复制) | 4 | M | Low | Broker |
| 17 | Customer empty: single primary 办理加车报价 full-width; others row below | 5 | M | Med | Customer |
| 18 | Remove customer UTC timing footnote from default view | 3 | M | Low | Customer |
| 19 | Disable 开始整理 → tooltip "请先清空或打开新消息" | 4 | M | Low | Broker |
| 20 | Merge app title into brand card; hide dark header product_only | 4 | M | Low | Global |

---

## Top 10 — Under 1 Week Each

| # | Improvement | ROI | Effort | Risk | Screen |
|---|-------------|-----|--------|------|--------|
| 21 | Visual success state after copy draft (toast + check) | 4 | L | Low | Case |
| 22 | Empty state illustration/mock draft snippet | 4 | L | Low | Broker |
| 23 | Customer portal on separate route; remove tab from trial URL | 5 | L | Med | Global |
| 24 | Responsive: paste above fold at 768px height | 4 | L | Med | Broker |
| 25 | Unified typography scale (reduce 11px/12px soup) | 3 | L | Low | All |
| 26 | Icon-only 刷新/清空 with tooltips | 3 | L | Low | Broker |
| 27 | Customer post-handoff: single result card, hide progress card | 4 | L | Med | Customer |
| 28 | Append follow-up promoted in glance when reopened | 4 | L | Low | Case |
| 29 | Follow-up block collapsed product_only with "展开跟进" | 3 | L | Low | Case dev |
| 30 | Spacing pass: 14px→16px rhythm, reduce nested cards | 3 | L | Low | All |

---

## Next 20 (31–50) — Backlog by ROI

| # | Improvement | ROI | Effort | Bucket |
|---|-------------|-----|--------|--------|
| 31 | Remove ①②③ numbering in glance | 3 | S | <1h |
| 32 | Practice scenarios → links not buttons | 3 | S | <1h |
| 33 | Hide 状态 in kebab until Day-7 | 2 | S | <1h |
| 34 | Customer: hide step track until first submit | 3 | M | <1d |
| 35 | Remove bubble tags in customer thread | 3 | M | <1d |
| 36 | Collapse structured add-car by default (verify) | 3 | S | <1h |
| 37 | English "case" strings → 服务记录 in dev UI | 2 | M | <1d |
| 38 | queue: icon badge for due today vs text tag | 3 | M | <1d |
| 39 | Loading skeleton in result area not spinner card | 3 | M | <1d |
| 40 | Remove 场景仿真 from customer hero | 4 | S | <1h |
| 41 | Pilot intro → one sentence + link "了解更多" | 3 | M | <1d |
| 42 | Case detail: single border color system | 2 | L | <1wk |
| 43 | Mobile paste textarea min-height tap target | 3 | L | <1wk |
| 44 | Customer result: hide thread by default (verify) | 3 | S | <1h |
| 45 | Demo progress in button label not separate text | 3 | M | <1d |
| 46 | Remove AddCarFlowExplanation component from render | 3 | S | <1h |
| 47 | Identity strip hidden until handoff | 2 | M | <1d |
| 48 | Footer trust: single grey line at page bottom | 3 | M | <1d |
| 49 | Keyboard: Cmd+V focus textarea on load | 3 | M | <1d |
| 50 | Print stylesheet for case glance (broker ask) | 1 | L | <1wk |

---

## ROI × Effort Matrix (Top 15)

```
High ROI │ #2 #11 #17 #23 #1 #3 #12
         │ #14 #16 #9
         ├─────────────────────────
Med ROI  │ #21 #24 #27 #13
         │
Low ROI  │ #50 #42
         └─────────────────────────
           S (<1h)    M (<1d)    L (<1wk)
```

**Recommended sprint order:** 1 → 2 → 3 → 11 → 12 → 17 → 13 → 14 → 23

---

## Expected Cumulative Impact

| Milestone | UI element reduction | 10s broker score | Stripe score |
|-----------|---------------------|------------------|--------------|
| After top 10 (<1h) | −20% empty state | 83 → 88 | 75 → 78 |
| After top 20 (<1d) | −35% | 88 → 92 | 78 → 82 |
| After top 30 (<1wk) | −45% | 92 → 95 | 82 → 85 |

---

*End of P16-M Top 50 UI Improvements*
