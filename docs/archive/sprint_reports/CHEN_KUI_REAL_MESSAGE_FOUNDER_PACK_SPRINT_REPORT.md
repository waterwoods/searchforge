# Chen Kui Real Message Founder-Pack Sprint Report

**Sprint name:** Chen Kui Real Message Founder-Pack Sprint  
**Date:** 2026-03-09

---

## 1. Tasks completed

| Task | Status | Notes |
|------|--------|-------|
| **Task 1** — Build realistic Chen Kui founder case pack | Completed | Expanded from 5 to 10 cases |
| **Task 2** — Improve case focus labeling | Completed | Add car, remove car, premium review, DMV/SR-22 show specific labels |
| **Task 3** — Strengthen founder demo walkthrough | Completed | Updated docs with exact step order |
| **Task 4** — Optional polish | Completed | Added Payment failed to QUICK_FILL; R15, R16 to scenario pack |

**Skipped:** None.

---

## 2. Founder case pack changes

| Metric | Before | After |
|--------|--------|-------|
| Founder demo cases | 5 | 10 |
| Scenario pack scenarios | 26 | 28 |

**New cases:** Payment failed / lapse risk, Remove car, English notice + Chinese confusion, Declaration page missing, Chinese cancellation summary.

**Categories covered:** cancellation risk, missing document, add car, premium review, DMV/SR-22, payment failed, remove car, English+Chinese confusion, declaration page, Chinese cancellation.

---

## 3. Product changes made

### Task 1
- `scripts/prepare_unified_intake_founder_demo.py` — Added 5 new DemoSeed entries
- `ui/src/pages/UnifiedIntakePage.tsx` — Added same 5 to FOUNDER_DEMO_QUEUE
- `configs/inbox_triage_scenarios.json` — Added R15 (remove car), R16 (declaration page missing)

### Task 2
- `ui/src/pages/UnifiedIntakePage.tsx` — CATEGORY_DISPLAY_LABELS, inferCaseFocusFromText(), humanizeCategory(cat, sourceText?)

### Task 3
- `docs/CHEN_KUI_FOUNDER_DEMO_SCRIPT.md` — Exact step order
- `docs/UNIFIED_INTAKE_DEMO_READINESS.md` — Strongest Father-Demo Order
- `docs/runbooks/UNIFIED_INTAKE_MVP_RUNBOOK.md` — Best Demo Path
- `docs/UNIFIED_INTAKE_MVP_SCENARIOS.md` — Founder-demo route, R15/R16

### Task 4
- `ui/src/pages/UnifiedIntakePage.tsx` — Payment failed in QUICK_FILL_EXAMPLES
- `docs/UNIFIED_INTAKE_MVP_SCENARIOS.md` — Category coverage

---

## 4. Before vs after

| Aspect | Before | After |
|--------|--------|-------|
| Queue size | 5 cases | 10 cases |
| Case labels | "Customer Question" for add car, remove car, premium, DMV | "Add car quote", "Remove car", "Premium review", "DMV / SR-22 help" |
| Walkthrough | Vague | Exact: Load queue -> cancellation (opens first) -> reopen missing doc -> reopen add-car/premium |
| Example cases | 3 | 4 |

---

## 5. Validation summary

| Check | Result |
|-------|--------|
| npm run build | Pass |
| run_inbox_triage_scenarios.py | 28/28 passed |
| run_chen_kui_proxy_calibration.py | 12/12 passed |
| test_inbox_triage_api.py | All passed |
| guardrail_inbox_triage.sh | PASS |
| unified_intake_smoke_check.sh | PASS |
| prepare_unified_intake_founder_demo.py | 10 cases seeded |

---

## 6. Business value impact

- Queue looks like real office traffic
- Clearer case focus for broker
- Easier walkthrough for Andy
- Honest about mock vs real

---

## 7. Remaining blocker(s)

None.

---

## 8. Recommended next step

Run a live walkthrough with Chen Kui using the updated script. Gather feedback on whether the queue and labels feel like his office.

---

## 9. Chinese / mixed summary

**Main changes:** Expanded founder demo from 5 to 10 cases. Added payment failed, remove car, English notice + Chinese confusion, declaration page missing, Chinese cancellation. Improved labels so add car, remove car, premium review, DMV/SR-22 show specific labels instead of generic "Customer Question". Updated demo script with exact order: Load founder demo queue -> cancellation (opens first) -> reopen missing document -> reopen add-car or premium review.

**More like Chen Kui office:** Queue now includes payment failed, remove car, English+Chinese confusion, declaration page missing. Labels are more operational.

**Difficulties:** None. All validations passed.

**Best to show:** Load founder demo queue, then cancellation risk -> reopen missing document (follow-up continuity) -> reopen add-car or premium review (everyday value).

---

## 10. How to run frontend / backend

**Default:**
```bash
bash scripts/run_demo_local.sh
```
- Backend: http://localhost:8001
- Frontend: http://localhost:5173
- Unified Intake: http://localhost:5173/workbench/unified-intake

**Alternative (if 8001/5173 occupied):**
```bash
python3 -m uvicorn services.fiqa_api.app_main:app --host 0.0.0.0 --port 8002
VITE_API_PROXY_TARGET=http://127.0.0.1:8002 npm run dev -- --host 0.0.0.0 --port 5174
```
- Backend: http://localhost:8002, Frontend: http://localhost:5174

**Prepare founder demo queue:**
```bash
PYTHONPATH=. python3 scripts/prepare_unified_intake_founder_demo.py
```

---

## 11. Founder demo walkthrough simulation

1. **Open:** http://localhost:5173/workbench/unified-intake
2. **Click:** Load founder demo queue — 10 cases seeded; cancellation risk auto-opens
3. **See:** Current case shows CRITICAL, Cancellation risk, Broker action required, Your next move, Client draft
4. **Scroll to:** Recent broker cases — Work now and Waiting or parked sections
5. **Click:** Reopen case on Missing document follow-up — shows Waiting on client, Broker notes, follow-up continuity
6. **Click:** Reopen case on Add-car quote or Premium review — labels show "Add car quote" or "Premium review"
7. **Click:** Copy client draft — draft copied to clipboard
8. **Value:** Founder demo snapshot shows Needs attention now, Waiting on client, At-risk cases surfaced
