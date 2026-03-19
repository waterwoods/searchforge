# Rules Center UX / Interaction Spec

**Sprint:** Minimal Business Rules Center for Add-Car Quote  
**Purpose:** Describe what page/surface exists, how editing, preview, and publish work.

---

## 1. Where the Rules Center Lives

**Location:** Under Broker Workbench — `workbench/rules-center` or `workbench/add-car-rules`

- Not under Customer Entry (does not clutter customer-facing entry)
- Accessible from AI Workbench menu (alongside Unified Intake)
- Single page focused on Add-Car Quote only

---

## 2. Page Structure

### Layout (business-friendly labels)

| Section | Label (中文) | Purpose |
|---------|-------------|---------|
| Header | 加车报价流程规则 | Add-Car Quote flow rules |
| Current rules | 当前流程 | Show current flow structure |
| Editable fields | 可编辑规则 | Edit first reply, next-step prompts, handoff |
| Preview | 流程预览 | Preview with sample input |
| Actions | 保存草稿 / 发布 | Save draft, Publish, Restore |

---

## 3. How the Business User Sees Current Rules

**Flow structure (read-only):**
- 收集顺序: 年份车型 → 邮编 → 提车日期/驾驶人 → 转办公室
- 转办公室条件: 有车 + 邮编 + (提车或驾驶人)

**Editable fields (read-write):**
- 第一句怎么回 (中文 / 英文)
- 缺年份车型时问什么
- 缺邮编时问什么
- 缺提车/驾驶人时问什么
- 转办公室时说什么

---

## 4. How Editing Works

- Each field: text input or textarea
- Labels in business language (no intent_key, soft_route, etc.)
- Save draft: updates draft config; does not affect live flow
- Preview: uses draft config

---

## 5. How Preview Works

- **Input:** Text area for sample customer message

**Examples:**
- "我想加一台X5"
- "2024 BMW X5, 90210"
- "90210" (after vehicle+zip)

- **Output:** System reply (as would be sent to customer)
- **Context:** Collected / still needed (optional)

---

## 6. How Publish Works

- **Publish** button: copies draft → published config
- **Restore** button: restores last published version to draft
- **Live flow** uses published config only

---

## 7. What Should Feel Simple and Intuitive

- No engineering terms
- One scenario (Add-Car) only
- Clear separation: view → edit → preview → publish
- No hidden state; draft vs published always visible

---

*See also: 03_ADD_CAR_RULES_DATA_MODEL.md, 04_SAFETY_GUARDRAIL_SPEC.md*
