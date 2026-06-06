# Execution Outline — PRODUCT_READINESS_GAP_ASSESSMENT_SPRINT

**Mode:** Document-driven assessment (this execution is **inspection + scoring**, not implementation).  
**Budget:** 45–90 minutes (single pass + write-up).

---

## Phase A — Inventory (≈15–25 min)

1. Read **north star** docs: `docs/goals/insurance_paid_pilot_goal.md`, `docs/STANDARD_SCENARIO_PACKAGE.md`.  
2. Read **recent sprint outcomes:**  
   - `NARROW_POSITIONING_AND_OPERATOR_VALUE_SPRINT/FINAL_REPORT.md`  
   - `SECOND_BROKER_CLIENT_PACK_DRILL/FINAL_REPORT.md`  
   - `PRE_BROKER_TARGETED_ACCEPTANCE_SPRINT/05_FINAL_REPORT.md`  
   - `CLIENT_PACK_OPERATING_MANUAL_PRODUCTIZATION_INDEX/PRODUCTIZATION_INDEX.md` (orientation)  
3. Skim **trial index:** `docs/trial/INDEX.md` for pilot artifact completeness.

---

## Phase B — Engine & config audit (≈15–25 min)

1. Confirm triage contract: `triage.py` — `REQUIRED_FIELDS`, `WORKFLOW_STATE_KEYS`.  
2. Confirm config layering: `config_loader.py` — industry vs client merge, defaults.  
3. Confirm persistence stance: `case_store.py` — JSON demo-safe model, env path.  
4. Confirm API surface shape: `routes/inbox_triage.py` — triage, client-config, case endpoints (prefix skim).

---

## Phase C — UI & client experience (≈10–20 min)

1. `UnifiedIntakePage.tsx` — tabs, customer vs workbench intent, density signals.  
2. `clientConfig.ts` — breadth of `ui_copy`; default Chen strings.

---

## Phase D — Validation discipline (≈10–15 min)

1. Read `scripts/guardrail_inbox_triage.sh` — enumerate gates.  
2. Note scenario runner dependencies — strength of regression story.

---

## Phase E — Score + gap + prioritize (≈15–25 min)

1. Complete `PRODUCT_READINESS_SCORECARD.md` (12 goals).  
2. Classify gaps in `GAP_ANALYSIS_SPEC.md`.  
3. Write roadmap + next 3 sprints in `PRIORITY_ROADMAP_SPEC.md` and `FINAL_REPORT.md`.  
4. **Founder Inspection Notes** — bullets for live demo discipline.  
5. **中文总结** in `FINAL_REPORT.md` — mandatory.

---

## Outputs checklist

- [x] Blueprint  
- [x] Assessment framework spec  
- [x] Scorecard + summary table  
- [x] Gap analysis spec  
- [x] Priority roadmap spec + next-3 sheet  
- [x] Execution outline (this file)  
- [x] Founder inspection notes  
- [x] Final report (full narrative + judgment + Chinese)

---

## Loops (if time allows)

- Re-run `bash scripts/guardrail_inbox_triage.sh` locally to confirm green (not required for doc validity if environment differs).  
- Spot-check `configs/clients/chen_kui/` vs `socal_precision/` for pack parity.

---

*End of execution outline*
