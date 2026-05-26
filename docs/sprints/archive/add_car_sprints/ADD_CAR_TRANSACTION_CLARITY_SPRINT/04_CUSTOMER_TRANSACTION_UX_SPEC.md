# Customer Transaction UX Spec (Unified Entry)

## Page: 客户服务入口 (`CustomerEntryTab`)

### Empty state

- Unchanged hero and quick-start grid.  
- Hybrid add-car block remains **加车报价 · 快速填写（可选）**.

### Active conversation

- **Transaction ribbon** (Add-Car only): full-width subtle banner under hero, before chat transcript.  
- **Transcript**: existing bubbles; office label from `office_label`.  
- **Progress card**: transaction-titled when Add-Car; shows structured progress.  
- **Composer**: `当前办理` + `加车报价` when Add-Car; otherwise retain `当前主题` behavior.  
- **Handoff card**: green closure panel with headline → reply → processing → boundary → buttons.

### Toasts

- On `handoff_ready` + Add-Car: `add_car_handoff_toast` (stronger than generic `handoff_default`).  
- Other flows: keep `handoff_default`.  
- Avoid double-toast noise: when both `case_id` and `handoff_ready`, prefer a **single** toast (Add-Car handoff message wins when applicable).

## Accessibility / tone

- Short sentences, office Chinese, no slang.  
- No false precision (no fake ticket numbers).

## Regression checks

- Non–Add-Car flows still get generic closure headline + same buttons.  
- Reroute away from Add-Car clears ribbon semantics (intent cleared or triage no longer Add-Car).
