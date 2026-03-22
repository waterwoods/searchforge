# Fix-Now / Fix-Next / Defer Review Spec

**Sprint:** Pre-Trial Review Sprint  
**Created:** 2026-03-18

---

## 1. Decision Rules

| Decision | When | Example |
|----------|------|---------|
| **Fix now** | Trial-breaking; blocks real broker use | Talk to Agent routes wrong; next move always generic |
| **Fix next** | Important but not blocking; 1–2 sprints | Billing clarification route; correction badge visibility |
| **Defer** | Not worth doing before first trial | Inbox sync; OCR; carrier API; bundling |

**Rule:** If broker would say "I can't use this" → fix now. If "this could be better" → fix next. If feature request → defer.

---

## 2. Pre-Trial Fix-Now (Trial-Breaking)

| # | Item | Why fix now |
|---|------|-------------|
| — | *(None identified from current guardrail)* | Guardrail PASS; no known trial-blockers |

**Note:** If append API test fails in production (case_id for append), verify route deployed. Not a scenario logic issue.

---

## 3. Fix-Next (Important, Not Blocking)

| # | Item | Why fix next |
|---|------|--------------|
| 1 | Billing clarification | fix_next in scenario_logic_center; must NOT route to payment_lapse |
| 2 | Correction / already_sent visibility | Last-mile risk: broker may not see when customer said "already sent" |
| 3 | Handoff thresholds in triage.py | Hardcoded; extract to config if client variation needs it |

---

## 4. Defer

| # | Item | Why defer |
|---|------|-----------|
| 1 | Inbox sync, email/WeChat integration | Out of scope |
| 2 | OCR upload | Out of scope |
| 3 | Carrier API | Out of scope |
| 4 | Bundling scenario | Weak; low priority |
| 5 | Simulation coverage counts in UI | Nice-to-have |
| 6 | add-car-rules client-aware | Legacy cases; fallback works |

---

## 5. Post-Trial Flow

After first 3–5 real conversations:

1. Copy observation log to `results/trial_logs/{broker}_{date}.md`
2. Fill Friction Classification table
3. Use `docs/trial/FIX_NOW_QUEUE_SPEC.md`
4. Copy `docs/trial/FIX_NOW_QUEUE_TEMPLATE.md`; fill and save
5. Add fix-now items to next sprint backlog

---

*End of Fix-Now / Fix-Next / Defer Review Spec*
