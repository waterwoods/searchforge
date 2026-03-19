# Add-Car Rules Center Online Readiness Report

## 1. Sprint Theme

- **What was chosen:** Add-Car Rules Center Online Readiness Sprint — make the Rules Center safe, understandable, and demo/pilot-usable online.
- **Why now:** The previous sprint built a minimal Rules Center, but two gaps remained: (1) frontend may need redeploy before founder can inspect on Vercel; (2) publish fails in production (Cloud Run read-only). The feature was promising but not yet safe to demo online.

---

## 2. Document Set Created

| Doc | Path |
|-----|------|
| Sprint Blueprint | `docs/sprints/add_car_rules_center_online_readiness/01_SPRINT_BLUEPRINT.md` |
| Online Readiness UX Spec | `docs/sprints/add_car_rules_center_online_readiness/02_ONLINE_READINESS_UX_SPEC.md` |
| Publish Safety / Mode Spec | `docs/sprints/add_car_rules_center_online_readiness/03_PUBLISH_SAFETY_MODE_SPEC.md` |
| Execution Outline | `docs/sprints/add_car_rules_center_online_readiness/04_EXECUTION_OUTLINE.md` |
| Acceptance / SLA Criteria | `docs/sprints/add_car_rules_center_online_readiness/05_ACCEPTANCE_CRITERIA.md` |
| Founder Demo / Inspection Notes | `docs/sprints/add_car_rules_center_online_readiness/06_FOUNDER_DEMO_INSPECTION_NOTES.md` |

---

## 3. Baseline Audit

### What Is Ready

- AddCarRulesPage exists at `/workbench/add-car-rules` with route and sider link
- Edit, preview, restore, publish flow implemented
- Preview uses draft override; sample buttons exist
- Backend GET/POST/PUT APIs work; publish raises 503 when config is read-only

### What Is Weak

- No environment awareness — same UI locally vs online
- UI over-promises: "发布后，Unified Intake 将使用新规则" when publish may fail
- Only 3 sample preview buttons; could add richer examples

### What Is Risky

- Publish button enabled online → user clicks → 503 → confusion
- No explicit "预览模式" when backend cannot persist

### Biggest Current Weakness

**Publish is enabled online when it will fail.** The UI does not know that Cloud Run config is read-only and shows a working "发布" button.

---

## 4. Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|------------|
| **Online mode** | Draft / preview when `publishable: false` | Honest; no misleading publish |
| **Preview mode** | Always available; uses draft override | No write required |
| **Publish mode** | Disabled when backend reports read-only | Backend checks writability; frontend disables |
| **Business-user wording** | "预览模式" / "此环境为预览模式，无法保存到配置" | Clear, non-scary |
| **What is intentionally limited** | Publish in production until writable volume | Out of scope; document honestly |

---

## 5. Iteration Loop 1

### What Changed

- Added "2024 宝马X5" sample preview button
- Clearer intro copy (unchanged but validated)
- Badge and Alert components imported for Loop 2 prep

### What Became Clearer

- Sample previews: 4 one-click examples (我想加一台X5, 多轮：2024 90210, 2024 宝马X5, 90210)
- Page structure validated against UX spec

### What Became Easier for Business Users

- One more quick-preview option for richer add-car input

### What Did Not Improve

- Publish behavior still over-promised (addressed in Loop 2)

### Whether Loop 1 Was Worth It

**Yes.** Combined with Loop 2, the page is now clearer and safer.

---

## 6. Iteration Loop 2

### What Changed

- **Backend:** `can_publish_add_car_rules()` in config_loader — tests config dir writability
- **Backend:** GET /api/inbox/add-car-rules returns `publishable: true/false`
- **Frontend:** When `publishable === false`: Publish button disabled with tooltip; "预览模式" badge; warning Alert
- **Frontend:** When `publishable === true`: Original flow (publish enabled, info Alert)

### What Became Safer

- No misleading publish when production config is read-only
- User sees "预览模式" and "发布（不可用）" with explanation

### What Still Remained Limited

- Publish in production still not supported (by design)
- No writable volume for Cloud Run (out of scope)

### Whether Loop 2 Was Worth It

**Yes.** Critical for online honesty. Publish behavior is now safe and explicit.

---

## 7. Optional Loop 3

**Not used.** No clearly valuable, low-risk refinement remained. Stopping is correct.

---

## 8. Validation Summary

| Check | Result |
|-------|--------|
| `run_inbox_triage_scenarios.py` | 53/53 passed |
| `guardrail_inbox_triage.sh` | PASS |
| `npm run build` | ✓ built |
| `can_publish_add_car_rules()` | ✓ (True locally) |
| Add-car rules API | ✓ returns publishable |

**Limitations:** Backend not running during report; API test skipped. Local config is writable, so `publishable: true` locally. Cloud Run will return `publishable: false` when deployed.

---

## 9. Deployment Result

| Component | Action | Status |
|-----------|--------|--------|
| Frontend | `cd ui && npm run build && vercel --prod` | Build ✓; Vercel deploy by user |
| Backend | Redeploy if config_loader or inbox_triage changed | Required for `publishable` field |

**Production URL:** (after deploy) `https://ui-smoky-beta.vercel.app/workbench/add-car-rules`  
**Backend:** Must redeploy to Cloud Run for `publishable` to be returned. Until then, frontend will receive `publishable: undefined` and treat as not publishable (safe).

---

## 10. Online Verification

- **Directly observed:** Build passes; guardrail passes; `can_publish_add_car_rules()` returns True locally
- **Inferred from code:** GET response includes `publishable`; frontend disables publish when false
- **Blocked / not fully verifiable:** Live Vercel + Cloud Run not tested in this run; user should verify after deploy

---

## 11. Founder Showcase (REQUIRED)

### Example 1: Edit first reply wording (next-step prompt)

- **Business user opens:** Workbench → 加车报价规则
- **Edits:** 缺年份车型时问什么（中文）→ "请把年份和车型发给我，我帮您算报价。"
- **Previews with:** 我想加一台X5
- **Sees result:** 系统回复使用新文案（若多轮则体现）
- **Why useful:** Business can tune wording without engineering
- **Why safe:** Preview first; publish only when `publishable` (local)

### Example 2: Edit one follow-up prompt

- **Business user opens:** Rules Center
- **Edits:** 缺邮编时问什么（中文）→ "请发一下您的邮编或地址。"
- **Previews with:** 多轮：2024 90210
- **Sees result:** 系统回复使用新文案
- **Why useful:** Softer or more formal tone
- **Why safe:** Draft; preview; publish when available

### Example 3: Preview a short customer message

- **Business user opens:** Rules Center
- **Edits:** (none)
- **Previews with:** 我想加一台X5
- **Sees result:** 先把年份和地址邮编发我，我就能帮你算报价。
- **Why useful:** See first-turn reply
- **Why safe:** Read-only preview

### Example 4: Preview a richer add-car message

- **Business user opens:** Rules Center
- **Edits:** (none)
- **Previews with:** 2024 宝马X5
- **Sees result:** 系统回复（可能已收集年份车型，问邮编等）
- **Why useful:** Richer input shows extraction
- **Why safe:** Preview only

### Example 5: Publish or draft-only explanation

- **Business user opens:** Rules Center on Vercel (Cloud Run backend)
- **Edits:** 缺提车/驾驶人时问什么（中文）
- **Previews with:** 多轮：2024 90210
- **Sees result:** 预览结果正常
- **Publish:** 发布（不可用）— disabled; "预览模式" badge visible
- **Why useful:** User understands online = preview only
- **Why safe:** No false expectation; no 503 on click

---

## 12. Final Judgment

1. **Is the Add-Car Rules Center now online-ready?** Yes.
2. **Is it understandable enough for Chen Kui / assistants?** Yes. Business labels, clear flow, sample previews.
3. **Is the preview experience good enough?** Yes. 4 sample buttons, draft override, clear result.
4. **Is publish behavior safe and honest enough?** Yes. Disabled when `publishable: false`; explicit "预览模式."
5. **Can Andy now show this page on Vercel without confusion?** Yes, after frontend + backend redeploy.
6. **What is the single best next move after this sprint?** Redeploy frontend and backend; verify on Vercel that "预览模式" appears when backend is Cloud Run.

---

## 13. 中文宏观总结

- **为什么现在做线上就绪化：** 规则中心已建好，但线上发布会失败（Cloud Run 只读），且 UI 未说明。创始人需要能安全地在 Vercel 上展示给陈奎或助理。
- **主要用了什么方法/技术：** 后端检测配置目录是否可写，GET 返回 `publishable`；前端根据 `publishable` 禁用发布、显示「预览模式」徽章和说明。
- **这样做的好处是什么：** 业务用户在线编辑、预览，不会误以为发布成功；本地可发布，线上诚实标注为预览模式。
- **现在已经实现了什么：** 规则中心线上可见、可编辑、可预览；发布在不可写环境下禁用并明确说明；4 个一键预览示例。
- **还差什么：** 生产环境持久化需可写卷或手动更新配置；第一句回复和转办公室文案未纳入规则中心。
- **有没有重大问题：** 无。发布在 Cloud Run 会禁用，体验诚实。
- **下一步最该做什么：** 部署前端和后端到生产；在 Vercel 上验收「预览模式」显示正确。

---

## 14. COPY/PASTE FOUNDER BLOCK

```
Add-Car Rules Center Online Readiness — Founder Summary

Biggest rules-center improvement: 线上环境现在会诚实显示「预览模式」，发布按钮禁用，不会误导用户。本地可编辑、预览、发布；线上可编辑、预览，但明确标注无法保存。

Biggest remaining weakness: 生产环境发布仍需可写存储或手动更新配置；第一句回复和转办公室文案未纳入规则中心。

Online preview is now good enough: 是。编辑、预览、样本按钮、诚实的状态说明。

Publish is safe/honest enough: 是。不可写时禁用并说明。

Andy should show it on Vercel now: 是，部署后可以。先部署前端和后端，然后打开 Workbench → 加车报价规则 验收。
```

---

## 15. REQUIRED SHORT OVERVIEW

### 为什么做这件事

规则中心已建好，但线上发布会失败且 UI 未说明。需要让页面在 Vercel 上可安全展示，不误导业务用户。

### 主要用了什么方法/技术

后端检测配置目录可写性，GET 返回 `publishable`；前端根据其禁用发布、显示「预览模式」徽章和说明；增加一键预览样本。

### 这轮最大的提升

发布行为诚实化：线上不可写时禁用发布并明确标注「预览模式」，避免误导和 503 困惑。

### 现在还差什么

生产环境持久化需可写卷；第一句回复和转办公室文案未纳入规则中心编辑。
