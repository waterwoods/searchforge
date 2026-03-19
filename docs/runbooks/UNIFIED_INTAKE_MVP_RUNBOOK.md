# Unified Intake MVP — Runbook

**Purpose:** How to run, test, and validate the Unified Intake MVP during development.

**Package context:** This runbook supports the **Broker Standard Package** (see `docs/STANDARD_SCENARIO_PACKAGE.md`). The package includes: Customer Entry + Broker Workbench + 7 core scenarios. The workbench is part of the package, not an add-on.

---

## 1. End-to-End Workflow (v1)

```
[Input: pasted message text]
        ↓
  1. Normalize input (strip, collapse whitespace)
        ↓
  2. Classify issue type (issue_category)
        ↓
  3. Estimate urgency (low/medium/high/critical)
        ↓
  4. Determine manual follow-up needed (boolean)
        ↓
  5. Produce broker next step (actionable text)
        ↓
  6. Produce client prep (what client should gather/do)
        ↓
  7. Produce client-ready reply draft (editable by broker)
        ↓
  8. Save lightweight case record locally
        ↓
  9. Reopen recent case / update simple status / save lightweight follow-up target + timing / add broker note
        ↓
[Output: structured triage result]
```

**Why this order:** Classification and urgency drive escalation; broker next step and client prep inform the draft. All six outputs are produced in one pass for v1.

---

## 2. Default Dev/Test Loop

```
1. Edit triage logic or prompts
2. Run scenario runner: PYTHONPATH=. python3 scripts/run_inbox_triage_scenarios.py
3. Inspect failures
4. Fix one thing
5. Re-run
6. Stop when scenario pack passes or next step needs Andy
```

---

## 3. Scenario Runner

| Command | Purpose |
|---------|---------|
| `PYTHONPATH=. python scripts/run_inbox_triage_scenarios.py` | Run full scenario pack; report pass/fail |
| `PYTHONPATH=. python scripts/run_inbox_triage_scenarios.py --verbose` | Show per-scenario output |
| `PYTHONPATH=. python scripts/run_inbox_triage_scenarios.py --single <id>` | Run one scenario by ID (e.g. S3) |

**Mature intake skeleton:** `docs/MATURE_INTAKE_SKELETON.md` — shared flow shape for all high-value scenarios.

**Broker handoff clarity:** `docs/BROKER_HANDOFF_CLARITY_GUIDE.md` — unified workflow language: Case focus → Your next move → Collected → Still needed → Full conversation. Add-car, renewal, claim, and missing-document cases show structured Collected/Still needed chips; other flows use conversation_summary.

**Queue triage:** §0a of the handoff guide defines queue-level signals: urgency, case focus, readiness (Ready to act / Needs more info / Verify receipt), work now vs waiting/parked. Recent cases list shows compact flow-specific previews and a queue legend.

**Where things live:** `docs/KNOWLEDGE_ARCHITECTURE_AND_CONFIG_LAYER.md` — rules vs knowledge vs state vs tests; `docs/RETRIEVAL_KNOWLEDGE_LAYER_FOUNDATION.md` — what goes into RAG vs rules/config; `docs/CURRENT_SYSTEM_FILE_CLASSIFICATION.md` — file-to-layer mapping; `docs/CONFIG_EXTRACTION_GUIDE.md` — config structure, what is extracted.

**Config layer / package model:** See `docs/CLIENT_PACK_FOUNDATION.md`. `configs/industries/insurance/markers.json` (intent markers), `configs/industries/insurance/reply_templates.json` (cancellation_warning, add_car, payment_lapse_expiration, missing_document, etc.), `configs/clients/chen_kui/handoff_phrases.json` (handoff wording), `configs/clients/chen_kui/reply_overrides.json` (optional reply overrides).

**Scenario pack location:** `configs/inbox_triage_scenarios.json`
**Proxy calibration pack:** `configs/chen_kui_proxy_calibration_cases.json`
**Multi-turn simulation pack:** `configs/customer_entry_multi_turn_simulations.json`
**Expression robustness pack:** `configs/expression_robustness_cases.json` — run: `PYTHONPATH=. python3 scripts/run_expression_robustness.py`

**Complex adversarial pack** (mixed-intent + long-context): `configs/mixed_intent_scenarios.json`, `configs/long_context_memory_shift_simulations.json` — run: `PYTHONPATH=. python3 scripts/run_complex_adversarial_simulation.py`

Multi-turn intake simulations (2–3 turn customer conversations):

```bash
PYTHONPATH=. python3 scripts/run_multi_turn_simulations.py
PYTHONPATH=. python3 scripts/run_multi_turn_simulations.py --verbose --single MT1
```

**Add-car / new quote flow (demo key):**
- First turn: If customer gives year+model+zip (or delivery/driver), hand off immediately.
- Partial first turn: Ask for year, model, VIN (optional), zip, delivery, driver.
- Turn 2: If only year+model given, ask for zip (or delivery/driver).
- Turn 3: Zip provided → hand off.
- Broker sees: "New quote / new vehicle" or "Add car to existing policy" + Collected fields + Still needed (when safe).
- Scenarios: MT1, MT2, MT13, MT15, MT16 in `customer_entry_multi_turn_simulations.json`.

Multilingual realism guardrails can also be stored in the scenario pack when helpful:

- `expected_draft_language`: `zh` or `en`
- `expected_draft_contains_any`: short phrases that should appear in the client-facing draft

Proxy-style calibration check:

```bash
PYTHONPATH=. python3 scripts/run_chen_kui_proxy_calibration.py
```

Use this when tightening client-facing drafts and broker next-step tone against the Chen-Kui-style proxy pack.

---

## 4. API Endpoint

**POST /api/inbox/triage**

| Item | Value |
|------|-------|
| Request | `{"text": "...", "persist_case": true|false}` |
| Response | Six required triage fields; when `persist_case=true`, also returns `case_id`, `case_status`, `created_at`, `updated_at`, `source_text`, `waiting_on`, `next_contact_by`, `case_notes`, `case_activity` |

```bash
# With server running (default port 8001):
curl -X POST http://localhost:8001/api/inbox/triage \
  -H "Content-Type: application/json" \
  -d '{"text": "Notice: Policy will be cancelled in 7 days due to non-payment.", "persist_case": true}'
```

**API test script** (requires server running):
```bash
python3 scripts/test_inbox_triage_api.py
python3 scripts/test_inbox_triage_api.py --url http://localhost:8001 --verbose
```

**Recent cases / status:**

| Endpoint | Purpose |
|----------|---------|
| `GET /api/inbox/cases?limit=8` | List recent saved cases |
| `PATCH /api/inbox/cases/{case_id}/status` | Update `new`, `reviewing`, `waiting_client`, or `done` |
| `PATCH /api/inbox/cases/{case_id}/follow-up` | Update `waiting_on` + `next_contact_by` on a saved case |
| `POST /api/inbox/cases/{case_id}/notes` | Append one short broker follow-up note |
| `POST /api/inbox/cases/{case_id}/append-message` | Paste new customer follow-up; re-triage in context and update case |

---

## 5. UI Entry Point (Unified Intake MVP v1)

| Item | Value |
|------|-------|
| Route | `/workbench/unified-intake` |
| Nav | AI Workbench → Unified Intake |
| Tabs | **客户入口 (Customer Entry)** — default. Same-page conversational intake. **Broker Workbench** — internal triage and case management. |
| Customer flow | Enter message → System replies inline → Can continue to add info → System asks next missing field if partial (e.g. add-car: zip) → Hand off when enough or after 2–3 turns → Case saved to broker workbench → "查看工作台" to switch |
| Broker flow | Paste raw inbound text → Triage + save → Review broker next move, client prep, and draft → Reopen recent case / update status / save follow-up target + timing / add broker note |

**How to run:**
1. Start demo: `bash scripts/run_demo_local.sh`
2. Open UI: http://localhost:5173/workbench/unified-intake
3. Optional for a clean founder-demo queue: `PYTHONPATH=. python3 scripts/prepare_unified_intake_founder_demo.py`
4. Paste the raw inbound text as-is; do not pre-clean it for the demo
5. Click **Start case**, then review the structured workbench result
6. Confirm the top of the page is short, clear, and action-first: one dominant entry area, one honest local-memory note, and optional examples hidden behind **Need an example?**
7. Optional for live demos: click **Load founder demo queue** to seed a repeatable demo-safe local queue and business snapshot
8. Confirm the active case puts one broker-owned next move first, with client prep and draft-to-send clearly secondary
9. Confirm the case appears in Recent cases
10. Reopen it, update a lightweight status, set `waiting_on` / `next_contact_by`, and optionally add one broker follow-up note

Optional examples behind **Need an example?** focus on: cancellation warning, missing document, mixed shorthand chase.

---

## 5b. Visual Simulation Assistant (QA + Demo Prep)

**Purpose:** Quickly run scripted multi-turn scenarios to see how the system responds. Helps founders, testers, and Chen Kui spot flow problems and demo value.

**How to use:**
1. On Customer Entry tab, click **Simulation Assistant**
2. Select a scenario (Notice/cancellation, Missing document, Add car, Claim, Renewal, etc.)
3. Click **Run simulation** — turns are injected one by one; system replies come from the real triage API
4. Use **Next turn** for step-by-step mode, or **Auto-play** for timed replay
5. Review the **Evaluation** tag: Normal | Needs review | Off-flow / suspicious
6. Use **Reset** then **Replay** to run again

**Scenarios:** 15 prebuilt in `configs/simulation_assistant_scenarios.json` and `ui/src/components/simulation/SimulationAssistant.tsx`. Grouped: **Recommended trial (3–4 turn)** — Cancellation risk, Missing document, Add-car quote (Chinese), Premium review, Claim intake (all 3-turn deep); **Strongest multi-turn proof** — Add-car 3-turn (SIM15); **Edge cases** — AutoPay failed, missing DL, notice correction, vague "already sent", add-car partial, claim hit-and-run, renewal indirect, notice minimal (tricky).

**Evaluation tags (heuristic):**
- **Normal:** Handoff at expected turn, no generic fallback, reply on-flow
- **Needs review:** Handoff slightly late, robotic phrasing, or simulation incomplete; notes may include "Issue likely at turn N"
- **Off-flow / suspicious:** Generic "please provide more context", wrong category, or no handoff after expected turns

**CLI script:** `PYTHONPATH=. python3 scripts/run_simulation_assistant_scenarios.py` — runs all 15 scenarios for bug harvest; guardrail step 8.

**Demo honesty:** Labels are heuristic, not perfect truth. Human judgment still required for final quality assessment.

---

## 5a. Compact Founder Demo Prep (one command)

```bash
bash scripts/run_demo_local.sh
# Wait for backend + frontend ready, then:
PYTHONPATH=. python3 scripts/prepare_unified_intake_founder_demo.py
# Open http://localhost:5173/workbench/unified-intake
# Click "Load founder demo queue"
```

**Online trial (no local setup):** Open https://ui-smoky-beta.vercel.app/workbench/unified-intake — click **Simulation Assistant** to run trial scenarios (Notice/Cancellation, Missing document, Add car, etc.). Backend: Cloud Run.

---

## 6. Best Demo Path

Use this exact order:

1. **Load founder demo queue** — seeds 13 demo-safe cases (including claim intake, messy-user, mixed-intent); cancellation-risk case auto-opens.
2. **Cancellation risk (opens first)** — shows urgency, same-day action, manual follow-up
3. **Reopen missing document** from Recent cases — shows operational follow-up, waiting-client state, and saved continuity
4. **Reopen add-car quote or premium review** — shows everyday broker work that can save time and reduce repeated explanation

**Chen Kui trial pack:** See `docs/CHEN_KUI_TRIAL_PACK.md` for trial purpose, scenarios, order, value validation questions, and pilot offer.

What to say while showing it:

- "This is the one unified intake surface for the kinds of messages a broker already receives."
- "I can drop the raw message here without cleaning it up first."
- "I paste the message once, and the system turns it into a structured case card."
- "The broker immediately sees urgency, next step, what the client should prepare, and a draft response."
- "The case does not disappear after triage; recent work stays visible with a lightweight status plus who we're waiting on and when to check again."
- "The top snapshot is a local workbench summary, not a production analytics dashboard."
- "The broker stays in control; nothing is auto-sent."

---

## 7. Real vs Mocked (Demo-Honest Framing)

| Area | Status | Notes |
|------|--------|-------|
| Text triage | **Real** | `POST /api/inbox/triage` returns structured output |
| Structured case card | **Real** | Rendered in the UI |
| Lightweight case persistence | **Real** | Cases save locally and appear in Recent cases |
| Simple case status | **Real** | `new`, `reviewing`, `waiting_client`, `done` |
| Follow-up target + timing | **Real** | Local-only `waiting_on` + `next_contact_by` on saved cases |
| Broker note + activity trail | **Real** | Local-only notes and auto-logged activity on saved cases |
| Copy draft action | **Real** | Clipboard copy in browser |
| Founder demo snapshot | **Real** | Counts come from the current local saved-case queue |
| Founder demo starter queue | **Demo-assisted** | Demo-safe seed messages run through the real local triage + saved-case flow |
| Example cases / quick-fill | **Demo-assisted** | Seeded examples for repeatable walkthrough, hidden behind **Need an example?** |
| Inbox feed / OCR upload / CRM collaboration | **Not built** | Do not imply these exist in v1 |

---

## 8. Manual Test (Single Message)

```bash
# CLI (no server needed):
PYTHONPATH=. python3 scripts/inbox_triage_cli.py "paste message here"

# API (server must be running):
curl -X POST http://localhost:8001/api/inbox/triage -H "Content-Type: application/json" -d '{"text":"..."}'
```

---

## 9. Guardrail

Before considering MVP "ready":

```bash
bash scripts/guardrail_inbox_triage.sh
```

---

## 10. Knowledge Ingestion + Retrieval Validation

When adding or updating knowledge slices (DMV/SR-22, notice_interpretation, declaration_page_garaging):

```bash
USE_LOCAL_QDRANT=1 PYTHONPATH=. python3 scripts/ingest_insurance_knowledge.py
USE_LOCAL_QDRANT=1 PYTHONPATH=. python3 scripts/test_knowledge_retrieval.py
```

**Retrieval-assisted flows (2 paths):**
1. **Notice confusion** — `english_notice_confusion` → `retrieve_notice_explanation` (notice_interpretation, dmv_sr22)
2. **Document confusion** — declaration page / garaging proof questions → `retrieve_document_explanation` (declaration_page_garaging)

Safe fallback to template-only when retrieval fails. Runtime check: `scripts/verify_retrieval_health.py`; product proof: `scripts/run_retrieval_product_proof.py`; 3-agent simulation: `scripts/run_retrieval_3agent_simulation.py`. See RETRIEVAL_KNOWLEDGE_LAYER_FOUNDATION §8.

---

## 11. Demo-Simulation Checklist

Recommended cases before showing the demo:

1. Cancellation warning
2. Missing document
3. Payment / lapse concern
4. Vague customer question
5. Fragmented mixed-language input
6. Mixed shorthand document chase (`UW follow up - need dec page + garaging proof. 客户说上周发过了`)
7. Broken AutoPay wording (`AutoPay failed again, please update card to avoid interruption in coverage`)
8. Mixed overdue / policy-stop question (`客户问 这个是不是保单要停了? 他说昨天收到账单 overdue`)
9. DMV / SR-22 help wording (`Need SR-22 filing proof for DMV suspension clearance, what should client bring?`)
10. English notice with Chinese client question (`客户问：这个英文 notice 说 payment failed，我现在怎么办？`)
11. English carrier notice with Chinese summary (`Carrier notice: Your policy will be cancelled due to non-payment. 客户说这个是不是今天一定要处理？`)
12. Founder demo starter queue (cancellation risk, missing-document follow-up, add-car quote, premium review, DMV / SR-22 help)

Expected visible signals:

- One obvious intake area
- One case card with urgency + category
- Clear broker next step
- Clear client draft
- Broker next step sounds operational, not generic
- Client draft stays short and broker-editable, not formal/template-heavy
- Client draft matches the likely client language on clear Chinese and mixed-language cases
- Clear manual follow-up signal
- Recent cases read like a lightweight queue rather than a detailed log

---

## 11. What Cursor Can Do From Docs

- Implement triage logic from `UNIFIED_INTAKE_MVP_MASTER_GOAL.md` and `UNIFIED_INTAKE_MVP_STANDARD.md`
- Add scenarios to `configs/inbox_triage_scenarios.json`; update `UNIFIED_INTAKE_MVP_SCENARIOS.md`
- Run scenario runner and fix regressions

---

## 13. What OpenClaw Can Do

- Run scenario pack and report drift
- Flag weak outputs (missing section, unsafe wording)

---

## 13. Deferred Case-Management Features (Do Not Implement Now)

The MVP now includes `case_id` and `case_status`, but these items remain deferred:

| Future field | Purpose | Where to add |
|--------------|---------|--------------|
| `customer_id` | Link to customer/contact | API response; Case card header |
| `assigned_owner` | Broker or team member | API response |
| Full `timeline` / CRM history | Rich past actions, notes, assignments | Separate case-management layer, not current MVP |
| `attachments` | Original files / OCR sources | Separate upload + storage flow |

**Implementation note:** Do not extend this into CRM behavior. Keep the current saved-case record local, lightweight, and single-broker friendly.

---

## 14a. Daily-Use End-to-End Simulation

Validates the full broker workday loop: queue → open → assess → reopen → append → see what changed → continue.

```bash
PYTHONPATH=. python3 scripts/run_daily_use_simulation.py
PYTHONPATH=. python3 scripts/run_daily_use_simulation.py --verbose
```

Seeds 8 mixed cases (add-car, renewal, claim, missing-doc, cancellation, premium, DMV) with notes and follow-up targets; appends customer follow-ups to 3 cases. Checks: queue surfaces action cases, reopen shows Resume here / last update, append refreshes triage. Used in smoke check step 21.

---

## 15. Smoke-Flow Checklist

```bash
bash scripts/unified_intake_smoke_check.sh
```

Runs guardrail (scenario pack + optional API test + persistence check, including follow-up target/timing plus note/activity trail), then prints manual UI verification steps. Step 21 runs the daily-use simulation.

**Full broker flow to validate:**
1. Paste message (or open **Need an example?** and use Cancellation, Missing document, or Mixed shorthand chase)
2. Click Triage
3. Review case card: urgency, Same-day action (if critical/high), Broker action required
4. Confirm the broker/client split is readable: broker-owned next move, client prep, draft to review and send
5. Confirm the case appears in Recent cases
6. Open the saved case from Recent cases
7. Change case status (`new` → `reviewing` or `waiting_client`) and confirm activity updates
8. Set `waiting_on` and `next_contact_by`; confirm the follow-up summary appears in the case card and Recent cases
9. Add one short broker note and confirm it appears after reopen
10. Read "Your next step" — is it actionable?
11. Click Copy draft — verify clipboard has client-facing text
12. Decide: manual follow-up needed? (critical/high = yes)
13. If using the founder demo queue, verify the top snapshot counts change in a believable way and stay clearly local/demo-safe

---

## 16. Deployment (Vercel + Cloud Run)

**Target:** Frontend on Vercel, backend on GCP Cloud Run. Lightweight shareable demo.

### Backend (Cloud Run)

1. Create `.env.cloudrun` from `configs/demo.env.example`
2. Set: `QDRANT_URL`, `QDRANT_API_KEY`, `QDRANT_COLLECTION=auto_insurance_demo_core`, `OPENAI_API_KEY`
3. For Vercel frontend: `ALLOWED_ORIGINS=https://your-project.vercel.app`
4. Deploy: `bash scripts/deploy_rag_demo.sh`

### Frontend (Vercel)

1. Connect repo to Vercel (ui/ as root or repo root with framework preset Vite)
2. Set env: `VITE_API_BASE_URL=https://your-cloud-run-url.run.app`
3. Build: `npm run build` (Vercel auto-detects Vite)
4. Deploy

### Post-deploy

- Open `https://your-app.vercel.app/workbench/unified-intake`
- Paste a cancellation warning message → verify triage works
- Check browser console for CORS errors; if any, add Vercel URL to `ALLOWED_ORIGINS` on Cloud Run

See `docs/DEPLOYMENT_READINESS.md` for full checklist.

---

*End of runbook*
