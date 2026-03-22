# Acceptance Criteria — Add-Car Transaction Clarity

## Must pass

- [ ] With Add-Car active conversation, customer sees a **current-transaction** strip (`当前办理：加车报价` or configured equivalent).  
- [ ] Progress card title for Add-Car is **not** generic `整理中` only — shows **加车报价 · 进度** (or configured).  
- [ ] On `handoff_ready`, handoff panel shows a **closure headline** before the system reply (Add-Car-specific copy configurable).  
- [ ] Handoff panel includes **boundary hint** for starting a different issue (`提交新问题`).  
- [ ] Add-Car handoff **toast** uses stronger office-submitted wording when `case_id` + handoff (no duplicate weak toasts for that path).  
- [ ] `configs/clients/chen_kui/ui_copy.json` includes new keys; API `get_ui_copy` returns them.  
- [ ] `handoff_phrases.json` add_car line reinforces **办公室已接手 / 已提交处理** semantics.  
- [ ] `bash scripts/guardrail_inbox_triage.sh` passes.  
- [ ] `cd ui && npm run build` passes if UI changed.  
- [ ] Founder scenario runner completes; manual judgment recorded in final report.

## Non-blocking

- English parity: defaults provided; Chen Kui primary is Chinese.  
- Workbench one-line context is **nice-to-have** clarity, not a new workflow.
