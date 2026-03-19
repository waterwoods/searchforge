# Broker Inbox Triage — Runbook

**Purpose:** How to run, test, and validate the Broker Inbox Triage MVP.

---

## 1. Minimum End-to-End Workflow (v1)

```
[Input: pasted message text]
        ↓
  1. Classify issue type (issue_category)
        ↓
  2. Estimate urgency (low/medium/high/critical)
        ↓
  3. Determine manual follow-up needed (boolean)
        ↓
  4. Produce broker next step (actionable text)
        ↓
  5. Produce client prep (what client should gather/do)
        ↓
  6. Produce client-ready reply draft (editable by broker)
        ↓
[Output: structured triage result]
```

**Why this order:** Classification and urgency drive escalation; broker next step and client prep inform the draft. All six outputs are produced in one pass for v1.

---

## 2. Default Dev/Test Loop

```
1. Edit triage logic or prompts
2. Run scenario runner: python scripts/run_inbox_triage_scenarios.py
3. Inspect failures
4. Fix one thing
5. Re-run
6. Stop when scenario pack passes or next step needs Andy
```

---

## 3. Scenario Runner

| Command | Purpose |
|---------|---------|
| `python scripts/run_inbox_triage_scenarios.py` | Run full scenario pack; report pass/fail |
| `python scripts/run_inbox_triage_scenarios.py --verbose` | Show per-scenario output |
| `python scripts/run_inbox_triage_scenarios.py --single <id>` | Run one scenario by ID |

---

## 4. API Endpoint

**POST /api/inbox/triage**

| Item | Value |
|------|-------|
| Request | `{"text": "..."}` (message to triage) |
| Response | `issue_category`, `urgency`, `manual_followup_needed`, `broker_next_step`, `client_prep`, `client_reply_draft` |

```bash
# With server running (default port 8001):
curl -X POST http://localhost:8001/api/inbox/triage \
  -H "Content-Type: application/json" \
  -d '{"text": "Notice: Policy will be cancelled in 7 days due to non-payment."}'
```

**API test script** (requires server running):
```bash
python3 scripts/test_inbox_triage_api.py
python3 scripts/test_inbox_triage_api.py --url http://localhost:8001 --verbose
```

---

## 5. Manual Test (Single Message)

```bash
# CLI (no server needed):
python scripts/inbox_triage_cli.py "paste message here"

# API (server must be running):
curl -X POST http://localhost:8001/api/inbox/triage -H "Content-Type: application/json" -d '{"text":"..."}'
```

---

## 6. Guardrail

Before considering MVP "ready":

```bash
bash scripts/guardrail_inbox_triage.sh
```

---

## 7. What Cursor Can Do From Docs

- Implement triage logic from `BROKER_INBOX_TRIAGE_MASTER_GOAL.md` and `BROKER_INBOX_TRIAGE_STANDARD.md`
- Add scenarios from `BROKER_INBOX_TRIAGE_SCENARIOS.md`
- Run scenario runner and fix regressions

---

## 8. What OpenClaw Can Do

- Run scenario pack and report drift
- Flag weak outputs (missing section, unsafe wording)

---

*End of runbook*
