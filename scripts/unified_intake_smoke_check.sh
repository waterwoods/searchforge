#!/bin/bash
# Unified Intake — Smoke-flow checklist
# ======================================
# Run guardrail first, then prints manual UI verification steps.
# Usage: bash scripts/unified_intake_smoke_check.sh
#
# Prereq: bash scripts/run_demo_local.sh (backend + frontend running)
#
# Full broker flow: paste → triage → save case → reopen recent case → update status → save follow-up → add note

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_DIR"

echo "[1] Guardrail..."
if ! bash "$SCRIPT_DIR/guardrail_inbox_triage.sh" 2>/dev/null; then
  echo "  Fix guardrail first: bash scripts/guardrail_inbox_triage.sh"
  exit 1
fi

echo ""
echo "[2] Manual smoke check (UI) — Full broker flow"
echo "  Open: http://localhost:5173/workbench/unified-intake"
echo "  If Vite is running on a different local port (for example 5174), use the active URL shown in the frontend terminal."
echo ""
echo "  Flow: paste raw message → start case → review broker/client split → recent cases → status update → follow-up → note → copy draft"
echo ""
echo "  Steps:"
echo "  1. Paste any real message, or click 'Need an example?' and choose 'Cancellation warning'"
echo "  2. Click 'Start case'"
echo "  3. Verify: Case card shows urgency=critical, 'Same-day action' tag, Broker action required"
echo "  4. Verify: one dominant broker next move appears first, with client prep and draft reply clearly secondary"
echo "  5. Verify: case appears in Recent cases"
echo "  6. Click 'Reopen case' — verify saved case reloads"
echo "  7. Change case status to Reviewing or Waiting Client"
echo "  8. Save follow-up target + next contact timing — verify it appears in 'Where this case stands now' and Recent cases"
echo "  9. Add one short broker note — verify it appears in Broker notes under 'Keep this case moving'"
echo "  10. Verify: activity shows case created, status change, and follow-up update"
echo "  11. Verify: the current broker next move is visible and actionable"
echo "  12. Click Copy client draft — verify clipboard contains client-facing draft"
echo "  13. Decide: manual follow-up needed? (critical/high = yes)"
echo "  14. (Add-car) Verify: 'Collected' and 'Still needed' chips appear for add-car cases (e.g. 'Add car / premium' example)"
echo "  15. (4 flows) Verify: add-car, renewal, claim, missing-document all show consistent Collected/Still needed layout"
echo "  15b. (Case focus) Verify: 'Case focus: Add car quote' (or Premium review, etc.) appears at top of action card; queue cards show case focus tag first"
echo "  15c. (Human confirmation) Verify: 'Human confirmation recommended' badge appears for payment/cancellation risk, missing-doc customer_says_sent, or add-car VIN/driver cases"
echo "  15d. (Case handoff) Verify: 'Case handoff' card shows: Case focus, Status (Collecting/Ready for handoff), Your next move, Human confirmation (when needed), Collected, Still needed in one compact block"
echo "  16. (Queue triage) Load founder demo queue; verify Work now / Waiting or parked; verify Ready to act / Needs more info / Verify receipt badges"
echo "  17. (Follow-up continuity) Reopen a case with saved note; verify 'Resume here' card shows waiting on + latest note"
echo "  18. (Due-state) Verify Overdue / Due today / Due tomorrow tags; verify 'Last meaningful update' in Where this case stands"
echo "  19. (Paste follow-up) Reopen a case; paste new customer message in 'Paste new customer follow-up'; click 'Update with new customer message'; verify case refreshes with new next step and source_text"
echo "  20. (What changed) After append: verify 'Just updated with customer follow-up' badge; verify queue card shows 'Last update: Customer follow-up added: ...' for that case"
echo "  21. (Handoff readiness) Reopen add-car or multi-turn case; verify 'Recent customer messages' section shows last 2-3 customer messages above 'Your next move'"
echo "  22. (Correction badge) If case has follow_up_type=correction or already_sent: verify 'Customer corrected' or 'Client says already sent' badge appears"
echo "  23. (Handoff order) Verify 'Your next move' appears immediately after Case focus (before Recent customer messages) — trial execution visibility"
echo ""
echo "[3] Daily-use end-to-end simulation (optional)..."
if PYTHONPATH=. python3 scripts/run_daily_use_simulation.py 2>/dev/null; then
  echo "  OK (daily-use mixed queue + append flow)"
else
  echo "  WARN: run_daily_use_simulation.py failed or not run"
fi
echo ""
echo "  Optional: try 'Missing document' and 'Mixed shorthand chase'"
echo ""
