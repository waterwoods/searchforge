# State / Workflow Phase 2.5 — Execution Outline

---

## Phase A — Control Docs (Done)

1. Sprint Blueprint
2. Execution Outline
3. Acceptance / Operational Criteria
4. Founder Cross-Window Summary Notes

---

## Phase B — Baseline Recheck

Inspect:
- session continuity behavior
- workflow_state shape
- next_best_question visibility
- lifecycle_status visibility
- workbench visibility
- remaining fragility
- anything still too ambiguous or too hidden

Classify: strong | acceptable | weak | blocking | demo-only | needs hardening

---

## Phase C — Iteration Loops

### Loop 1: Harden Core Backbone

Targets:
- Tighten session/conversation semantics
- Tighten workflow_state consistency
- Improve lifecycle visibility wording
- Improve frontend/backend field coherence
- Strengthen 1–2 high-value guardrails

**Do NOT overbuild.** Smallest high-value slice.

After loop 1: run all validation scripts + UI build.

### Loop 2: Small High-Value Visibility / Coherence

Targets:
- Slightly better in-progress vs handed-off labeling
- Clearer "next step" visibility
- Cleaner state display in workbench
- Stronger state contract guardrail

**Do NOT redesign the UI.** Do NOT broaden scope.

### Loop 3: Optional

Only if one clearly valuable, low-risk refinement remains. Otherwise stop.

---

## Phase D — Deploy

- Backend: `bash scripts/deploy_rag_demo.sh`
- Frontend: `cd ui && vercel --prod`
- Capture URLs, revision, success/failure

---

## Phase E — Post-Deploy Verification

- Backend ready/health
- Add-car flow: next_best_question / collecting behavior
- Payment or missing-doc flow: state visibility
- Workbench / case detail: lifecycle visibility

---

## Phase F — Final Report

- What was hardened
- What was deployed
- What improved vs before
- What still remains weak
- Cross-window summary block
