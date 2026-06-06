# P16-H Phase 6 — Top 50 UI Deletions

**Date:** 2026-05-31  
**Rule:** No new features. Only hide, collapse, remove, defer.  
**Ranked by:** ROI vs Risk (Higher ROI + Lower Risk first)  
**Constraint:** Maps to existing Capabilities 1 and 4 only

---

## Ranking Key

| ROI | Meaning |
|-----|---------|
| **Critical** | Directly fixes Day 1 abandonment or 10-second fail |
| **High** | Saves broker minutes or reduces training |
| **Medium** | Polish; trial Week 2 |
| **Low** | Nice-to-have |

| Risk | Meaning |
|------|---------|
| **Low** | CSS/copy/conditional hide; easy rollback |
| **Medium** | Behavior change; needs dry-run |
| **High** | Breaks dev workflow or customer portal GTM |

---

## TOP 50 (Ranked)

| Rank | Deletion | Action | ROI | Risk | Cap |
|------|----------|--------|-----|------|-----|
| 1 | Tab suffix subtitles on both tabs | Remove secondary text from tab labels | Critical | Low | 1 |
| 2 | `portal_brand_tagline` Add-Car wording in header | Replace with cancellation-first one-liner in ui_copy | Critical | Low | 1 |
| 3 | **客户报送 tab** in product_only trial | Hide tab entirely | Critical | Low | 1 |
| 4 | **练习场景** card on workbench | Merge into demo queue or remove | High | Low | 1 |
| 5 | Duplicate trust subtitles (3 lines saying manual paste) | Keep one line | High | Low | 1 |
| 6 | **返回工作台** link in unified-intake header | Hide in product_only | High | Low | 1 |
| 7 | English **"Case 整理明细"** title | Rename or remove | High | Low | 3 |
| 8 | **复制摘要** button on case detail (trial) | Hide; keep draft copy only | High | Low | 3 |
| 9 | Status **radio group** on case detail default view | Move to ⋮ overflow menu | High | Medium | 5 |
| 10 | **Case 整理明细** card default expanded | Collapse by default; glance summary sufficient | High | Low | 3 |
| 11 | Nested collapse「更多状态标签」 | Hide in product_only | High | Low | 3 |
| 12 | **IntakeFlowStepTrack** on customer empty state | Hide until after first message | Critical | Medium | 4 |
| 13 | Customer empty headline「建议从加车报价开始」 | Replace with message-first copy | Critical | Low | 4 |
| 14 | **6 category buttons** on customer empty state | Hide; show after triage or in dropdown | Critical | Medium | 4 |
| 15 | **加车报价 · 结构化报送** collapse on empty state | Defer until user clicks optional link | High | Medium | 4 |
| 16 | Numbered ①②③ instructions on customer entry | Remove | High | Low | 4 |
| 17 | **Add-car transaction banner** (blue gradient card) | Show only when add-car active post-triage | Medium | Low | 4 |
| 18 | **显示产品说明** link after intro collapsed | Remove; intro never re-expands in trial | Medium | Low | 1 |
| 19 | Pilot intro **Tag wall** (做/不做 tags) | Collapse to one trust line permanently | Medium | Low | 1 |
| 20 | Left **快速体验** card above paste on first visit | Move below paste or right column only | High | Medium | 1 |
| 21 | Queue card extra「与客户报送同源」 | Remove | Medium | Low | 5 |
| 22 | Section split「立即处理」vs「等待或暂存」 | Single sorted list for trial | Medium | Medium | 5 |
| 23 | Per-card **tag explosion** on queue rows | Show urgency + 1 preview line only | High | Medium | 5 |
| 24 | **Pagination** when total ≤50 | Hide simple pager in trial | Low | Low | 5 |
| 25 | **服务记录编号** hint block about customer portal | Remove hint; keep ID copyable small | Medium | Low | 3 |
| 26 | **Follow-up CRM block** (waiting_on + date + notes) | Defer to Week 2 trial | High | Medium | 5 |
| 27 | **Append follow-up** buried — not deletion but promote | *(promote, not delete — skip)* | — | — | — |
| 28 | **AddCarFlowExplanation** panels on customer portal | Hide in product_only | Medium | Low | 4 |
| 29 | **WeChat identity binding** strip | Hide in trial | Medium | Low | 4 |
| 30 | **Resume portal hint** (继续上次申请) | Hide until customer portal GTM | Low | Low | 4 |
| 31 | **Scenario simulation** text button on customer hero | Already hidden in product_only ✅ | — | — | — |
| 32 | **我的办理** tab | Already hidden in product_only ✅ | — | — | — |
| 33 | Engineer filters (镜像异常/测试/正式) | Already hidden in product_only ✅ | — | — | — |
| 34 | PG mirror tags | Already hidden in product_only ✅ | — | — | — |
| 35 | **Dark KPI header** on unified-intake | Use minimal white header | Medium | Medium | 1 |
| 36 | **founderQueueLoadedCount** tag (N/13 条示例已就绪) | Hide after first load | Low | Low | 1 |
| 37 | **Current-open anchor** box in queue when case selected | Remove duplicate of selection highlight | Medium | Low | 5 |
| 38 | **续接此处** + **最近更新** duplicate boxes | Merge to one | Medium | Low | 3 |
| 39 | Add-car **submission snapshot** collapse on workbench | Hide for non-add-car; collapse for add-car | Medium | Low | 3 |
| 40 | **Conversation thread** collapse labels | Collapse default closed | Medium | Low | 3 |
| 41 | **Attachment upload** on workbench case detail | Defer v1 | Low | Medium | 4 |
| 42 | **Note field** on case detail | Defer to Week 2 | Medium | Low | 5 |
| 43 | Customer **bubble thread UI** pre-handoff | Collapse; show result card only | High | Medium | 4 |
| 44 | **portal_post_handoff** timing truth notes (UTC) | Hide from customer; broker-only if needed | Medium | Low | 4 |
| 45 | **Record summary rail** 7 sections | Collapse to 3 lines on customer portal | Medium | Medium | 4 |
| 46 | **Light identity WeChat modal** | Remove from trial surfaces | Low | Low | 4 |
| 47 | **English document.title** patterns with Add-Car | Align titles to 办公室工作台 | Medium | Low | 1 |
| 48 | **Sidebar "Unified Intake"** English label | Rename 客户统一受理 only | Low | Low | 1 |
| 49 | **Demo vs real** visual distinction | Remove demo tag noise; one queue | Low | Medium | 5 |
| 50 | **Multiple loading messages** (card + spin + toast) | Single loading line | Medium | Low | 4 |

---

## ROI vs Risk Matrix (Clusters)

```
High ROI + Low Risk (DO FIRST — 15 items)
├── #1–8, #13, #16, #19, #21
│
High ROI + Medium Risk (DO BEFORE CHEN KUI — 10 items)
├── #3, #9, #12, #14, #15, #20, #22, #23, #26, #43
│
Medium ROI + Low Risk (WEEK 2 — 12 items)
├── #5, #10, #11, #17, #18, #25, #28, #29, #37, #38, #39, #50
│
Low ROI or High Risk (DEFER — remainder)
├── #24, #30, #35, #41, #46, #49
```

---

## Estimated Surface Reduction

| Metric | Current (visible) | After Top 20 deletions |
|--------|-------------------|------------------------|
| Focal points (workbench landing) | 7 | 3 |
| Focal points (customer empty) | 9+ | 2 (if tab kept) / 0 (if hidden) |
| Focal points (case detail) | 10+ | 4 |
| Clicks to copy draft | 2 | 1 |
| Decisions before first paste | 4 | 1 |
| **Estimated UI removable** | — | **~35–40% of visible chrome** |

---

## Must NOT Delete (Trial-Critical)

- Wayfinding banner「经纪人：请在本页粘贴客户消息」
- Paste textarea + 开始整理
- 加载演示队列 (Day 0 training)
- 复制客户草稿
- 不自动发送 trust line (somewhere visible)
- Inline practice seed texts (can merge UI, not remove mechanism)
- Urgency tags on cases
- OfficeWorkbenchOneGlanceSummary (broker moat)

---

*End of P16-H Phase 6 — Top 50 UI Deletions*
