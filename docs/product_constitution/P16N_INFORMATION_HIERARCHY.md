# P16-N Phase 7 — Information Hierarchy

**Date:** 2026-06-01  
**Audit dimensions:** Titles · Subtitles · Instructions · Buttons · Warnings · Trust copy  
**Question:** What should be visible immediately · hidden · progressive disclosure?

---

## Hierarchy Levels (Target Model)

| Level | When visible | Typography | Example |
|-------|--------------|------------|---------|
| **L0 — Identity** | Always | H1 or brand | 陈魁团队 · 车险服务 |
| **L1 — Task** | Always | H2 / question | 请描述您的需求 |
| **L2 — Action** | Always | Primary button | 发送给办公室 |
| **L3 — Trust** | Always | 1 line grey | 不会自动发送 |
| **L4 — Progress** | After first send | Step dots | 第 2 步，共 3 步 |
| **L5 — Detail** | On demand | Collapse | 已记录的内容 |
| **L6 — Audit** | Rare | Hidden default | 参考编号、UTC |

**Current problem:** L4–L6 appear at L1–L2 on landing (flow track, categories, rail sections, timestamps)

---

## Landing / Empty State

| Element | Current level | Target level | Action |
|---------|---------------|--------------|--------|
| portalHeroTitle H2 | L0 | L0 | Shorten: user problem not product name |
| portalServiceTagline | L1 (wrong) | **Remove** | Replace L3 trust line |
| IntakeFlowStepTrack | L4 | L4 after send | **Move later** |
| portalEmptyHeadline | L1 | **Remove** | Conflicts with L1 task |
| portalEmptySecondary ①②③ | L1 | **Remove** | Instructions = failure |
| portalChoosePathLabel | L1 | **Remove** | |
| Quick-start buttons | L2 (×3) | **Remove** | Infer intent |
| Structured collapse label | L2 | L5 link | **Hide** |
| Textarea | L5 (buried) | **L1** | Promote to hero |
| Submit button | L2 | L2 | Keep |
| welcome_hint / 联系人工 | L2 | L5 footer link | Demote |
| 场景仿真 | L6 | **Delete** | |
| Resume hint | L4 | L4 | Keep when present |

**Immediate visible (target):** Brand · one question · textarea · one button · one trust line = **5 elements**

---

## Mid-Flow — Titles & Subtitles

| Element | Current | Target | Action |
|---------|---------|--------|--------|
| Compact hero (active) | L0 duplicate | L0 minimal | Icon + 报送进行中 |
| Transaction banner title+subtitle | L1 | **Remove** | Progress card enough |
| portal_thread_heading | L1 | L5 collapsed | |
| Progress card title | L1 | L1 | Keep |
| portalProgressNote （状态随报送更新） | L6 | **Remove** | |
| 当前请求与类型 | L5 | L5 collapsed | |
| Record rail section headings (6×) | L1–L2 each | L5 one collapse | |
| next_best_question | L1 | **L1** | Primary question — keep prominent |
| Bubble content | L1 | L1 | Keep |
| Bubble labels/tags | L6 | **Remove** | |

---

## Instructions Audit

| Copy | Location | Verdict |
|------|----------|---------|
| 可先点选办理类型，或直接输入… | Input card empty | **Delete** — wrong hierarchy |
| portalAddCarQuickHint | Structured collapse | **Delete** — link only |
| portalHandoffPendingCtaHint | Alert body | **Merge** to title |
| portal_handoff_pending_button_subline | Below button | **Delete** |
| addCarBoundaryHint | Post-handoff | **One line** max |
| portalPostHandoffThreadHint | Thread section | **Delete** if thread collapsed |
| portalSubmittedAtTimingTruthNote | Result card | **Delete** customer-side |
| Example toggle instructions | Input card | **Move** to placeholder |

**Rule:** No instruction paragraph > 2 lines visible without user action

---

## Buttons Hierarchy

| Button | Current tier | Target tier |
|--------|--------------|-------------|
| 办理加车报价 | Primary | **Remove** (empty) |
| 联系人工 | Primary | Tertiary link |
| 其他事项 | Secondary | **Remove** (empty) |
| 提交报送 / 发送 | Primary | Primary |
| 提交补充 | Primary | Primary |
| 确认提交，开始报价处理 | Primary | Primary |
| 追加到本条记录 | Secondary | Tertiary link |
| 提交新问题 | Secondary | Secondary outline |
| 查看工作台 | Primary ghost | **Delete** |
| 去客户报送继续 | Primary | Primary (my requests) |
| 查看示例 | Tertiary | Placeholder inline |

**Rule:** Max 1 `type="primary" size="large" block"` per viewport

---

## Warnings & Alerts

| Alert | When | Target |
|-------|------|--------|
| Pre-submit gap (still needed) | Mid-flow | **One** warning max; title + chips |
| Handoff pending gap | Pre-submit | Merge with above |
| Contact-only ready | Pre-handoff | **Replace** handoff alert |
| Handoff pending title | Pre-handoff | Keep — shorten |
| completion_message success | Mid-flow | Keep |
| clientPrep 您可准备 | Post-handoff | Collapse |
| Office timing follow-up | Post-handoff | Collapse |
| Boundary blocked | Append error | Keep |
| API error | Any | Keep — friendly copy |

**Rule:** Never stack > 1 Alert above input area

---

## Trust Copy

| Copy | Occurrences | Target |
|------|-------------|--------|
| 不自动对外发送 / 办公室确认后再联系 | Brand + tagline + handoff | **Once** at bottom L3 |
| 非聊天流水 / 业务工单式 | Result eyebrows | **Delete** |
| UTC / 正式送达 vs 最近活动 | Timestamps | **Delete** footnote; one date |
| 办公室侧下一步 | Result card | **Delete** customer view |
| VIN 办公室仍会核实 | Snapshot | Inside collapsed detail |

**Trust formula (Stripe-style):**

> 您的信息只用于本次办理 · 办公室确认后才会联系您 · 参考编号供查询

Three fragments · one grey line · no repetition

---

## Progressive Disclosure Map

| Content | Trigger to reveal |
|---------|-------------------|
| Structured add-car fields | Click 「逐项填写加车信息」 |
| Flow step track | After first message sent |
| Chat thread (add-car) | Default collapsed; expand optional |
| Collected fields summary | Click 「已记录 N 项」 |
| Still-needed full list | Visible max 3 tags + 「还有 N 项」 |
| Structured snapshot post-handoff | Click 「查看整理详情」 |
| Thread post-handoff | Click 「查看对话记录」 |
| Append same case | Click 「有补充？」 |
| Case reference ID | Confirmation screen small text |
| Examples | Placeholder rotation, not toggle card |

---

## Typography Scale (Customer)

| Current issue | Target |
|---------------|--------|
| 11px / 12px / 13px soup | 14px body · 12px secondary only |
| 6 heading levels on one screen | 2 max (brand + question) |
| Monospace case ID prominent | 12px secondary, copy icon |

---

## Before / After — Empty State Hierarchy

**Before (top → bottom):**  
H2 product name → paragraph scope → step track → headline → ①②③ → label → 3 buttons → form header → textarea → submit

**After (top → bottom):**  
Brand → question (H2) → textarea → primary button → trust line → optional links (structured · 人工 · 示例)

**Information layers removed from immediate view:** 9  
**Reduction:** ~56% of above-fold information slots

---

*End of P16-N Phase 7 — Information Hierarchy*
