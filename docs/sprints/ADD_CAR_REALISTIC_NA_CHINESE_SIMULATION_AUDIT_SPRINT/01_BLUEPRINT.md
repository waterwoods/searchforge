# ADD-CAR REALISTIC NORTH-AMERICAN-CHINESE SIMULATION AUDIT — Blueprint

## Sprint goal

Stress-test Unified Intake Add-Car against **realistic North American Chinese** customer phrasing (mixed 中英、微信体、材料/VIN/家属驾驶人/改口/比价), and judge **intake understanding** plus **office-useful replies**—not “looks professional.”

## Why now

`docs/PROJECT_TRUTH_SWITCH.md` states Add-Car is the flagship monetizable path; broker pilots will be judged on real phrasing, not UI polish. Risk: professional portal + weak or misrouted conversational intake.

## Scope

- Phrasing pattern collection (web-light + synthesized).
- Rule-path simulation battery (`triage_conversation`, `LLM_GENERATION_ENABLED=0`).
- Failure mapping and small, evidence-backed triage fixes.
- Lightweight sprint docs (this folder only).

## Non-scope

- CRM/auth/deploy, triage engine rewrite, large UI redesign, full market study, heavy new test frameworks.

## What we are testing

1. Intent + slot capture (year/model/zip/delivery/driver/VIN/materials).
2. Category guardrails (e.g. add-car vs missing_document vs premium_review).
3. Customer-visible draft usefulness (next step, not empty politeness).

## Target outcome

- Clear map: which NA-Chinese patterns are **strong**, **weak**, or **broken** on the rule path.
- Optional **small** code/config fixes with guardrail green.
- Founder-readable answers on pilot readiness and next sprint.
