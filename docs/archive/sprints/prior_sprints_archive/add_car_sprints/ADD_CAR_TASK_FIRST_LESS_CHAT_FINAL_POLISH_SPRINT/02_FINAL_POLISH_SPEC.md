# ADD-CAR TASK-FIRST / LESS-CHAT — Final polish spec

## What still felt too chat-like

- **Pre-handoff** thread heading framed the center as “办理过程与办公室整理,” which reads like a **conversation object**.
- **Post-handoff** used hardcoded labels such as “查看完整报送与整理过程” and “办公室办理摘要（给客户）,” which keep **thread + reply** metaphors prominent.
- The **system closure paragraph** used a large body size (15px), visually competing with the **result card** like a **primary chat reply**.
- Copy still said **“本对话”** in places, which undercuts **same-record / office queue** mental model.

## What should feel more task-like

- **Primary object:** 受理结果卡 + 服务记录编号 + 状态 + 办公室下一步.
- **Secondary object:** 报送气泡 / 原文 — explicitly **备查**, optional, not “the main thing.”
- **Office:** clearly **已收到 / 已接手** the record; next steps are **办公室侧**.
- **Confidence:** explicit **不必在微信或电话里重复**已写在入口里的要点.

## What this sprint polished

1. **Configurable post-handoff chrome** — thread heading, hint, collapse label, “next section” divider, closure section divider (defaults in `clientConfig.ts`, Chen Kui overrides in `ui_copy.json`, API whitelist in `config_loader.py`).
2. **Copy tightening** — `handoff_closure_processing_add_car`, `handoff_new_issue_hint`, `portal_thread_heading`, `portal_closure_reply_summary_label`, `add_car_result_card_eyebrow_hint` (defaults + Chen Kui JSON).
3. **Subtle typography** — Add-Car handoff closure body **13px** instead of **15px** so the **result card** stays ahead of the **draft reply** block.

## Acceptance criteria

- [x] After handoff, section labels do **not** default to “给客户” / “完整聊天” framing; they reinforce **同条服务记录** and **备查**.
- [x] No new user-facing flows; only copy, labels, and one font-size adjustment.
- [x] `npm run build` passes for `ui/`.
- [x] New UI copy keys are **allowed** through `get_ui_copy()` for client JSON overrides.
