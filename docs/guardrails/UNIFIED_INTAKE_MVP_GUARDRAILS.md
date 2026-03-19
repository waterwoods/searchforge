# Unified Intake MVP — Guardrails

**Purpose:** Detect drift and weakness so future changes do not silently break triage quality.

---

## 1. What Can Drift

| Risk | Description |
|------|-------------|
| **Output shape** | New fields added or removed without standard update |
| **Category set** | New categories added without doc + scenario update |
| **Urgency mapping** | Same input produces different urgency without rationale |
| **Escalation logic** | `manual_followup_needed` flips without scenario re-run |
| **Client draft safety** | Unsafe phrases creep into `client_reply_draft` |
| **Case persistence drift** | Saved case cannot be listed, reopened, or status-updated |
| **Follow-up context drift** | `waiting_on`, `next_contact_by`, broker note, or activity trail stops persisting after reopen |
| **Skeleton drift** | Scenarios stop following detect → ask → enough? → hand off; handoff thresholds or summary quality regress |

---

**Mature intake skeleton:** `docs/MATURE_INTAKE_SKELETON.md` — shared flow shape. Multi-turn simulation pack (`configs/customer_entry_multi_turn_simulations.json`) protects skeleton behavior across all 7 high-value scenarios.

---

## 2. Guardrail Scripts

| Script | Protects | Fail/Warn |
|--------|----------|-----------|
| `scripts/guardrail_inbox_triage.sh` | Scenario pack pass, output shape | **Fail** on regression |
| `scripts/run_inbox_triage_scenarios.py` | Per-scenario category, urgency, escalation | **Fail** on mismatch |
| `scripts/verify_inbox_case_persistence.py` | Save/list/status/follow-up/note/activity behavior for local case store | **Fail** on regression |

---

## 3. What Each Checks

### guardrail_inbox_triage.sh

1. **Scenario pack exists:** `configs/inbox_triage_scenarios.json` present
2. **Scenario runner runs:** `run_inbox_triage_scenarios.py` exits 0
3. **Output shape:** All results have 6 required fields

### run_inbox_triage_scenarios.py

- Runs each scenario in pack
- Compares `issue_category`, `urgency`, `manual_followup_needed` to expected
- Reports pass/fail per scenario and overall

### verify_inbox_case_persistence.py

1. Saves a case to an isolated local JSON store
2. Confirms the case appears in the recent-case list
3. Updates the case status and confirms activity is appended
4. Updates `waiting_on` and `next_contact_by`
5. Adds one lightweight broker note
6. Confirms follow-up fields, note, and activity trail are persisted after reload

---

## 4. When to Run

- **Before internal review:** Run guardrail + scenario pack
- **After changing triage logic:** Re-run scenario pack
- **After changing saved-case behavior:** Run persistence verification
- **After changing saved-case follow-up behavior:** Re-run persistence verification and one manual reopen flow
- **After changing broker note/activity behavior:** Re-run persistence verification and one manual reopen flow
- **After adding scenarios:** Update expected values; re-run

---

## 5. Demo-Readiness Guardrail

Before a live walkthrough, confirm all of the following:

1. `run_inbox_triage_scenarios.py` passes on the supported scenario pack
2. The UI shows one clear intake surface and one readable case card
3. A saved case appears in Recent cases and can be reopened
4. A simple case status update is visible (`new`, `reviewing`, `waiting_client`, `done`)
5. A reopened case shows the saved follow-up target/timing and at least one lightweight note or activity item
6. At least one critical case and one messy/fragmented case were manually simulated
7. The copy action works on the client-facing draft
8. Andy can state what is real vs demo-assisted in one sentence

If those five checks are not true, the feature is not demo-ready even if the endpoint still works.

---

## 6. What Should Fail Loudly

- Scenario pack regression (any scenario fails expected values)
- Output missing required field
- Invalid urgency value
- Persistence check fails save/list/status flow
- Follow-up target/timing save fails or disappears after reload
- Broker note save or activity append fails on saved case
- Guardrail script exits non-zero

---

## 7. What Should Warn Only

- `client_reply_draft` contains potentially unsafe phrases (future: add phrase check)
- Empty `broker_next_step` (could be valid for some edge cases)
- New category not in standard (warn, do not fail until doc updated)
- UI looks like a raw utility form instead of a broker work surface
- Demo examples are present but not clearly labeled
- Recent-case list looks empty because UI is pointed at the wrong local backend
- Activity trail becomes noisy or repetitive from repeated no-op status clicks

---

*End of guardrails doc*
