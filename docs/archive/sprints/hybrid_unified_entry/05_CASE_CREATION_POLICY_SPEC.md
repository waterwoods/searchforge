# Hybrid Unified Entry — Case Creation Policy Spec

**Sprint**: Hybrid Unified Entry System  
**Created**: 2026-03-15

---

## 1. When NOT to Create a Case Automatically

| Scenario | Behavior |
|----------|----------|
| **Informational only** | `manual_followup_needed = false`; no broker action; no case needed |
| **User says "先看看" / "不用了"** | Do not persist; user may just be exploring |
| **First message, not enough context** | Collect first; suggest case only when handoff_ready |
| **User explicitly declines** | "不用整理成 case" → Do not create |

---

## 2. When to Suggest Case Creation

| Trigger | Suggestion |
|---------|------------|
| `handoff_ready = true` | "Would you like me to organize this into a case so our office can follow up?" |
| Case already created (from triage persist) | No need to ask; show "Case created" and "查看工作台" |

**Timing**: At the moment of handoff, after the system has replied with the handoff message.

---

## 3. When to Strongly Recommend Case Creation

| Scenario | Wording |
|----------|---------|
| Urgent (critical/high) | "建议整理成 case，办公室会优先处理。" |
| Multi-turn collected | "资料已收集完整，建议整理成 case 让办公室跟进。" |
| User asked for help | Default: suggest; user can decline |

---

## 4. User Confirmation Copy

| Language | Suggestion |
|----------|------------|
| **Chinese** | "是否要整理成 case 让办公室跟进？" |
| **English** | "Would you like me to organize this into a case so our office can follow up?" |

**Optional secondary**: "整理后您可以在工作台查看进度。" (After organizing, you can check progress in the workbench.)

---

## 5. Customer-Visible vs Office-Visible Case Report

| Aspect | Customer | Office (Broker) |
|--------|----------|-----------------|
| **Case card** | Simplified: "已收到，办公室会尽快处理" | Full: urgency, next step, collected, still needed, draft |
| **Case ID** | Optional; not required for customer | Required for broker workflow |
| **Follow-up** | "有结果会联系您" | Full follow-up plan, notes, status |

Customer sees: reassurance + handoff message. Office sees: full triage output.

---

## 6. Implementation Notes

- **Current behavior**: Triage API already persists case when `persist_case=true`; frontend passes `true` for multi-turn
- **This sprint**: Add explicit case-creation suggestion in UI when `handoff_ready` — either as copy in the handoff card or as a confirmatory "整理成 case" button
- **Backend**: No change to persist logic; case is created when triage returns with case_id. UI clarifies the moment.

---

*See also: UX/Interaction Design Spec, Structured Intake Flow Spec*
