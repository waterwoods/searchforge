# Hybrid Unified Entry System Report

**Sprint**: Hybrid Unified Entry System  
**Date**: 2026-03-15  
**Production URL**: https://ui-smoky-beta.vercel.app/workbench/unified-intake

---

## 1. Sprint Theme

**What was chosen**: Upgrade the Unified Intake page into a hybrid customer entry system that combines welcome, quick-button guided start, free-text main entry, dynamic rerouting when user intent changes, structured intake logic, and clearer case-creation confirmation.

**Why now**: The current entry felt like a lab tool—single text area, no guided start. The founder agreed the product should feel welcoming, easy to start, not intimidating, and able to guide without forcing. This sprint defines and implements the next major interaction model.

---

## 2. Document Set Created

| Document | Path | Purpose |
|----------|------|---------|
| Product Blueprint | `docs/sprints/hybrid_unified_entry/01_PRODUCT_BLUEPRINT.md` | Why sprint matters, current vs new model, design principle |
| UX / Interaction Design Spec | `docs/sprints/hybrid_unified_entry/02_UX_INTERACTION_DESIGN_SPEC.md` | First screen, 5 buttons, button+text coexistence, rerouting, customer vs office |
| Structured Intake Flow Spec | `docs/sprints/hybrid_unified_entry/03_STRUCTURED_INTAKE_FLOW_SPEC.md` | Button-guided flow, free-text-first, one-question-at-a-time, answer-first |
| Routing / State Logic Spec | `docs/sprints/hybrid_unified_entry/04_ROUTING_STATE_LOGIC_SPEC.md` | Button context storage, free-text override, soft vs hard route |
| Case Creation Policy Spec | `docs/sprints/hybrid_unified_entry/05_CASE_CREATION_POLICY_SPEC.md` | When to suggest case creation, confirmation copy |
| Acceptance / SLA Criteria | `docs/sprints/hybrid_unified_entry/06_ACCEPTANCE_SLA_CRITERIA.md` | Success criteria, UX bar, anti-patterns |
| Founder Demo / Inspection Notes | `docs/sprints/hybrid_unified_entry/07_FOUNDER_DEMO_INSPECTION_NOTES.md` | What to inspect, scenarios, checklist |

---

## 3. Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|------------|
| **Welcome model** | "今天有什么可以帮您？" + "您可以选择下面的主题，或直接在下方输入您的问题。" | Friendly, one line; secondary explains buttons + free text |
| **5-button model** | 获取报价, 保单变更, 报事故, 付款/账单, 上传材料/联系客服 | Maps to 5 core flows: add_car, remove_car, claim_intake, cancellation_warning, missing_document |
| **Button vs free-text priority** | Buttons are soft starters; free text overrides | Non-negotiable: "Free text is always the highest-priority truth" |
| **Rerouting behavior** | When text intent conflicts with button, system acknowledges and proceeds with text intent | "看起来这是 [X] 相关的问题，我先帮您处理这个。" |
| **Case creation policy** | Explicit "已整理成 case，办公室会尽快跟进。" when case persisted | Makes case creation visible to customer |

---

## 4. Iteration Loop 1

**What changed**:
- Added welcome card: "今天有什么可以帮您？" with secondary copy
- Added 5 quick-start buttons with selected state (primary when selected)
- Free-text input remains prominent below
- `selectedButtonIntent` state; passed as `soft_route` to API
- Case-creation message: "已整理成 case，办公室会尽快跟进。" when case_id present

**What got more customer-friendly**:
- Welcoming first impression
- Easy start: one click sets topic
- No lock-in: user can type without button or deselect

**What got more product-like**:
- Page feels like SaaS intake, not paste-only lab
- Clear separation: customer entry vs Broker Workbench tab

**What did not improve**:
- Rerouting not yet implemented (Loop 2)
- Backend did not use soft_route for logic yet

**Whether it was worth it**: Yes. Visible product improvement; foundation for Loop 2.

---

## 5. Iteration Loop 2

**What changed**:
- Backend: `soft_route` in TriageRequest; `_infer_intent_from_result()`; reroute when inferred ≠ soft_route
- Response: `reroute_occurred`, `reroute_message`, `previous_soft_route`, `new_intent`
- Frontend: on reroute, clear `selectedButtonIntent`; prepend reroute message to reply
- Multi-turn: "当前主题" tag when button selected; closable to clear

**What improved vs Loop 1**:
- Rerouting works: click "付款" then type "我想加一台新车" → system says "看起来这是加车报价相关的问题，我先帮您处理这个。" and proceeds with add-car
- Soft-route messaging is explicit
- Selected topic visible during multi-turn; user can clear

**What still remained weak**:
- Reroute detection is rule-based; edge cases (e.g., mixed intent) may not reroute
- Audit: 6/7 passed (M1 missing_document follow_up_type known issue)

**Whether it was worth it**: Yes. Rerouting is a core design principle; now implemented.

---

## 6. Optional Loop 3

**Whether used**: No.

**Reason**: Main design is implemented. Remaining refinements (wording tweaks, visual hierarchy) are low-impact. Stopping allows founder validation before further polish. Avoids scope creep.

---

## 7. Validation Summary

| Check | Result |
|-------|--------|
| `run_inbox_triage_scenarios.py` | 53/53 passed |
| `run_multi_turn_simulations.py` | 38 passed |
| `audit_state_field_accuracy.py` | 6/7 passed (M1 known) |
| `verify_speed_routing.py` | OK |
| `guardrail_inbox_triage.sh` | PASS |
| `unified_intake_smoke_check.sh` | Guardrail pass; manual steps printed |
| `npm run build` | Success |

---

## 8. Frontend Redeploy Result

| Item | Value |
|------|-------|
| **Success/failure** | Success |
| **Production URL** | https://ui-39tqb9xpa-andys-projects-1f411b73.vercel.app |
| **Alias** | https://ui-smoky-beta.vercel.app |
| **Alias updated** | Yes |
| **Warnings** | Chunk size > 500 kB (pre-existing) |

---

## 9. Post-Deploy Inspection

**Directly visible**:
- Welcome card: "今天有什么可以帮您？"
- 5 buttons: 获取报价, 保单变更, 报事故, 付款/账单, 上传材料/联系客服
- Free-text input below
- Button selection toggles (primary when selected)
- Tabs: 客户入口 vs Broker Workbench

**What now feels better**:
- Welcoming first screen
- Guided start without forcing
- Free text always available
- Customer vs office separation clear

**What still feels weak**:
- Rerouting requires specific conflict (button ≠ text); subtle cases may not trigger
- "当前主题" tag during multi-turn is functional but could be refined

---

## 10. Founder Showcase (REQUIRED)

### Example 1: Button and text agree

- **User starts by clicking**: 获取报价
- **Then types**: 我想加一台2021 Tesla Model Y，下周提车
- **System does**: Proceeds in add-car flow; asks for zip if needed; handoff when enough
- **Why this is better**: Button gave a head start; flow feels natural

### Example 2: Button and text conflict

- **User starts by clicking**: 付款 / 账单
- **Then types**: 我想加一台新车，zip 90210
- **System does**: Detects add-car intent; returns reroute message "看起来这是加车报价相关的问题，我先帮您处理这个。" and proceeds with add-car triage
- **Why this is better**: User is not locked into wrong flow; system adapts and acknowledges

### Example 3: User comes in with free text only

- **User starts by clicking**: (none)
- **Then types**: 刚出事故了，要收集什么？
- **System does**: Triage infers claim_intake; proceeds normally
- **Why this is better**: Power users can skip buttons; no friction

### Example 4: User reaches case-creation point

- **User starts by clicking**: 获取报价
- **Then types**: 2021 Tesla Model Y，zip 90210，下周一提车
- **System does**: Handoff; case persisted; shows "已整理成 case，办公室会尽快跟进。" and "查看工作台" button
- **Why this is better**: Case creation is explicit; user knows office will follow up

### Example 5: User should be routed to office/human confirmation

- **User starts by clicking**: 付款 / 账单
- **Then types**: 我发了截图在微信，你们收到了吗
- **System does**: Missing-doc / payment flow; "Human confirmation recommended" for customer_says_sent; handoff with "好的，收到了" style draft
- **Why this is better**: Broker sees verify-before-acting; customer gets reassurance

---

## 11. Final Judgment

| Question | Answer |
|----------|--------|
| Is the hybrid unified entry model now well-designed? | Yes. Docs are detailed; design is explicit. |
| Was the design docs phase detailed enough? | Yes. Another worker could implement from the specs. |
| Did the product become more natural and friendlier? | Yes. Welcome + buttons + free text feel product-like. |
| Did button + free-text coexistence work better than expected or worse? | Better. Rerouting works; no lock-in. |
| Is the rerouting model clear enough? | Yes. Conflict detection and acknowledgment are implemented. |
| Is case-creation timing clearer? | Yes. "已整理成 case" when persisted. |
| What is the single best next move after this sprint? | Founder validation; then consider wording/visual polish and edge-case rerouting. |

---

## 12. Iteration Log (REQUIRED)

### Loop 1

- **What changed**: Welcome + 5 buttons + selected state + soft_route API + case-creation message
- **What got better vs prior**: First screen is welcoming; guided start; product-like
- **What did not improve**: Rerouting not implemented
- **Whether the loop was worth it**: Yes
- **Recommended next step**: Implement rerouting (Loop 2)

### Loop 2

- **What changed**: Backend reroute detection; frontend reroute display; "当前主题" tag
- **What got better vs Loop 1**: Rerouting works; soft-route messaging explicit
- **What did not improve**: Edge cases; audit M1
- **Whether the loop was worth it**: Yes
- **Recommended next step**: Founder validation; optional Loop 3 for polish

### Loop 3

- **Skipped**: No clearly valuable, low-risk refinement; stopping is right to avoid scope creep

---

## 13. 中文宏观总结

**为什么要做这个统一入口混合模型**：原来的入口像一个实验室工具，只有粘贴框，没有引导。创始人希望产品感觉友好、易上手、不吓人、能引导但不强迫。

**我们用了什么主要设计和方法**：欢迎语 + 5 个快捷按钮 + 自由输入。按钮是软引导，自由输入是最高优先级。当用户点的按钮和输入内容冲突时，系统会识别并说「看起来这是 [X] 相关的问题，我先帮您处理这个」，然后按输入内容处理。

**它的好处是什么**：更像真实 SaaS 产品；降低「不知道写什么」的焦虑；自由输入始终可用；不锁死流程。

**现在已经实现了什么**：欢迎卡片、5 按钮、选中状态、软路由 API、冲突时重路由及提示、case 创建提示、「当前主题」标签。

**还差什么**：边缘情况重路由、个别文案/视觉微调、M1 审计已知问题。

**下一步最该做什么**：创始人验证；根据反馈做小范围优化。

---

## 14. COPY/PASTE FOUNDER BLOCK

**Biggest design improvement**: Hybrid entry with welcome + 5 buttons + free text. Buttons are soft starters; free text overrides. Rerouting when button and text conflict.

**Biggest remaining weakness**: Reroute detection is rule-based; some edge cases may not trigger. Audit M1 (missing_document follow_up_type) known.

**Whether hybrid entry is the right direction**: Yes. Product feels more welcoming and product-like.

**Whether redeploy succeeded**: Yes. Alias https://ui-smoky-beta.vercel.app updated.

**What Andy should inspect next**: Open https://ui-smoky-beta.vercel.app/workbench/unified-intake → 客户入口 tab → see welcome + 5 buttons → click one, type conflicting message (e.g. 付款 then type 加车) → verify reroute message → complete flow to handoff → verify "已整理成 case".
