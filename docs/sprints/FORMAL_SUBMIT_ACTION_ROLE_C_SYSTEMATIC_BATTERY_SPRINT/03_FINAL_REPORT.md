# FORMAL SUBMIT ACTION + ROLE C SYSTEMATIC BATTERY — Final report

## What was implemented

- **Chen Kui `ui_copy.json`:** Stronger CTA **「正式提交办公室（送达处理队列）」**; expanded `portal_handoff_pending_cta_hint` (三件事分清楚); new **`portal_handoff_pending_button_subline`**; new **`portal_handoff_pending_empty_submit_line`**; aligned flow explainer + record-rail completion hint + alert title.
- **`UnifiedIntakePage.tsx`:** On `handoff_pending`, empty input uses the configurable formal-submit line; **subline under primary button** when the handoff-pending alert shows.
- **`clientConfig.ts`:** Types for the two new copy keys.
- **`AddCarFlowExplanation.tsx`:** Default fallback line2 aligned with new CTA wording.
- **`run_role_c_add_car_battery.py`:** Preset **`handoff_loop`** (C1–C5 per sprint spec); trace entries include **`lifecycle_status`**, **`handoff_ready`**, **`case_persisted`**, **`has_case_id`**.

## What was run

- **`bash scripts/guardrail_inbox_triage.sh`:** PASS (full scenario / multi-turn / simulation packs).
- **Live Role C `handoff_loop` battery:** **Not run** — no `fiqa_api` on `127.0.0.1:8001` in this environment (guardrail API step skipped).

## Issues found (evidence-based vs inferred)

### Directly verified (code / guardrail)

- **C. State / lifecycle (architecture note):** With **`persist_case: true`**, the triage route **persists as soon as `handoff_ready`** and returns a case with **`lifecycle_status: handed_off`**. The portal therefore often **skips** the in-session **`handoff_pending`** surface unless persistence fails or flows use `persist_case: false` (e.g. simulation). **Severity: high for product truth vs UI.** *Inferred from `inbox_triage.py` + `case_store.save_case` + portal `triageMessage(..., true)`.*

### From static review (needs live Role C + broker pass)

- **B. Handoff truth:** Role C may still surface **timeline / coverage** questions where replies must stay **non-binding**; battery is the right instrument once live.
- **A. Formal submit clarity:** If customers rarely see `handoff_pending` on the live portal, **copy hardening** helps sim/workbench/consistency but **deferring persist until formal submit** would be the deeper alignment (out of this sprint’s risk budget).

## What remains partial

- Live **`handoff_loop`** execution and JSONL harvest.
- Optional backend change: **defer Add-Car case persistence** until explicit formal submit (separate sprint; touches `routes/inbox_triage.py` + tests).

## Recommended next sprint

**「Add-Car formal submit + persist gate」** — align `handoff_pending` with live portal: only create/persist case when customer sends formal submit (or equivalent), keep JSON/session until then; re-run guardrail + Role C `handoff_loop` live.
