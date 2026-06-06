# ADD-CAR FIRST-TIME CLARITY + REALISTIC INTAKE HARDENING — Final report

## What changed

- **First-time clarity:** Portal hero/empty-state copy now states that Add-Car is the usual main path, lists three entry modes (button / free text / structured card), and states that submission becomes a business record reviewed by the office (not auto-binding). Add-Car quick-start uses primary styling when no intent is selected, with a small「常用」tag.
- **Intake hardening (rule-based):** Expanded delivery routing and field signals (Friday / pickup / calendar 月日 + 提), driver markers (主要我本人、我跟老婆都可能开), material-state `collected_fields` (`materials_send_question`, `materials_still_pending`, `customer_says_materials_sent`), tightened VIN detection to avoid false positives from「VIN还没拿到」and「要不要先发VIN」style offers.
- **Validation:** New script `scripts/run_add_car_realistic_intake_scenarios.py` (R1–R7). `bash scripts/guardrail_inbox_triage.sh` PASS. `cd ui && npm run build` PASS.

## What was tested

- Full inbox triage guardrail (including multi-turn, adversarial, append boundary, cross-client).
- Add-Car realistic battery R1–R7 under `LLM_GENERATION_ENABLED=0`.

## What improved

- First-time users get explicit guidance on how to start and what happens after submit.
- Add-Car is visually emphasized as the default path.
- More realistic Chinese/English phrasing maps to structured fields; VIN false positives reduced for common colloquial phrases.

## What remains

- **R4-style messages** without a model year (e.g. only「BMW X5」) still yield `need_more` until a year appears — correct for quote readiness, not full “latest date wins” extraction in a narrative summary.
- **LLM-enabled deployments** may differ from rule-only tests; re-validate with `LLM_GENERATION_ENABLED=1` if used in pilot.

## Recommended next sprint

- Optional: resolve a **single canonical delivery phrase** when multiple dates appear (last customer clause wins) for broker summary text, not only boolean flags.
- Light **UI A/B** on empty-state length if operators find copy too dense on mobile.
