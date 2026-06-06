# Client UI Copy Wiring Spec

**Sprint:** Client Configuration Wiring Sprint  
**Created:** 2026-03-18

---

## 1. UI Labels/Copy to Wire First

| Key | Current hardcoded | Source | Location |
|-----|-------------------|--------|----------|
| `app_title` | "保险经纪人智能助手" | ui_copy.json | AppLayout.tsx |
| `office_label` | "办公室" | ui_copy.json | UnifiedIntakePage.tsx (role labels, bubbles) |
| `office_workbench` | "办公室工作台" | ui_copy.json | Tab label, Workbench title |
| `handoff_default` | "办公室会尽快处理，有结果会联系您。" | ui_copy.json | Success message, handoff card |
| `welcome_highlight` | "您的消息会直接转给办公室，我们会尽快帮您处理。" | ui_copy.json | Customer Entry paragraph |
| `welcome_hint` | "如需人工协助，点击「联系人工」即可，消息会直接转给办公室。" | ui_copy.json | Quick-start card |
| `quick_start_buttons` | QUICK_START_BUTTONS array | ui_copy.json | All 6 buttons |

---

## 2. Where Current Hardcoded Copy Exists

| File | Lines (approx) | Content |
|------|----------------|---------|
| AppLayout.tsx | 42 | "保险经纪人智能助手" |
| UnifiedIntakePage.tsx | 74–82 | QUICK_START_BUTTONS |
| UnifiedIntakePage.tsx | 957 | message.success handoff |
| UnifiedIntakePage.tsx | 1008 | welcome_highlight |
| UnifiedIntakePage.tsx | 1031 | welcome_hint |
| UnifiedIntakePage.tsx | 1099, 1147 | 您 / 办公室 role labels |
| UnifiedIntakePage.tsx | 1313, 1316 | handoff_default, case_created |
| UnifiedIntakePage.tsx | 1749 | 办公室工作台 |
| UnifiedIntakePage.tsx | 2626–2627 | Tab label, office suffix |

---

## 3. Visible Differences Between Clients

| Client | app_title | office_label | Example |
|--------|-----------|--------------|---------|
| chen_kui | 保险经纪人智能助手 | 办公室 | Chen Kui branding |
| demo_broker | 保险经纪助手 Demo | 客服团队 | Generic demo branding |

---

## 4. Fallback When Config Missing

Use current hardcoded values as fallback. Never render empty or broken.
