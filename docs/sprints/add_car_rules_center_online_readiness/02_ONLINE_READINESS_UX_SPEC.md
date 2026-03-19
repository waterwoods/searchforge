# Add-Car Rules Center — Online Readiness UX Spec

**Sprint:** Add-Car Rules Center Online Readiness  
**Purpose:** Describe how the Rules Center page should look and behave online for business users.

---

## 1. Page Appearance Online

### Header
- **Title:** 加车报价流程规则
- **Subtitle:** 可编辑加车报价流程中的回复文案，预览效果后再发布。当前仅支持下一步提示语的编辑。

### Sections
| Section | Label | Purpose |
|---------|-------|---------|
| Editable rules | 可编辑规则 | 6 fields (ask_vehicle, ask_zip, ask_delivery_driver × zh/en) |
| Actions | 发布 / 恢复已发布版本 | Publish (when safe) or Draft-only badge |
| Flow structure | 当前流程（只读） | 收集顺序、转办公室条件 |
| Preview | 流程预览 | Input + sample buttons + preview result |

---

## 2. What the Business User Should Understand Immediately

- **What this page is:** A place to edit the wording of Add-Car Quote follow-up prompts.
- **What is editable:** "缺年份车型时问什么"、"缺邮编时问什么"、"缺提车/驾驶人时问什么" (zh/en).
- **What is not editable:** Collection order, handoff threshold, extraction logic.

---

## 3. Draft / Edit / Preview / Publish States

| State | How user sees it | What it means |
|-------|-------------------|---------------|
| **Viewing** | Loaded rules, no edits | Displaying current published (or default) rules |
| **Editing** | Changed any field | Draft state; preview uses draft |
| **Preview** | Click 预览 → see result | Uses draft if any; otherwise published |
| **Published** | Click 发布 → success | Rules saved to config; live flow uses them |
| **Draft-only** | 发布 disabled + badge | This environment cannot persist; edit + preview only |

---

## 4. Copy That Reassures the User

- **When publish is available:** "编辑后点击「预览」查看效果。确认无误后点击「发布」保存到配置。发布后，Unified Intake 将使用新规则。"
- **When publish is unavailable:** "此环境为预览模式。可编辑和预览，但无法在此保存到配置。如需正式发布，请在本地环境操作。"

---

## 5. Limitations Visible Without Sounding Scary

- **Environment badge:** "预览模式" or "可发布" — small, non-alarming
- **Publish button:** Disabled with tooltip when draft-only
- **Restore:** Always available (reloads from backend; no write needed)

---

## 6. Sample Preview Inputs (One-Click)

| Label | Text | Turns |
|-------|------|-------|
| 我想加一台X5 | 我想加一台X5 | — |
| 多轮：2024 90210 | 2024 90210 | 客户: 我想加一台X5; 系统: 先把年份和地址邮编发我... |
| 90210 | 90210 | — |

Optional: add "2024 宝马X5" and "2024 宝马X5，90210" for richer examples.

---

*See also: 03_PUBLISH_SAFETY_MODE_SPEC.md*
