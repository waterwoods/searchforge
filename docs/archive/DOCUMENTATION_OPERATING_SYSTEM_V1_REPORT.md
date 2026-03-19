# Documentation Operating System v1 Report

**Sprint:** Documentation Operating System v1  
**Date:** 2026-03-07  
**Scope:** California Auto Insurance Broker Assistant only

---

## 1. Structure created or confirmed

| Category | Path | Status |
|----------|------|--------|
| goals | `docs/goals/` | Existed; added BROKER_ASSISTANT_MASTER_GOAL.md bridge + INDEX.md |
| standards | `docs/standards/` | Created; symlinked BROKER_DEMO_QUALITY_STANDARD + INDEX.md |
| runbooks | `docs/runbooks/` | Created; symlinked RUNTIME_PATH_STANDARD, BROKER_VALUE_VALIDATION_MEETING_PACK + INDEX.md |
| guardrails | `docs/guardrails/` | Created; symlinked BROKER_DEMO_DRIFT_GUARDRAIL + INDEX.md |
| reports | `reports/` | Created; INDEX.md pointing to broker reports in docs/ |

---

## 2. Main docs and where they live

| Doc | Location | Notes |
|-----|----------|-------|
| BROKER_ASSISTANT_MASTER_GOAL | `docs/goals/BROKER_ASSISTANT_MASTER_GOAL.md` | Bridge → insurance_paid_pilot_goal.md |
| BROKER_DEMO_QUALITY_STANDARD | `docs/standards/BROKER_DEMO_QUALITY_STANDARD.md` | Symlink to docs/BROKER_DEMO_QUALITY_STANDARD.md |
| RUNTIME_PATH_STANDARD | `docs/runbooks/RUNTIME_PATH_STANDARD.md` | Symlink to docs/RUNTIME_PATH_STANDARD.md |
| BROKER_VALUE_VALIDATION_MEETING_PACK | `docs/runbooks/BROKER_VALUE_VALIDATION_MEETING_PACK.md` | Symlink to docs/BROKER_VALUE_VALIDATION_MEETING_PACK.md |
| BROKER_DEMO_DRIFT_GUARDRAIL | `docs/guardrails/BROKER_DEMO_DRIFT_GUARDRAIL.md` | Symlink to docs/BROKER_DEMO_DRIFT_GUARDRAIL.md |
| reports/INDEX | `reports/INDEX.md` | Index of broker sprint/diagnosis reports |

All original paths (`docs/BROKER_*.md`, etc.) still work; symlinks provide canonical locations.

---

## 3. What was consolidated or linked

- **BROKER_ASSISTANT_MASTER_GOAL:** New bridge doc pointing to `insurance_paid_pilot_goal.md` as primary.
- **Index files:** Added INDEX.md in goals, standards, runbooks, guardrails, reports.
- **PROJECT_DOC_SYSTEM_MAP:** New top-level map at `docs/PROJECT_DOC_SYSTEM_MAP.md`.
- **README:** Added Broker Demo section with link to doc map and quick start.
- **PRE_DEMO_FLOW.md:** Fixed stale "3 questions" → "5 questions" to match current standard.

---

## 4. What still feels confusing

| Issue | Notes |
|-------|-------|
| **Multiple meeting/demo docs** | BROKER_MEETING_PACKAGE, BROKER_DEMO_OPERATOR_RUNBOOK, BROKER_DEMO_SCRIPT_15MIN, BROKER_DEMO_CHECKLIST all overlap. BROKER_VALUE_VALIDATION_MEETING_PACK is primary; others are lighter summaries. Map clarifies this. |
| **Reports in docs/** | Sprint reports live in docs/ (not reports/). reports/INDEX points to them. Moving would require many reference updates. |
| **INSURANCE_BROKER_DEMO_OPERATIONS_PACKAGE** | Historical report; still says "3 questions" in places. Left as-is (historical); not primary for daily use. |
| **PROMPT* / OPERATOR_STEP* docs** | Many operator/prompt docs in docs/; not broker-specific. Out of scope for this sprint. |

---

## 5. Recommended default reading order

1. **New to project:** `docs/goals/insurance_paid_pilot_goal.md`
2. **Running a demo:** `docs/ANDY_QUICK_START.md` → `docs/runbooks/BROKER_VALUE_VALIDATION_MEETING_PACK.md`
3. **Before broker meeting:** `docs/ANDY_2MIN_BEFORE_DEMO.md`
4. **Ports / recovery:** `docs/runbooks/RUNTIME_PATH_STANDARD.md`
5. **Quality bar:** `docs/standards/BROKER_DEMO_QUALITY_STANDARD.md`
6. **Drift check:** `docs/guardrails/BROKER_DEMO_DRIFT_GUARDRAIL.md`
7. **Something wrong:** `docs/ANDY_IF_SOMETHING_GOES_WRONG.md`

---

## 6. Next 10 actions

1. **Use the map:** Start from `docs/PROJECT_DOC_SYSTEM_MAP.md` when unsure where to look.
2. **Before demo:** Run `bash scripts/demo_pre_checklist.sh`; open `docs/ANDY_2MIN_BEFORE_DEMO.md`.
3. **Broker meeting:** Use `docs/runbooks/BROKER_VALUE_VALIDATION_MEETING_PACK.md` as single runbook.
4. **After changes:** Run `bash scripts/guardrail_broker_demo.sh` to catch drift.
5. **New sprint reports:** Add to `reports/INDEX.md` when creating broker-related reports.
6. **Cursor/OpenClaw:** Point agents to `docs/PROJECT_DOC_SYSTEM_MAP.md` for broker context.
7. **Optional:** Add `.cursor/rules` or AGENTS.md entry: "For broker demo: see docs/PROJECT_DOC_SYSTEM_MAP.md."
8. **Optional:** Archive or tag historical reports (e.g. INSURANCE_BROKER_DEMO_OPERATIONS_PACKAGE) as "historical" in reports/INDEX.
9. **Optional:** Consolidate BROKER_MEETING_PACKAGE into BROKER_VALUE_VALIDATION_MEETING_PACK in a future sprint (low priority; both point to same primary).
10. **Optional:** Move broker sprint reports from docs/ to reports/ in a future refactor (would require reference updates).

---

*End of report*
