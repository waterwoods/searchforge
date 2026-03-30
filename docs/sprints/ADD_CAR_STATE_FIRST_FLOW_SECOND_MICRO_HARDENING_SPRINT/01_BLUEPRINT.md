# ADD-CAR STATE-FIRST / FLOW-SECOND MICRO-HARDENING — Blueprint

## Sprint goal

Push Add-Car **one notch** toward a single business record with **scannable state**, **clear next actions** (customer + office), and **aligned customer / result / workbench** presentation—without redesigning the page or rewriting the engine.

## Why now

`PROJECT_TRUTH_SWITCH.md` and Add-Car Industrial Scorecard V1 agree: **PAGE** and handoff copy are relatively strong; **STATE** and **FLOW** remain the main gaps—especially state visibility, continuity between customer closure and office queue, and task-shaped clarity versus chat-shaped history.

## Scope

**In scope**

- Add-Car-only UI/state presentation on Unified Intake (customer progress, post-handoff result card, workbench queue + opened record).
- Config keys for one new customer-facing lane heading (optional client override).
- Lightweight validation (frontend build).

**Out of scope**

- Backend / triage engine changes, broad handoff rewrite, non–Add-Car flows, CRM, deployment, large doc sets.

## Remaining gap this sprint targets

- Pre-handoff: customer “where am I / what do I do next” was split across tags and a generic “下一步（系统建议）” block—**not one primary lane**.
- Post-handoff Add-Car: **办公室侧下一步** sat below several dividers and panels—**not immediately after record identity**.
- Workbench: queue cards had tags but **not the same Add-Car status strip** as the customer result card—**weaker same-record / same-state-world** feel.

## Target outcome

- **STATE:** Same strip vocabulary on customer progress, post-handoff (already), queue, and detail.
- **FLOW:** Customer next step is one bordered lane driven by `lifecycle_status` / gaps / `next_best_question`; office next step is earlier on the Add-Car closure card.
