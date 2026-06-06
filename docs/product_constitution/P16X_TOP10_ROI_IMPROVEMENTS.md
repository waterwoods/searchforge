# P16-X Phase 9 — Top 10 Highest ROI Improvements

**Date:** 2026-06-01  
**Constraints:** No architecture · No new capability · No platform work · UI/copy/layout only  
**Goal:** Make users **naturally continue after first submit**  
**Ranked by:** Probability × Impact ÷ Effort

---

## Rules applied

- Improvements are **deletions, promotions, copy, and layout** — not new systems  
- Each must address F-001 / F-002 class frictions from P16X_TOP50_FRICTIONS.md  
- No Constitution edits

---

## Top 10

| Rank | Improvement | Friction IDs | Effort | Expected effect |
|------|-------------|--------------|--------|-----------------|
| **1** | **One-line post-triage continuation copy** directly under 复制客户草稿: 「下一步：复制后发微信 → 客户回复后在本页下方队列点开本条 → 追加补充」 | F-001, F-002 | S | Bridges Turn 1 → Turn 2 without training |
| **2** | **Promote 追加客户补充 on first persist** — show append card whenever `case_id` exists, not only `caseView === reopened` | F-002, F-004 | S | Fixes lifecycle without new API |
| **3** | **Auto-scroll to case detail** after triage completes | F-006 | S | User sees draft without hunt |
| **4** | **Copy toast with continuation hint** —「已复制 — 发送后等客户回复，从队列打开继续」 | F-001, F-022 | S | Reinforces habit at moment of exit |
| **5** | **Chinese-only glance for product_only** — hide or translate English `broker_next_step` and queue preview strings | F-005, F-041 | M | Trust for Chen Kui |
| **6** | **Collapse/hide 快速体验 block when `currentCase` exists** | F-012, F-010 | S | Reduces noise after first success |
| **7** | **Replace top paste hint after first case** — swap「继续粘贴下一条」for「整理新消息请先点清空」vs append card (mutually exclusive copy) | F-004, F-021 | S | Removes fork-case ambiguity |
| **8** | **Promote 状态 to visible pill** after copy (e.g. show current status +「改为等客户」as text link, not kebab) | F-008, F-009 | M | Makes waiting state legible |
| **9** | **Queue row: show Chinese 下一步 snippet only** (product_only max 1 line) | F-005, F-017 | M | Monday-morning scan |
| **10** | **Sticky 复制客户草稿 on scroll** (P16-M #14) | F-006, F-019 | M | Keeps primary action visible during read |

---

## Detail — #1 (highest ROI)

**Problem:** User copies draft → switches app → never learns queue reopen path.  
**Fix:** Single sentence, no new UI region — placed adjacent to copy button.  
**ROI rationale:** Addresses P×I=25 friction with ~15 min copy change.

---

## Detail — #2 (second highest ROI)

**Problem:** Append exists in code (`caseView === reopened'`) but not after fresh triage despite persisted `case_id`.  
**Fix:** Render same append card when `currentCase.case_id` is set.  
**ROI rationale:** Unlocks multi-turn without backend change — directly raises Cap 5 follow-up score.

---

## Explicitly NOT in top 10 (scope guard)

| Idea | Why excluded |
|------|--------------|
| Customer portal route | New surface / capability |
| Push notifications | Platform work |
| Stripe / billing UI | Cap 6 docs, not continuation |
| CRM fields | Constitution Must Not Build |
| Work now/Waiting split rebuild | Architecture |
| Mobile app | Platform |

---

## Expected score impact (if all 10 shipped)

| Metric | Before | After (est.) |
|--------|--------|--------------|
| Cap 5 Lifecycle | 53 | **62–65** |
| Cap 6 Trial (Day 1–7 stickiness) | 51 | **58–62** |
| F-001 probability | 5 | **3** |
| Chen Kui continue-after-first-draft | 52 | **68** |

---

## Recommended ship order

```
Day 1 (<2h):  #1 → #3 → #4 → #6 → #7
Day 2 (<1d):  #2 → #5
Day 3 (<1d):  #8 → #9 → #10
```

---

*End of P16-X Phase 9 — Top 10 ROI Improvements*
