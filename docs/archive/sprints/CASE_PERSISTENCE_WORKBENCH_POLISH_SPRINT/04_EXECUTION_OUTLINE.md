# Execution Outline — Case Persistence Review + Workbench Polish

## Loop 1 — Audit (read-only)

1. Read `case_store.py`: save/update/append paths, fields, caps, attachment handling.
2. Read `session_store.py`: what is stored pre-handoff vs case.
3. Read `routes/inbox_triage.py`: when `persist_case` triggers save; append and patch endpoints.
4. Skim Workbench UI (`UnifiedIntakePage.tsx`) for **non-demo-queue** friction: internal English, follow-up clarity, trust labels.

**Output:** Current architecture spec + list of top polish items (demo queue excluded).

## Loop 2 — Improve

1. Author sprint docs (blueprint, current spec, future spec, outline, acceptance, founder notes).
2. Apply **1–2** small, high-value Workbench improvements **without** changing demo queue behavior or persistence logic.

## Loop 3 — Verify

1. `bash scripts/guardrail_inbox_triage.sh`
2. If UI touched: `cd ui && npm run build`
3. Final report: persistence judgment + recommendation + polish outcome + remaining weakness.

## Time budget

30–60 minutes: favor **accurate docs** and **one cohesive UX improvement** over scattered edits.
