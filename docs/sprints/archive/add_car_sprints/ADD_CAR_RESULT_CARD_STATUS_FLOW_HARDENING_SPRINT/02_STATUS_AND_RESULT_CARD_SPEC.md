# Add-Car status + result card spec

## Desired result-card structure (customer entry)

1. **Case identity** — Always visible for Add-Car: “加车报价” as the transaction type (not generic “咨询”).
2. **Status strip** — One horizontal band (non-chat) with ordered chips:
   - Identity: `加车报价`
   - **Intake (pre-handoff):** quote readiness (`quote_ready_status`) + lifecycle (`lifecycle_status`) or, if lifecycle absent, `collection_stage` (可交办公室 / 信息收集中).
   - **Submitted (handoff_ready):** `已报送办公室` + optional quote + lifecycle chips when present.
3. **Record reference** — When `case_id` exists: show short copyable **服务记录编号**.
4. **Structured body** — Keep existing panels: 已记录要点 / 仍缺待补充 / 整理度.
5. **Next steps** — Customer prep (`client_prep`), timing copy, then **办公室侧下一步** from `broker_next_step` when non-empty.
6. **Customer-facing summary** — Existing “办公室办理摘要” block remains the reply surface.
7. **Boundary** — Explicit section: same-case append (collapse) vs **提交新问题**; short rule text before CTAs.

## Status model (presentation only)

Map existing fields; do not invent server states.

| Signal | Presentation |
|--------|----------------|
| `quote_ready_status` | 可报价 / 差一点 / 信息不足 |
| `lifecycle_status` | 信息收集中 / 待确认提交 / 已交办公室 / 办公室跟进 |
| `collection_stage` | Fallback when lifecycle missing: 可交办公室 vs 信息收集中 |
| `handoff_ready` + customer view | Primary: 已报送办公室 |

## Same-case vs new-case

- **Same case:** Collapse “追加到本条记录” — corrections, VIN, screenshots for **this** add-car record.
- **New issue:** Primary ghost button “提交新问题” — different topic; must not mix into the same thread casually.

## Office-handoff framing

- Processing lines + timing stay in Alerts/info blocks.
- `broker_next_step` surfaced as **办公室侧下一步（系统整理）** to separate operational intent from the customer reply draft.

## Acceptance criteria

- [ ] Add-Car shows a **dedicated status strip** on both pre-handoff progress card and post-handoff result card.
- [ ] **Case id** visible when persisted.
- [ ] **broker_next_step** visible when returned for Add-Car handoff.
- [ ] Boundary section makes **continue vs new** obvious without new APIs.
- [ ] No changes to triage persistence contracts.
