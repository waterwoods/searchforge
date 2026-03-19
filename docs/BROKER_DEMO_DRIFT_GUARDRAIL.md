# Broker Demo Drift Prevention Guardrail

**Purpose:** Detect drift early so future changes do not silently break broker value, offline fallback quality, or demo safety.

## Guardrail Scripts

| Script | Protects | Fail/Warn |
|--------|----------|-----------|
| `scripts/guardrail_broker_demo.sh` | Q1–Q5 question consistency, offline pack workflow hints, item count | Fail on critical drift |
| `scripts/demo_pre_checklist.sh --strict` | Workflow hints, offline pack | Fail when workflow < 5 |
| `scripts/demo_quick_validate.sh` | Live Q1–Q5 regression | Fail on any scenario regression |

## What Each Guardrail Checks

### guardrail_broker_demo.sh

1. **Question consistency:** `broker_regression_all5.py` QUESTIONS must match `snapshot_demo_answers.py` QUESTIONS (same 5 questions, same order).
2. **Offline pack exists:** `ui/src/assets/demo_fallback.json` has `items` with length ≥ 5.
3. **Offline workflow hints:** At least 5 items have both 客户可准备 and 经纪人可进一步询问 in `answer`.

Exits 1 on any failure. No backend required.

### demo_pre_checklist.sh --strict

- Same workflow-hint check as guardrail.
- When `--strict`: exits 1 if workflow hints < 5/5.
- Default (no --strict): reports status only, does not fail.

### demo_quick_validate.sh

- Requires running backend.
- Validates live API for Q1–Q5.
- On PASS: runs `snapshot_demo_answers.py` to refresh offline pack.

## Default Pre-Demo Path

```bash
# 1. Guardrail (no backend needed) – catches drift early
bash scripts/guardrail_broker_demo.sh

# 2. Pre-checklist (reports status; use --strict to fail on drift)
bash scripts/demo_pre_checklist.sh

# 3. If backend up: quick validate (refreshes offline on PASS)
bash scripts/demo_quick_validate.sh
```

**One-liner for "am I demo-ready?":**
```bash
bash scripts/guardrail_broker_demo.sh && bash scripts/demo_pre_checklist.sh
```

## When to Run

- **Before demo:** Run guardrail + pre-checklist. If backend up, run quick validate.
- **After changing query.py / broker fixes:** Run quick validate; guardrail will pass if snapshot ran on PASS.
- **After adding new workflow hints:** Run quick validate; snapshot refreshes offline pack.
- **CI / Cursor / OpenClaw:** Run `guardrail_broker_demo.sh` to catch question drift and offline pack drift without needing backend.

## Simulated Drift Examples

| Drift | Guardrail Catches? |
|-------|-------------------|
| Someone adds Q6 to broker_regression but not snapshot | Yes (question count/order mismatch) |
| Someone removes workflow hint from query.py, snapshot not re-run | Yes (offline pack has < 5 with hints) |
| demo_fallback.json deleted | Yes (items < 5) |
| New broker-only phrase added, not in BROKER_ONLY_MARKER | No (would need copy-to-client test) |
| Port 8000 vs 8001 confusion | No (operator/doc responsibility) |
