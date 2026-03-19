# Broker Demo Operator Runbook

Quick reference for running the 15-minute California Auto Insurance Broker Demo for 陈魁.

**→ For value-validation meeting:** Use `docs/runbooks/BROKER_VALUE_VALIDATION_MEETING_PACK.md` as the primary runbook (agenda, scripts, success criteria, next-step logic).

## Before the Demo

1. **Run pre-demo checklist** (one command; includes guardrail + validation):
   ```bash
   bash scripts/demo_pre_checklist.sh
   ```
   Runs guardrail first (question consistency, offline pack, copy-to-client), then env/offline/validation. Use `--strict` to fail on workflow-hint drift. Output: `results/demo_pre_checklist/<timestamp>/CHECKLIST.md`.

2. **Start the demo**:
   ```bash
   bash scripts/run_demo_local.sh
   ```
   Wait for "Demo ready" and note the Mode (Live or Offline).

3. **Open the demo URL**: http://localhost:5173/demo

4. **Check the status bar** at top of page:
   - **Live** (green) = Backend connected, use any question
   - **Offline** (orange) = Use the 5 recommended questions

## During the Demo

- **If Live**: Ask any of the 5 recommended questions or type custom questions.
- **If Offline**: Click the 5 recommended questions (they load pre-saved answers).
- Do not type custom questions in Offline mode — they will fail.
- Use "复制给客户" to show the WeChat-ready copy feature.

## If Live Fails Mid-Demo

1. Do not panic. Say: "Let me switch to our offline demo mode."
2. Refresh the page (F5).
3. Wait for the orange "离线演示模式" banner to appear.
4. Click the 5 recommended questions in order.
5. Continue the script as normal.

## After the Demo

1. Ask for feedback: "What would make this most useful for your day-to-day work?"
2. Note any questions you couldn't answer.
3. Send follow-up message (see `docs/BROKER_FOLLOWUP_MESSAGE.md`).

## Runtime Path

| Path | Port | Use |
|------|------|-----|
| **Default (broker demo)** | **8001** | `run_demo_local.sh`, validation scripts |
| Docker / alternate | 8000 | `docker compose up rag-api` |
| **Recovery** | 8001 | `bash scripts/restore_8001_readiness.sh` when embedding_warming |

See `docs/runbooks/RUNTIME_PATH_STANDARD.md`.

## Key Paths

| Item | Path |
|------|------|
| **Pre-demo checklist (default)** | `scripts/demo_pre_checklist.sh` — guardrail + validation + checklist (use `--strict` to fail on drift) |
| Quick prep (backend up) | `scripts/demo_prep_one_command.sh` — 30 sec, no checklist file |
| Guardrail only | `scripts/guardrail_broker_demo.sh` — standalone drift check |
| Demo launcher | `scripts/run_demo_local.sh` |
| Quick validate (live, Q1–Q5) | `scripts/demo_quick_validate.sh` |
| Snapshot offline pack | `python3 scripts/snapshot_demo_answers.py` |

**Offline pack refresh:** `demo_quick_validate.sh` automatically runs the snapshot on PASS, so `demo_fallback.json` stays aligned with validated Q1–Q5. One command = validate + refresh offline.

| Demo script | `docs/BROKER_DEMO_SCRIPT_15MIN.md` |
| Fallback script | `docs/BROKER_DEMO_FALLBACK_SCRIPT.md` |
| Meeting pack | `docs/runbooks/BROKER_VALUE_VALIDATION_MEETING_PACK.md` |
