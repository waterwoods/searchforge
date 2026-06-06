# Human Front Door + Talk-to-Agent — Acceptance / SLA Criteria

**Sprint:** Human Front Door + Talk-to-Agent Sprint  
**Created:** 2026-03-15

---

## 1. What Counts as More Human

| Criterion | Pass | Fail |
|-----------|------|------|
| Welcome copy | Warm, office-assistant tone | Robotic, technical |
| First response | Acknowledges then asks | "请提供更多信息" when intent clear |
| Handoff message | "办公室会尽快处理，有结果会联系您" | Generic or missing |
| Examples | "不确定说什么？点这里看示例" or equivalent | "需要示例？" tucked away, unclear |

---

## 2. What Counts as More Reassuring

| Criterion | Pass | Fail |
|-----------|------|------|
| Office connection | "您的消息会直接转给办公室" or equivalent | No mention of office |
| Follow-up | "有结果会联系您" | Vague or absent |
| Urgent cases | "今天尽快处理" when critical | Same as low urgency |
| Human path | "如需人工协助，可点击「联系人工」" | No mention |

---

## 3. What Counts as Clear Human Handoff

| Criterion | Pass | Fail |
|-----------|------|------|
| Button visibility | "联系人工" in button set, always visible | Missing or hidden |
| Click behavior | Immediate handoff, no multi-turn | Routes to missing_document |
| Broker sees | "Customer requested human contact" in broker_next_step | Generic category |
| Customer sees | "已帮您转给陈奎办公室，他们会尽快联系您" | Generic handoff |

---

## 4. What Counts as Business-Readable Case Summary

| Criterion | Pass | Fail |
|-----------|------|------|
| Collected labels | "年份、车型、邮编" or "Year, Make/Model, ZIP" | "year, make_model, zip" |
| Still needed labels | "提车日期、主驾信息" | "delivery_date, primary_driver" |
| Intent label | "新车报价" or "Add car quote" | "add_car" |
| Broker notes feel | Readable by office staff | Developer field names |

---

## 5. What Counts as Still Too Prototype-Like

| Anti-Pattern | Example |
|--------------|---------|
| Technical labels in customer view | "collected: year make_model" |
| No human path | User wants human, can't find it |
| Internal jargon | "Unified Intake" in customer header |
| Robotic copy | "请提供更多信息" when intent clear |
| Hidden examples | "需要示例？" small, easy to miss |

---

## 6. SLA for This Sprint

- All Loop 1 and Loop 2 changes must pass: `cd ui && npm run build`
- Existing scripts (run_inbox_triage_scenarios, guardrail_inbox_triage) must not regress
- Talk-to-Agent flow must create a case with `broker_next_step` containing "Customer requested human contact"

---

*See also: UX Design Spec, Talk-to-Agent Policy*
