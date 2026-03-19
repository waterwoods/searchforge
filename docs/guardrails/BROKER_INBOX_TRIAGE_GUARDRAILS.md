# Broker Inbox Triage — Guardrails

**Purpose:** Detect drift and weakness so future changes do not silently break triage quality.

---

## 1. Guardrail Scripts

| Script | Protects | Fail/Warn |
|--------|----------|-----------|
| `scripts/guardrail_inbox_triage.sh` | Scenario pack pass, output shape | Fail on regression |
| `scripts/run_inbox_triage_scenarios.py` | Per-scenario category, urgency, escalation | Fail on mismatch |

---

## 2. What Each Checks

### guardrail_inbox_triage.sh

1. **Scenario pack exists:** `configs/inbox_triage_scenarios.json` present
2. **Scenario runner runs:** `run_inbox_triage_scenarios.py` exits 0
3. **Output shape:** All results have 6 required fields

### run_inbox_triage_scenarios.py

- Runs each scenario in pack
- Compares `issue_category`, `urgency`, `manual_followup_needed` to expected
- Reports pass/fail per scenario and overall

---

## 3. When to Run

- **Before internal review:** Run guardrail + scenario pack
- **After changing triage logic:** Re-run scenario pack
- **After adding scenarios:** Update expected values; re-run

---

## 4. Weak Output Detection (Future)

- Missing `client_reply_draft`
- `client_reply_draft` contains unsafe phrases (e.g., "guarantee", "promise")
- Invalid `urgency` value
- Empty `broker_next_step`

---

*End of guardrails doc*
