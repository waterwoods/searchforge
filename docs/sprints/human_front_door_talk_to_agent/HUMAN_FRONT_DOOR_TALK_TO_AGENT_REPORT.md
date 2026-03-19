# Human Front Door + Talk-to-Agent Report

**Sprint:** Human Front Door + Talk-to-Agent Sprint  
**Scope:** Chen Kui Insurance Unified Entry  
**Date:** 2026-03-15

---

## 1. Sprint Theme

**What was chosen:** Upgrade the Unified Entry front door so it feels more like a real customer-facing service and less like an internal demo tool. Focus on: (1) more human and reassuring entry, (2) clear Talk-to-Agent path, (3) business-readable case summary, (4) trust and sellability.

**Why now:** The founder agreed that before customers care about durable architecture, they first need to feel understood, reassured, not trapped, and able to reach a real human when needed. The product has strong logic but needed a stronger front door.

---

## 2. Document Set Created

| Doc | Path |
|-----|------|
| Product Blueprint | `docs/sprints/human_front_door_talk_to_agent/01_PRODUCT_BLUEPRINT.md` |
| UX / Interaction Design Spec | `docs/sprints/human_front_door_talk_to_agent/02_UX_INTERACTION_DESIGN_SPEC.md` |
| Execution Outline | `docs/sprints/human_front_door_talk_to_agent/03_EXECUTION_OUTLINE.md` |
| Acceptance / SLA Criteria | `docs/sprints/human_front_door_talk_to_agent/04_ACCEPTANCE_SLA_CRITERIA.md` |
| Talk-to-Agent Policy Spec | `docs/sprints/human_front_door_talk_to_agent/05_TALK_TO_AGENT_POLICY_SPEC.md` |
| Founder Demo / Inspection Notes | `docs/sprints/human_front_door_talk_to_agent/06_FOUNDER_DEMO_INSPECTION_NOTES.md` |

---

## 3. Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Welcome / reassurance** | "今天有什么可以帮您？" + "如需人工协助，可点击「联系人工」。您的消息会直接转给办公室，我们会尽快处理。" | Warm, office-assistant tone; explicit human path; office connection |
| **Talk-to-Agent** | 6th button "联系人工", always visible, immediate handoff with "我想联系陈奎办公室" | No multi-turn; user clicked = we honor it; broker sees "Customer requested human contact" |
| **Customer-facing wording** | CUSTOMER_FIELD_LABELS_ZH for Case Summary (年份, 车型, 邮编) | Business-readable, not developer field names |
| **Business-readable summary** | humanizeStructuredFieldForCustomer() in Customer Entry Case Summary | Broker notes feel; customer sees "已收集：年份、车型、邮编" |
| **Trust boundary** | "办公室会尽快处理，有结果会联系您" / "您的消息会直接转给办公室" | No false promises; office follow-up clear |

---

## 4. Iteration Loop 1

**What changed:** Header paragraph, welcome card secondary, examples button ("不确定说什么？点这里看示例"), loading message ("正在整理，马上就好...").

**What became more welcoming:** Secondary copy now explicitly says messages go to the office. Examples more discoverable.

**What became more reassuring:** "您的消息会直接转给办公室" in header and welcome card.

**What did not improve:** Talk-to-Agent not yet added; Case Summary still raw field names.

**Whether it was worth it:** Yes.

---

## 5. Iteration Loop 2

**What changed:** 6th button "联系人工"; backend soft_route=talk_to_agent → immediate handoff; split "上传材料/联系客服" into "上传材料" + "联系人工"; Case Summary humanized (年份, 车型, 邮编); welcome card "如需人工协助，可点击「联系人工」".

**What improved vs loop 1:** Talk-to-Agent path clear; Case Summary business-readable.

**What still remained weak:** URL /workbench/unified-intake; header may show "Unified Intake".

**Whether it was worth it:** Yes. Single biggest audit weakness addressed.

---

## 6. Optional Loop 3

**Whether used:** No. No single clear refinement justified another loop.

---

## 7. Validation Summary

- `cd ui && npm run build`: PASS
- `bash scripts/guardrail_inbox_triage.sh`: PASS
- `bash scripts/unified_intake_smoke_check.sh`: PASS
- talk_to_agent test added to test_inbox_triage_api.py

---

## 8. Redeploy Result

- **Frontend:** Success
- **Backend:** Not required (route in existing service)
- **Production URL:** https://ui-ge7nlqyry-andys-projects-1f411b73.vercel.app
- **Alias:** https://ui-smoky-beta.vercel.app (updated)

---

## 9. Post-Deploy Inspection

**Directly visible:** 6 buttons including "联系人工"; welcome with office + human path; Case Summary "已收集：年份、车型、邮编"; click "联系人工" → immediate handoff.

**What still feels weak:** URL and header branding.

---

## 10. Founder Showcase

### Example 1 — User wants reassurance
- **User sees:** Lands on page
- **System now says:** "今天有什么可以帮您？" + "如需人工协助，可点击「联系人工」。您的消息会直接转给办公室，我们会尽快处理。"
- **If user wants a human:** Clicks "联系人工" → immediate handoff
- **Why better:** Office connection and human path visible before typing

### Example 2 — User wants quote help
- **User clicks:** "获取报价", types "2024 BMW X5"
- **System now says:** "好的，宝马X5。" then asks for zip
- **Summary now reads:** "已收集：年份、车型" / "还需：邮编、提车日期"
- **Why better:** Business-readable labels

### Example 3 — User wants human contact
- **User clicks:** "联系人工"
- **System now says:** "好的，已帮您转给陈奎办公室，他们会尽快联系您。"
- **Broker sees:** "Customer requested human contact. Call or message back promptly."
- **Why better:** One click; no form; broker knows to call back

### Example 4 — User reaches handoff
- **User:** Add-car flow, provides year, model, zip
- **System now says:** "报价资料已收集，办公室会尽快出价，有结果会联系您。"
- **Summary now reads:** "已收集：年份、车型、邮编"
- **Why better:** Business-readable; office follow-up clear

### Example 5 — Payment help
- **User clicks:** "付款 / 账单"
- **If user wants a human:** Clicks "联系人工" anytime
- **Why better:** Human path available; no feeling trapped

---

## 11. Final Judgment

1. **More human?** Yes.
2. **More reassuring?** Yes.
3. **Talk-to-Agent clear enough?** Yes.
4. **Business-readable summary better?** Yes.
5. **More trustworthy to small customer?** Yes.
6. **Best next step:** Replace "Unified Intake" in header with "客户服务"; consider /support URL.

---

## 12. Iteration Log

**Loop 1:** Welcome, examples, loading → more welcoming. Worth it. Next: Loop 2.

**Loop 2:** Talk-to-Agent + humanized summary → path clear, summary readable. Worth it. Next: Deploy.

**Loop 3:** Skipped.

---

## 13. 中文宏观总结

**为什么先做：** 客户先要感到被理解、能联系真人，才关心架构。

**设计方法：** 欢迎语强调「转给办公室」；第六按钮「联系人工」一点即转；Case Summary 用人话（年份、车型、邮编）。

**好处：** 入口更像真实客服；客户不觉得被困；办公室收到「Customer requested human contact」。

**已实现：** 6 按钮含「联系人工」；欢迎卡有办公室和人工说明；摘要人话标签；点击即转。

**还差：** URL 和页头「Unified Intake」仍偏内部。

**下一步：** 页头改为「客户服务」；可选 /support URL。

---

## 14. COPY/PASTE FOUNDER BLOCK

**Biggest improvement:** 6th button "联系人工" + immediate handoff; welcome says "您的消息会直接转给办公室"; Case Summary "年份、车型、邮编".

**Biggest weakness:** URL and "Unified Intake" header still internal.

**Talk to Agent clear?** Yes. Always visible; one click → handoff.

**Redeploy succeeded?** Yes. https://ui-smoky-beta.vercel.app. Alias updated.

**Inspect next:** https://ui-smoky-beta.vercel.app/workbench/unified-intake → Customer Entry → welcome, 6 buttons, click "联系人工", Case Summary labels.
