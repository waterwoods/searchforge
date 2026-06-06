# ADD-CAR Pilot Verification + Handoff Credibility + Conditional Deploy — Blueprint

## Sprint goal

Answer one question with evidence: **Is the current Add-Car flagship path strong enough for constrained friend/broker pilot testing?**  
Secondarily: **Is handoff credible enough** that a broker would trust “office received this”?  
**Deploy frontend/backend only if a clear release gate passes**; otherwise stop and document blockers.

## Why now

Prior sprints improved Add-Car-first framing, result/service-record feel, state visibility, workbench echo, and handoff copy. The commercial decision is no longer “can we demo?” but **“is it credible enough to put in front of a real broker?”** This sprint closes that loop with practical validation and an honest deploy decision.

## Read-first (alignment)

1. `docs/UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md` — Stage 1 = intake + structuring + office handoff; Add-Car = flagship wedge; not carrier execution.
2. `docs/PROJECT_TRUTH_SWITCH.md` — canonical path, persistence truth, validation gate, deploy caution.
3. `docs/sprints/ADD_CAR_INDUSTRIAL_SCORECARD_V1_SPRINT/02_ADD_CAR_INDUSTRIAL_SCORECARD_V1.md` — PAGE/HANDOFF strengths and FLOW/STATE/HANDOFF gaps.
4. `docs/sprints/ADD_CAR_INDUSTRIAL_SCORECARD_V1_SPRINT/03_FINAL_REPORT.md` — conservative scores and recommended follow-ups.

## Scope

- Add-Car pilot-readiness and handoff-trust validation (rule path + config + UI wiring).
- Workbench continuity as inferable from UI copy + engine outputs (and live checks when possible).
- Small, bounded fixes only if a **clear** release blocker appears.
- Release gate + conditional deployment **when credentials and process allow**.

## Non-scope

- Product redesign, architecture passes, non–Add-Car expansion, CRM/carrier APIs, large doc sets.

## Target outcome

- Explicit **PASS / PASS WITH CAUTIONS / FAIL** for constrained pilot release.
- Record what was verified vs inferred vs not run.
- Deploy only if gate passes **and** deploy is actually executed successfully; otherwise record why deploy did not happen.
