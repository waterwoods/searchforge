# SERVICE_ENTRY_PORTAL_CLARITY_SPRINT — Final report

## 1. Sprint theme

- **Reviewed / improved**: Unified Intake **customer entry** and **page chrome** (brand strip, tabs, hero, thread labels, progress annotation, CTAs, closure summary label, config defaults).
- **Why now**: Positioning is **unified intake + case organization + office handoff**; the UI needed to **match** that story for paid pilot credibility.

## 2. Document set created

| Doc | Purpose |
|-----|---------|
| `01_BLUEPRINT.md` | Mission, loops, success criteria |
| `02_SERVICE_ENTRY_UX_GOALS_SPEC.md` | Plain-language portal goals |
| `03_HOMEPAGE_STRUCTURE_SPEC.md` | Section order |
| `04_PORTAL_COPY_SPEC.md` | Copy keys and hierarchy |
| `05_RESULT_CARD_AND_STATE_SPEC.md` | Progress + handoff card framing |
| `06_SCOPE_BOUNDARY_SPEC.md` | In/out of scope |
| `07_FOUNDER_INSPECTION_NOTES.md` | Acceptance checklist |
| `08_FINAL_REPORT.md` | This file |
| `COPY_HIERARCHY_ONE_PAGER.md` | Optional short summary |
| `PORTAL_VS_CHAT_CHECKLIST.md` | Optional heuristic list |
| `BEFORE_AFTER_PORTAL_NOTES.md` | Optional comparison |

## 3. Current front-end audit (pre-change summary)

- **Worked**: Branded header (金盾 / 陈魁团队); add-car **当前办理** ribbon; handoff closure card with 记录要点 + timing; quick-start grid; pilot trust alert.
- **Felt chat-like**: Hero title **客户服务入口**; greeting **今天有什么可以帮您**; bubbles **您 / 办公室**; **发送**; **正在整理，马上就好**; **（实时更新）**; **已恢复对话**; tab **客户入口 — 客户**.
- **Biggest portal gap**: Copy and labels framed **conversation** first, **受理/报送/记录** second.

## 4. Portal UX goals (post-sprint)

See `02_SERVICE_ENTRY_UX_GOALS_SPEC.md` — identity, service line, transaction, state, result, less chat idiom, more 报送/办理/办公室.

## 5. Homepage structure

See `03_HOMEPAGE_STRUCTURE_SPEC.md` — identity → service hero → entry → thread + progress → input → closure.

## 6. Copy hierarchy

See `04_PORTAL_COPY_SPEC.md` and `COPY_HIERARCHY_ONE_PAGER.md`. New keys are `portal_*` plus `app_title` and quick-start label tweak.

## 7. Implementation

| Area | Change |
|------|--------|
| `ui/src/api/clientConfig.ts` | `portal_*` fields, `app_title` default, add_car quick-start label, placeholders |
| `ui/src/pages/UnifiedIntakePage.tsx` | Wire portal copy; thread heading; bubble labels; loading; progress titles; CTAs; pilot intro; tab + brand tagline |
| `ui/src/components/layout/AppLayout.tsx` | Align `app_title` fallback with portal default |
| `configs/clients/chen_kui/ui_copy.json` | Full portal strings + `app_title` |
| `services/fiqa_api/inbox_triage/config_loader.py` | Whitelist new keys |

**Logic**: **No** triage or API behavior changes; **display + config pass-through** only.

## 8. Validation

- **Run**: `cd ui && npm run build` — **passed** (Vite production build).
- **Not run**: Live browser pass, `guardrail_inbox_triage.sh` (unchanged behavior expected).

## 9. Founder summary

1. **Chat-like before**: Greeting and microcopy (**帮您**, **发送**, **实时更新**, **对话**) and weak “what is this desk?” line vs **报送/受理**.
2. **Portal-like after**: Single **service tagline**, **办理类型** entry, **报送** labels on thread and buttons, **办公室办理摘要**, **客户报送** tab, config-driven brand tagline.
3. **Files**: Listed in §7.
4. **Logic**: Unchanged.
5. **Closer to real portal**: **Yes** for copy/hierarchy; layout is still a thread (acceptable low-risk scope).
6. **Later**: Optional wizard-style layout for non–add-car; mobile polish; translate remaining English customer tags.

## 10. 中文宏观总结

- 首页与客户页**更像正式受理门户**：品牌副标题、英雄区「统一受理与报送」、办理类型与「提交报送」用语统一。
- **当前在办什么**：加车 ribbon 与「当前办理」标签仍在；进度卡标题对非加车改为「当前受理进度」，减少闲聊感。
- **结果更像案件整理**：结案区用「办公室办理摘要」承接要点块与跟进说明，整体语义偏**记录与跟进**。
- **这轮值不值**：以低成本（配置 + 文案 + 少量结构标题）换试点叙事一致性，**值**。
- **下一步最值**：在浏览器里按 `07_FOUNDER_INSPECTION_NOTES.md` 走一遍真机验收；若仍嫌「像聊天」，再评估把线程区改成「时间线 + 折叠」或分栏式**案卷视图**（更大改动，另开 sprint）。
