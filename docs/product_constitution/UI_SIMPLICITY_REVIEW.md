# P16-H Phase 2 — UI Simplicity Review

**Date:** 2026-05-31  
**Scope:** Every visible page in product_only trial build  
**Method:** Component audit (`UnifiedIntakePage`, `BrokerWorkbenchTab`, `CustomerEntryTab`, `AppLayout`), P16-C visual checklist, local `:5173` bundle  
**Constraint:** Evaluation only

---

## Overall Simplicity Score: **58 / 100**

| Screen | Score | Primary blocker |
|--------|-------|-----------------|
| Global chrome (header + tabs) | 62 | Add-Car copy; dual tabs |
| Customer Intake (客户报送) | 42 | Category-first; 8+ focal points |
| Broker Workbench (landing) | 68 | Sprint A wins; still 5 layers before paste |
| Broker Workbench (queue) | 55 | Dense cards; hidden until populated |
| Case Detail | 48 | English labels; nested collapses; dual copy CTAs |
| Empty states | 60 | Helpful hints but wordy |

Target for Chen Kui unsupervised Day 1: **≥75**. Gap: **17 points**.

---

## Screen 1 — Global Chrome (Header + Tabs)

### 1. ONE primary action?
**No.** Two competing tabs (客户报送 / 办公室工作台) plus collapsed「显示产品说明」.

### 2. More than one primary?
**Yes.** Tab bar presents two equal-weight entry points with long suffix subtitles.

### 3. Visual focal points (count)
| # | Element |
|---|---------|
| 1 | Chen Kui avatar + team name |
| 2 | Tagline「加车报价为当前旗舰流程」 |
| 3 | Tab: 客户报送 + suffix |
| 4 | Tab: 办公室工作台 + suffix |
| 5 |「显示产品说明」link |
| **Total: 5** | Target: ≤2 |

### 4. Delete immediately
- Tab suffix secondary text (`— 报送入口（加车优先）`, `— 加车旗舰路径…`)
- `portal_brand_tagline` Add-Car wording in header
-「显示产品说明」link (replace with one-time tooltip or remove)

### 5. What Stripe would remove
Stripe would remove the **second tab entirely** for broker trial — one product, one entry. Tagline would be one line: "Paste customer messages → review draft → send."

### 6. What Linear would remove
Linear would remove **avatar block** from product surface (belongs in settings/branding), collapse tab labels to single words without suffixes.

### 7. What Notion would remove
Notion would remove **pilot intro alert** entirely after first visit — no「做/不做」tag wall.

---

## Screen 2 — Customer Intake (客户报送)

### 1. ONE primary action?
**No.** Primary is split:「办理加车报价」button, structured form collapse, free-text input, and 6 category buttons in dropdown.

### 2. More than one primary?
**Yes — at least 4:** Add-car CTA, 联系人工, 其他事项 dropdown, structured form, message input.

### 3. Visual focal points (count)
| # | Element |
|---|---------|
| 1 | Hero title「加车报价 · 客户统一报送」 |
| 2 | Service tagline (3 sentences) |
| 3 | IntakeFlowStepTrack (3 steps) |
| 4 | Empty headline + secondary (numbered ①②③) |
| 5 |「办理加车报价」primary button + badge |
| 6 |「联系人工」button |
| 7 |「其他事项」dropdown |
| 8 | Structured add-car collapse (5 fields) |
| 9 | Message textarea |
| **Total: 9+** | Catastrophic for 10-second test |

### 4. Delete immediately
- IntakeFlowStepTrack on empty state
-「建议从加车报价开始」headline (contradicts cancellation wedge)
- Structured form collapse (defer to post-handoff or broker paste)
- Numbered ①②③ instructions
- Add-car transaction banner (when active)

### 5. Stripe would remove
Everything except: **one headline**, **one textarea**, **one Submit button**. Categories revealed after first message.

### 6. Linear would remove
**All buttons except one input.** Linear's issue create is: type → enter. No category grid.

### 7. Notion would remove
**Flow track**, **status strips**, **bubble thread UI** — replace with single page block.

### Simplicity score: **42 / 100**

---

## Screen 3 — Broker Workbench (Landing / Paste)

### 1. ONE primary action?
**Almost.** Paste +「开始整理」is primary — but **加载演示队列** competes in left column.

### 2. More than one primary?
**Yes on Day 0:** Demo queue (left) vs paste (right) vs practice scenario buttons.

### 3. Visual focal points (count)
| # | Element |
|---|---------|
| 1 | Left: 快速体验 card + 加载演示队列 |
| 2 | Left: empty queue / loading spinner |
| 3 | Right: Title + subtitle (2 lines) |
| 4 | Wayfinding Alert |
| 5 | 练习场景 card (3 buttons) |
| 6 | Paste card + textarea |
| 7 | 开始整理 button |
| **Total: 7** | Target: ≤3 |

### 4. Delete immediately
- Merge **练习场景** into demo queue card (one "Try it" section)
- Remove duplicate subtitle lines (3 trust lines saying same thing)
- Demote left column below paste on first visit (queue second)

### 5. Stripe would remove
Left column on empty state — **paste is the whole page** until first case exists. Demo = one link, not a card.

### 6. Linear would remove
**练习场景** card — replace with command-K style quick actions or remove entirely for trial.

### 7. Notion would remove
Section titles on every card — use whitespace hierarchy instead of 4 bordered cards.

### Simplicity score: **68 / 100**

---

## Screen 4 — Queue (服务记录队列)

### 1. ONE primary action?
**Open a case** — but only after cases exist. Empty state competes with paste on right.

### 2. More than one primary?
**When populated:** Filter segmented control + case cards + pagination each demand attention.

### 3. Visual focal points (count)
| # | Element |
|---|---------|
| 1 | Card title + extra「与客户报送同源」 |
| 2 | Filter: 全部 / 需今天处理 / 24小时内 |
| 3 |「立即处理」section header |
| 4 | Case cards (×N) — each with 6–8 tags |
| 5 |「等待或暂存」section |
| 6 | Pagination |
| 7 | Current-open anchor box |
| **Total: 6+** per view |

### 4. Delete immediately
-「与客户报送同源」extra on card title
- Section split「立即处理」vs「等待或暂存」for trial (single sorted list)
- Per-card tag explosion (show urgency + one-line preview only)
- Pagination on trial (≤13 demo cases)

### 5. Stripe would remove
Filters until &gt;20 items. Cards would show: **urgency dot**, **one line**, **click**.

### 6. Linear would remove
**All tags on list rows** — detail view only.

### 7. Notion would remove
Section headers — use sort order only.

### Simplicity score: **55 / 100**

---

## Screen 5 — Case Detail

### 1. ONE primary action?
**Should be:** Copy draft. **Actually:** Competes with copy summary, status radio, follow-up form, append paste, collapses.

### 2. More than one primary?
**Yes — 5+:** 复制客户草稿, 复制摘要, status radio, 追加客户补充, 更新跟进.

### 3. Visual focal points (count)
| # | Element |
|---|---------|
| 1 | Title row: urgency + status + due tags |
| 2 | Status radio group |
| 3 | 复制摘要 + 复制客户草稿 |
| 4 | 服务记录编号 block |
| 5 | OfficeWorkbenchOneGlanceSummary |
| 6 | Case 整理明细 card (large) |
| 7 | Nested collapses (tags, conversation, add-car snapshot) |
| 8 | Draft textarea / preview |
| 9 | Follow-up section (waiting_on, date, notes) |
| 10 | Append message area |
| **Total: 10+** |

### 4. Delete immediately
- English **"Case 整理明细"** → Chinese「整理明细」or remove title
- Status radio from default view (move to ⋮ menu)
- **复制摘要** from default view (broker trial)
- Collapsed-by-default for: tags, full conversation, add-car snapshot
- Follow-up CRM fields on Day 1

### 5. Stripe would remove
Everything except: **summary (3 lines)**, **draft (editable)**, **one Copy button**. Actions in overflow menu.

### 6. Linear would remove
**All inline tags** — use priority icon + title. Properties panel on side click.

### 7. Notion would remove
Nested collapses — single scrolling page with clear H2 sections.

### Simplicity score: **48 / 100**

---

## Simplicity Scorecard Summary

| Dimension | Weight | Score |
|-----------|--------|-------|
| Single primary action per screen | 25% | 45 |
| Focal point count (≤3 target) | 20% | 40 |
| Copy alignment (cancellation wedge) | 20% | 55 |
| Deletable surface area | 15% | 50 |
| Time-to-value path clarity | 20% | 75 |
| **Weighted total** | | **58** |

---

## Stripe / Linear / Notion Consensus

All three would agree on:

1. **One tab** for broker trial — hide customer portal
2. **Message-first** — paste before categories/forms
3. **One copy button** — draft only
4. **List rows minimal** — urgency + preview + click
5. **Remove English product vocabulary** ("Case", "Unified Intake") from broker-visible UI
6. **Collapse or delete** CRM fields (status radio, waiting_on, next_contact_by) until Week 2

---

*End of P16-H Phase 2 — UI Simplicity Review*
