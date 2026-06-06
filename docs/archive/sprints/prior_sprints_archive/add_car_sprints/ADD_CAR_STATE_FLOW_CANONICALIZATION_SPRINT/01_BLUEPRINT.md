# ADD-CAR STATE + FLOW CANONICALIZATION — Blueprint

## Sprint goal

Tighten Add-Car so **customer portal, result card, and office workbench** read as **one service record** moving through **one practical state vocabulary**, with **clear customer vs office next-action** framing—without a workflow-engine rewrite.

## Why now

Scorecard V1 already rated PAGE strongly; **STATE** and **FLOW** sit at **3/5** because the experience is still partly thread-shaped and state language is not fully unified across surfaces. The master outline calls for **state-driven flow migration** with chat as input only; this sprint is a **small, bounded** step in that direction before broader pilot validation.

## Required read-first docs

1. `docs/UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md` — macro blueprint (Add-Car wedge, state-driven migration, client packs, technical evolution).
2. `docs/PROJECT_TRUTH_SWITCH.md` — canonical paths, edit risk, validation gate.
3. `docs/sprints/ADD_CAR_INDUSTRIAL_SCORECARD_V1_SPRINT/02_ADD_CAR_INDUSTRIAL_SCORECARD_V1.md` — baseline scores and gaps.
4. `docs/sprints/ADD_CAR_INDUSTRIAL_SCORECARD_V1_SPRINT/03_FINAL_REPORT.md` — recommended follow-ups.

## Scope

- Canonical **state** language alignment (lifecycle + strip + workbench echo).
- Canonical **next-action** labeling (customer vs office) via client pack where helpful.
- **Continuity** cues: same captions and office next-step wording between result card and queue preview.
- Lightweight **tech-fit** note in spec (no stack replacement).

## Non-scope

- Full workflow engine, CRM, auth, billing.
- Broad UI redesign or non–Add-Car flows.
- Backend refactor of `triage.py` beyond tiny consistency if needed (this sprint: **frontend + config** first).

## Target outcome

- One **documented** canonical state/next-action/continuity model.
- **Small** UI/config changes that make STATE/FLOW easier to scan and more consistent across surfaces.
- Clear statement of **what remains** and **recommended next sprint**.
