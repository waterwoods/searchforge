# Submit path + readiness — Spec

## Ambiguity points (before)

- Primary CTA stayed **「提交补充」** even when lifecycle was `handoff_pending`, conflating “keep typing” with “send to office”
- Flow explainer always read like generic **step 2 collecting**, even when the system had already marked **资料已齐 · 可提交**
- Workbench had lifecycle tags and `broker_next_step`, but **no compact “readiness mirror”** stating whether the office should wait for customer submit vs proceed
- Queue **readiness chip** did not surface `handoff_pending` distinctly for Add-Car

## Target customer-side clarity

- **Collecting:** “继续补充” / normal placeholders; flow explainer = 补齐缺项
- **Handoff pending:** dedicated flow-explainer card; primary CTA = **「正式提交办公室」**; optional warning `Alert` + placeholder explaining optional note; right-rail completion hint references the same CTA label
- **After submit (`handoff_ready`):** unchanged post-handoff closure path

## Target workbench readiness parity

- For Add-Car cases, show a **「加车 · 接手就绪度（与客户入口同源）」** block with:
  - **handoff_pending:** headline “待客户正式提交” + body explaining do not promise final premium until customer submits on the portal
  - **handed_off / office_followup:** “已报送 · 可接手处理” + optional appended missing fields
  - **Otherwise (collecting):** “信息收集中” + missing fields when present

## Acceptance criteria

- [x] When `lifecycle_status === 'handoff_pending'` on Add-Car, primary submit label is not the same as generic follow-up submit
- [x] Flow explanation layer switches copy for `handoff_pending` vs normal pre-handoff
- [x] Workbench shows readiness mirror for Add-Car when a case is open
- [x] Queue list shows **待客户提交** for Add-Car + `handoff_pending`
- [x] `npm run build` passes for `ui/`
- [ ] Manual browser pass on live triage (depends on backend emitting `handoff_pending`)
