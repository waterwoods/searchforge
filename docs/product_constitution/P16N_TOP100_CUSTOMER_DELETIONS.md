# P16-N Phase 4 — Top 100 Customer Deletions

**Date:** 2026-06-01  
**Goal:** Reduce visible customer UI by **40%** (from ~16–18 empty-state objects → ~8–10)  
**Classification:** Delete · Hide · Collapse · Move later · Keep  
**Constraint:** No capability removal — UI/copy/layout visibility only

---

## Scoring Key

| Class | Meaning |
|-------|---------|
| **Delete** | Remove from customer render entirely |
| **Hide** | Not shown by default; customer path never needs it |
| **Collapse** | Default closed; progressive disclosure |
| **Move later** | Show after first submit or handoff |
| **Keep** | Visible on first viewport |

---

## A. Landing / Empty State (Items 1–25)

| # | Element | Class | Rationale |
|---|---------|-------|-----------|
| 1 | Tab suffix — 报送入口（加车优先） | **Delete** | Engineer scope note |
| 2 | Tab suffix — 进行中的请求与待补充项 | **Delete** | Redundant with tab label |
| 3 | Dark header duplicate app title | **Hide** | Merge into brand card |
| 4 | portalServiceTagline full paragraph | **Delete** | Replace with one trust line |
| 5 | IntakeFlowStepTrack (3 steps) | **Move later** | After first message only |
| 6 | portalEmptyHeadline — 建议从加车报价开始 | **Delete** | Replace message-first headline |
| 7 | portalEmptySecondary — ①②③ numbered steps | **Delete** | Typeform never numbers paths |
| 8 | portalChoosePathLabel — 办理类型 | **Delete** | No category picker in Typeform |
| 9 | Button 联系人工 (equal primary) | **Hide** | Footer link: 「需要人工？」 |
| 10 | 推荐主路径 badge on add-car button | **Delete** | Obvious if single path |
| 11 | Button 办理加车报价 (standalone) | **Move later** | Becomes example chip, not button |
| 12 | Button 其他事项 dropdown | **Collapse** | 「更多类型」link after first line |
| 13 | Collapse header 加车报价·结构化报送 | **Hide** | Link: 「结构化填写加车信息」 |
| 14 | portalAddCarQuickHint paragraph | **Delete** | Redundant with link |
| 15 | 5 structured input fields (empty state) | **Hide** | Behind explicit opt-in |
| 16 | Button 用以上内容发起加车报送 | **Hide** | With structured panel |
| 17 | Textarea de-emphasized placeholder | **Keep** | Becomes hero — flip hierarchy |
| 18 | Instruction 可先点选办理类型… | **Delete** | Wrong for message-first |
| 19 | 场景仿真 text button | **Delete** | Zero customer value |
| 20 | Resume multi-case block | **Keep** | Rare but high value |
| 21 | Resume single-case link | **Keep** | High value |
| 22 | Hero H2 icon + long product name | **Keep** | Shorten title 50% |
| 23 | Nested grey hero card | **Delete** | Flatten — one white surface |
| 24 | Brand card tagline (office paste wording) | **Hide** | Customer-specific copy only |
| 25 | Pilot intro Alert (full UI) | **Hide** | Customer never needs broker scope essay |

**Empty-state reduction:** 25 items → ~8 visible = **−68%** on aggressive plan; **−40%** with balanced plan (keep hero, textarea, send, trust, resume)

---

## B. Mid-Flow / Active (Items 26–50)

| # | Element | Class | Rationale |
|---|---------|-------|-----------|
| 26 | Add-car transaction gradient banner | **Delete** | Redundant with progress card title |
| 27 | portal_thread_heading when add-car pre-handoff | **Collapse** | Already collapsed ✓ — verify default |
| 28 | Bubble label 您的报送 / 办公室整理回复 | **Hide** | Chat pattern obvious |
| 29 | Urgency tag on bubbles | **Hide** | Customer doesn't need orange tags |
| 30 | Lifecycle tag on bubbles | **Hide** | In progress card already |
| 31 | follow_up_type tag on bubbles | **Delete** | Engineer metadata |
| 32 | human_confirmation_required tag | **Hide** | Move to result card if needed |
| 33 | Monospace case ID (pre-handoff) | **Collapse** | 「参考编号」copy-on-click |
| 34 | 当前请求与类型 section in progress card | **Collapse** | Category inferrable |
| 35 | quote_ready_status tag (non-add-car) | **Hide** | Jargon |
| 36 | collected_fields tag wall (>3) | **Collapse** | Show count + expand |
| 37 | still_needed_fields tag wall | **Keep** | Actionable — but max 3 visible |
| 38 | AddCarRecordSummaryRail — 为什么在这一步 | **Collapse** | Default closed |
| 39 | Record rail — 完成条件 section | **Collapse** | Default closed |
| 40 | Record rail — 下一步谁负责 · 两条路径 | **Collapse** | One line in card header |
| 41 | Record rail — understood version lead | **Delete** | Meta-commentary |
| 42 | Record rail — timing section | **Delete** | Customer doesn't need UTC logic |
| 43 | Intent tag 加车报价 closable | **Hide** | Lane obvious from context |
| 44 | Intent tag hint （与本次加车无关…） | **Delete** | Post-handoff only |
| 45 | showAddCarPreSubmitGapAlert full description | **Collapse** | Title only + field chips |
| 46 | showAddCarHandoffPendingGapAlert | **Merge** | One alert max |
| 47 | contactOnlyHandoffGap Alert | **Keep** | But merge with #46 |
| 48 | completion_message success Alert | **Keep** | Short |
| 49 | 不确定如何描述？查看示例 | **Move later** | Inline in placeholder |
| 50 | Example link list card | **Collapse** | 3 examples in placeholder |

---

## C. Handoff Pending (Items 51–60)

| # | Element | Class | Rationale |
|---|---------|-------|-----------|
| 51 | portal_handoff_pending_alert_title | **Keep** | Shorten to one line |
| 52 | portalHandoffPendingCtaHint paragraph | **Delete** | Merge into alert |
| 53 | portal_handoff_pending_button_subline | **Delete** | Tooltip on button |
| 54 | Light identity strip (3 links) | **Hide** | Move to account settings later |
| 55 | Light identity phone/email hint | **Hide** | With strip |
| 56 | WeChat modal | **Hide** | Not v1 customer |
| 57 | Empty formal submit line auto-text | **Keep** | Backend — invisible OK |
| 58 | Dual placeholder for handoff pending | **Delete** | One placeholder |
| 59 | Identity strip dismiss persistence | **Hide** | Remove strip entirely |
| 60 | Button label 确认提交，开始报价处理 | **Keep** | Shorten copy |

---

## D. Post-Handoff Result (Items 61–85)

| # | Element | Class | Rationale |
|---|---------|-------|-----------|
| 61 | AddCarFlowExplanation component | **Delete** | P16-M #46 — education overload |
| 62 | addCarResultEyebrow + hint | **Delete** | Headline sufficient |
| 63 | portalSubmittedAtTimingTruthNote (UTC) | **Delete** | Engineer footnote |
| 64 | formal + activity timestamp dual block | **Collapse** | Show one date; expand for detail |
| 65 | portalSubmittedAtCreatedPrefix line | **Hide** | Rarely differs |
| 66 | Structured snapshot panel title + intro | **Collapse** | Default closed — 「查看整理详情」 |
| 67 | handoff_verify_with_office_note | **Collapse** | Inside snapshot |
| 68 | quote_ready_status in snapshot | **Hide** | Internal |
| 69 | AddCarHandoffGroupedSnapshot full | **Collapse** | Summary one-liner visible |
| 70 | Duplicate broker_next_step (add-car) | **Delete** | One block only |
| 71 | portalPostHandoffNextSectionLabel divider | **Delete** | Merge into headline |
| 72 | processingLine paragraph | **Keep** | One sentence |
| 73 | handoff_office_followup_timing Alert | **Collapse** | Link 「预计多久？」 |
| 74 | clientPrep Alert 您可准备 | **Collapse** | Optional |
| 75 | portalPostHandoffClosureSectionLabel divider | **Delete** | |
| 76 | portalClosureSummaryLabel eyebrow | **Delete** | |
| 77 | Full office reply Paragraph in green box | **Keep** | Core outcome |
| 78 | caseFollowLine | **Keep** | |
| 79 | Append collapse panel | **Keep** | Default collapsed ✓ |
| 80 | postHandoffBoundaryBlocked Alert | **Keep** | Error state |
| 81 | 本条记录 vs 新事项 heading + essay | **Delete** | One line in boundaryHint |
| 82 | addCarBoundaryHint full paragraph | **Collapse** | Link |
| 83 | boundaryHint duplicate | **Delete** | Merge #81–82 |
| 84 | Button 查看工作台 | **Delete** | Customer must not see broker UI |
| 85 | Button 提交新问题 | **Keep** | Secondary outline |

---

## E. My Requests Tab (Items 86–95)

| # | Element | Class | Rationale |
|---|---------|-------|-----------|
| 86 | Hero subtitle paragraph | **Delete** | One line |
| 87 | 共 N 条 count | **Hide** | Footer |
| 88 | Updated timestamp on list row | **Collapse** | Show on select only |
| 89 | Formal + updated in detail (both) | **Keep** | Simplify labels |
| 90 | Field chip groups (collected) | **Collapse** | Show count |
| 91 | Field chip groups (missing) | **Keep** | Max 4 tags |
| 92 | Gradient next-step panel | **Keep** | Good pattern |
| 93 | 刷新 button | **Hide** | Auto-refresh on tab focus |
| 94 | Empty → long hint | **Keep** | Shorten 30% |
| 95 | Two-column layout mobile | **Keep** | Stack OK |

---

## F. Global / Cross-Cutting (Items 96–100)

| # | Element | Class | Rationale |
|---|---------|-------|-----------|
| 96 | 办公室工作台 tab (customer URL) | **Hide** | Separate routes |
| 97 | 场景仿真 tab | **Hide** | Lab only |
| 98 | English "case" in any customer string | **Delete** | 服务记录 |
| 99 | Toast 已整理成 case | **Delete** | Customer-facing toast copy |
| 100 | Error Alert full API detail | **Collapse** | Friendly message only |

---

## Reduction Summary

| Surface | Current objects | After balanced purge | After aggressive | Target |
|---------|----------------|---------------------|------------------|--------|
| Landing empty | 16–18 | 10–11 (−38%) | 7–8 (−55%) | −40% |
| Add-car mid-flow | 25–35 | 14–18 (−45%) | 10–14 | −40% |
| Post-handoff | 18–24 | 10–12 (−45%) | 8–10 | −40% |
| My requests detail | 12–16 | 8–10 (−35%) | 7–9 | −35% |

**Balanced plan:** Delete/Hide 42 · Collapse 28 · Move later 8 · Keep 22

---

## Top 20 Deletes by Customer Impact

1. Empty-state three-button row  
2. ①②③ secondary instructions  
3. Flow step track before first action  
4. Long portalServiceTagline  
5. AddCarFlowExplanation post-handoff  
6. UTC timing truth footnote  
7. 查看工作台 button  
8. 场景仿真 link  
9. Transaction gradient banner  
10. Bubble micro-tags  
11. Record rail meta-sections (why here, completion, two paths)  
12. Duplicate broker_next_step  
13. Light identity strip  
14. 办理类型 label  
15. 推荐主路径 badge  
16. Structured form visible header (empty state)  
17. Tab suffix micro-copy  
18. Boundary hint essay (triple)  
19. Category-before-message instruction line  
20. Engineer toast "case"

---

*End of P16-N Phase 4 — Top 100 Customer Deletions*
