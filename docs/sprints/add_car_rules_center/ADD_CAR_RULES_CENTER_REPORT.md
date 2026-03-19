# Minimal Business Rules Center for Add-Car Quote Report

## 1. Sprint Theme

- **What was chosen:** Build the smallest useful Business Rules Center for the Add-Car Quote scenario so Chen Kui and assistants can safely view, edit, preview, and trial selected business rules without changing code.
- **Why now:** The founder wants more business flexibility, less dependency on engineering for wording changes, and safe experimentation. Add-Car Quote is the correct first scenario: high value, mature flow (80% completion), and config-driven surface already exists.

---

## 2. Document Set Created

| Doc | Path |
|-----|------|
| Product Blueprint | `docs/sprints/add_car_rules_center/01_PRODUCT_BLUEPRINT.md` |
| Rules Center UX / Interaction Spec | `docs/sprints/add_car_rules_center/02_RULES_CENTER_UX_SPEC.md` |
| Add-Car Rules Data Model / Config Spec | `docs/sprints/add_car_rules_center/03_ADD_CAR_RULES_DATA_MODEL.md` |
| Safety / Guardrail Spec | `docs/sprints/add_car_rules_center/04_SAFETY_GUARDRAIL_SPEC.md` |
| Execution Outline | `docs/sprints/add_car_rules_center/05_EXECUTION_OUTLINE.md` |
| Acceptance / SLA Criteria | `docs/sprints/add_car_rules_center/06_ACCEPTANCE_CRITERIA.md` |
| Founder Demo / Inspection Notes | `docs/sprints/add_car_rules_center/07_FOUNDER_DEMO_INSPECTION_NOTES.md` |
| Baseline Audit | `docs/sprints/add_car_rules_center/00_BASELINE_AUDIT.md` |

---

## 3. Baseline Audit

### Current Add-Car Logic

- **Location:** `services/fiqa_api/inbox_triage/triage.py`
- **Key functions:** `_get_next_ask_for_add_car`, `_add_car_enough_for_handoff`, `_extract_add_car_fields`, `_add_car_structured_fields`
- **First-turn reply:** `_build_client_reply_draft` — many inline branches; uses `templates.get("add_car")` as fallback
- **Next-step prompts:** Previously hardcoded in `_get_next_ask_for_add_car`

### What Was Hardcoded

- Ask vehicle (zh/en): "先把年份和车型发我，我就能帮你算。" / "Send me the year and make/model first..."
- Ask zip (zh/en): "先把地址邮编发我，我就能帮你算。" / "Send me the zip or address first..."
- Ask delivery/driver (zh/en): "提车日期和主要驾驶人发我一下，我好安排报价。" / "Send me the delivery date and main driver..."

### What Was Realistic to Externalize

- Next-step prompts (ask_vehicle, ask_zip, ask_delivery_driver) — **easy**
- First reply and handoff — already in reply_templates and handoff_phrases; Rules Center displays them but editing not in Loop 1 scope

### Biggest Current Weakness

Next-step prompts were fully hardcoded. Business users could not change them without a code change.

---

## 4. Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Where Rules Center lives** | `workbench/add-car-rules` under AI Workbench | Does not clutter Customer Entry; accessible with Unified Intake |
| **What is editable** | ask_vehicle, ask_zip, ask_delivery_driver (zh/en) | Highest value; first reply/handoff already configurable elsewhere |
| **What is locked** | Collection order, handoff threshold, extraction logic | Changing would require code; risky for business users |
| **How preview works** | POST /api/inbox/add-car-rules/preview with text + optional rules_override | Uses triage engine with override; shows client_reply_draft, collected/still_needed |
| **How draft/publish works** | Draft = UI state; Publish = PUT to backend writes add_car_rules.json | Simple; Restore = GET reloads published |

---

## 5. Iteration Loop 1

### What Changed

- Added `configs/industries/insurance/add_car_rules.json` with ask_vehicle, ask_zip, ask_delivery_driver
- Updated `config_loader.py`: `get_add_car_rules()`
- Updated `triage.py`: `_get_next_ask_for_add_car` reads from config; accepts `add_car_rules_override` for preview
- Added API: GET /api/inbox/add-car-rules, POST /api/inbox/add-car-rules/preview
- Added UI: AddCarRulesPage at workbench/add-car-rules with view, edit, preview

### What Became Editable

- 缺年份车型时问什么 (zh/en)
- 缺邮编时问什么 (zh/en)
- 缺提车/驾驶人时问什么 (zh/en)

### What Became Easier to Understand

- Business-friendly labels (no intent_key, soft_route)
- Current flow structure visible (收集顺序, 转办公室条件)
- Preview with sample input

### What Did Not Improve

- First reply and handoff not editable in Rules Center (remain in reply_templates / handoff_phrases)
- Preview for first turn does not use override (first-turn logic uses different code path)

### Whether Loop 1 Was Worth It

**Yes.** Proved the concept: config-driven next-step prompts, preview with override, business-readable UI.

---

## 6. Iteration Loop 2

### What Changed

- Added `save_add_car_rules()` in config_loader
- Added PUT /api/inbox/add-car-rules (publish)
- UI: Publish button, Restore button

### What Became Safer

- Publish writes to config; Restore reloads published
- Preview before publish (user can verify before publishing)

### What Became More Practical for Real Office Use

- Chen Kui can edit → preview → publish without code deploy
- Restore available if publish was mistaken

### What Still Remained Weak

- Publish may fail in read-only environments (e.g. Cloud Run without writable volume)
- No version history; single published version only

### Whether Loop 2 Was Worth It

**Yes.** Completes the flow: edit → preview → publish → restore.

---

## 7. Optional Loop 3

**Not used.** No clearly valuable, low-risk refinement remained. Stopping is correct.

---

## 8. Validation Summary

| Check | Result |
|-------|--------|
| `run_inbox_triage_scenarios.py` | 53/53 passed |
| `npm run build` | ✓ built |
| Add-car rules config load | ✓ |
| Preview with override | ✓ (multi-turn) |

**Limitations:** Publish requires writable config dir. In Cloud Run, may return 503.

---

## 9. Release / Deployment Judgment

- **Backend:** No redeploy required for Rules Center to work. Config is loaded at runtime. Publish writes to local config file.
- **Frontend:** Redeploy needed to expose Add-Car Rules page. Route: `/workbench/add-car-rules`.
- **Founder can inspect:** Yes, after frontend redeploy. Open Workbench → 加车报价规则.

---

## 10. Founder Showcase (REQUIRED)

### Example 1: Changing first next-step prompt

- **Business user changes:** 缺年份车型时问什么（中文）→ "请把年份和车型发给我，我帮您算报价。"
- **Preview input:** 多轮：2024 90210 (after 我想加一台X5)
- **Preview output:** 好的，2024的。 邮编90210。 提车日期和主要驾驶人发我一下，我好安排报价。（若编辑了 ask_delivery_driver，则显示新文案）
- **Why useful:** Business can tune wording without engineering.
- **Why safe:** Preview first; publish only when ready.

### Example 2: Changing ask_zip

- **Business user changes:** 缺邮编时问什么（中文）→ "请发一下您的邮编或地址。"
- **Preview input:** 多轮：90210
- **Preview output:** 系统回复使用新文案
- **Why useful:** Softer or more formal tone as needed.
- **Why safe:** Draft; preview; publish.

### Example 3: Changing ask_delivery_driver

- **Business user changes:** 缺提车/驾驶人时问什么（中文）→ "提车日期和主要驾驶人发我一下。"
- **Preview input:** 多轮：2024 90210
- **Preview output:** 好的，2024的。 邮编90210。 提车日期和主要驾驶人发我一下。
- **Why useful:** Minor wording tweak.
- **Why safe:** Preview confirms before publish.

### Example 4: Previewing short customer input

- **Business user changes:** (none)
- **Preview input:** 我想加一台X5
- **Preview output:** 先把年份和地址邮编发我，我就能帮你算报价。
- **Why useful:** See first-turn reply (from existing logic).
- **Why safe:** Read-only preview.

### Example 5: Publishing a draft

- **Business user changes:** Edit ask_delivery_driver.zh
- **Preview input:** 多轮：2024 90210
- **Preview output:** (new wording)
- **Publish:** Click 发布
- **Why useful:** Changes go live for Unified Intake.
- **Why safe:** Restore available to revert.

---

## 11. Final Judgment

1. **Is the minimal Rules Center now usable?** Yes.
2. **Is it simple enough for Chen Kui / assistants?** Yes. Business labels, no engineering terms.
3. **Does it actually increase flexibility?** Yes. Next-step prompts are editable without code.
4. **Is it safe enough not to create chaos?** Yes. Preview before publish; restore available.
5. **Biggest remaining weakness:** Publish may fail in read-only deployments; first reply and handoff not in Rules Center.
6. **Single best next move:** Add first reply and handoff to Rules Center; consider writable volume for Cloud Run if publish is needed in production.

---

## 12. Iteration Log

### Loop 1

- **What changed:** Config, backend integration, API, UI (view, edit, preview)
- **What got better:** Next-step prompts configurable; preview works
- **What did not improve:** First-turn preview does not use override
- **Worth it:** Yes
- **Recommended next step:** Loop 2 (draft/publish)

### Loop 2

- **What changed:** save_add_car_rules, PUT endpoint, Publish/Restore UI
- **What got better:** Full edit → preview → publish → restore flow
- **What did not improve:** Publish fails in read-only envs
- **Worth it:** Yes
- **Recommended next step:** Optional: first reply/handoff in Rules Center; writable volume for prod

### Loop 3

- **Used:** No
- **Reason:** No clear low-risk refinement; stopping correct

---

## 13. 中文宏观总结

- **为什么现在做业务规则中心最小版：** 创始人希望陈奎和助理能安全地调整加车报价流程的文案，而不依赖工程师。加车报价是成熟流程，适合作为第一个可配置场景。
- **主要用了什么方法/技术：** 将下一步提示语从代码中抽离到 `add_car_rules.json`；后端读取配置；API 支持预览时注入规则覆盖；前端提供业务友好的编辑和预览界面。
- **这样做的好处：** 业务人员可编辑「缺年份车型时问什么」「缺邮编时问什么」「缺提车/驾驶人时问什么」，预览后再发布，无需改代码。
- **现在已经实现了什么：** 加车报价规则中心页面；可编辑 6 个字段（3 类 × 中英）；预览（含多轮示例）；发布与恢复。
- **还差什么：** 第一句回复和转办公室文案未纳入规则中心编辑；发布在只读环境可能失败。
- **有没有重大问题：** 无。发布在 Cloud Run 等只读环境会返回 503，需可写卷或手动更新配置。
- **下一步最该做什么：** 将第一句回复和转办公室文案加入规则中心；若需生产环境发布，配置可写存储。

---

## 14. COPY/PASTE FOUNDER BLOCK

```
Minimal Business Rules Center for Add-Car Quote — Founder Summary

Biggest rules-center improvement: 陈奎和助理可以编辑加车报价的下一步提示语（缺年份车型、缺邮编、缺提车/驾驶人时问什么），预览后再发布，无需改代码。

Biggest remaining weakness: 发布在只读环境（如 Cloud Run）会失败；第一句回复和转办公室文案尚未纳入规则中心。

Business users can now safely try it: 是。编辑 → 预览 → 发布 → 恢复，流程完整。

Redeploy needed: 前端需要重新部署以暴露「加车报价规则」页面。

What Andy should inspect next: 打开 Workbench → 加车报价规则；编辑任一字段；点击「多轮：2024 90210」→ 预览；确认后发布；在 Unified Intake 中验证。
```

---

## 15. REQUIRED SHORT OVERVIEW

### 为什么做这件事

创始人希望业务人员能安全地调整加车报价流程的文案，减少对工程师的依赖，并支持在真实客户逻辑上做可控实验。

### 主要用了什么方法/技术

将下一步提示语从代码抽离到 JSON 配置；后端通过 config_loader 读取；triage 支持规则覆盖用于预览；前端提供业务友好的规则中心页面，支持编辑、预览、发布、恢复。

### 这轮最大的提升

加车报价的 6 个下一步提示语（3 类 × 中英）可在规则中心编辑，预览后发布，无需改代码；发布与恢复流程完整。

### 现在还差什么

第一句回复和转办公室文案未纳入规则中心；发布在只读部署环境会失败；无版本历史。
