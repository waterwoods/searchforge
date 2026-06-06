# P16-Z0 Capability Inventory

**Date:** 2026-06-01  
**Sprint:** P16-Z0 Capability Archaeology  
**Constraint:** Read-only inventory — no build, refactor, or P17  
**Method:** Search across `docs/`, `docs/product_constitution/`, `configs/`, `scripts/`, `ui/`, `services/fiqa_api/`

---

## How to read this table

| Column | Meaning |
|--------|---------|
| **Implemented?** | Code or rules exist in repo (may be local-only) |
| **Documented?** | Contract, runbook, or sprint artifact describes it |
| **Deployed?** | Works on Preview/trial URL (`product_only`) per P16-X/R evidence |
| **Hidden?** | Intentionally gated (`product_only`, env flag, lab route) |
| **Abandoned?** | Frozen, orphaned, or explicit non-goal |

**Backend path:** There is no `backend/` directory. Intake backend = `services/fiqa_api/inbox_triage/` + `routes/inbox_triage.py`.

---

## A. Constitution & governance (7 capabilities)

| Name | Status | Impl | Doc | Deploy | Hidden | Abandoned |
|------|--------|------|-----|--------|--------|-----------|
| Cap 1 — Broker Front Door | Partial | Yes | `contracts/CAPABILITY_01_*` | ~45 deploy / ~70 local | Customer tab hidden trial | — |
| Cap 2 — Urgent Message Triage | Strong | Yes | Cap 2 contract | ~85 | — | — |
| Cap 3 — Structured Case Record | Strong | Yes | Cap 3 contract | ~72 | Debug fields hidden | — |
| Cap 4 — Customer Intake Collection | Partial | Yes | Cap 4 + P16-O/N | ~55 deploy | Entire customer tab trial | — |
| Cap 5 — Case Lifecycle Management | Weak deploy | Yes | Cap 5 + P16-H/X | **53** (P16-X) | Work now/Waiting, timeline | — |
| Cap 6 — Trial Conversion | Weak | Docs | Cap 6 + P16-K | **51** (P16-X) | Observation log not in UI | Payment IDs empty |
| Cap 7 — Founder / Operator Control | Partial | Scripts | Cap 7 + P16-T/S | ~65 | Lab routes off trial | — |
| Constitution enforcement gate | Active | — | `CONSTITUTION_ENFORCEMENT.md` | N/A | — | — |
| Failure Pattern Library (FP-001+) | Active | Partial auto | `FAILURE_PATTERN_LIBRARY.md` | Runner checks | — | — |
| Reality validation checklist | Active | — | `REALITY_VALIDATION_CHECKLIST.md` | Manual | — | — |
| CAPABILITY_MAP_V1 | Active | — | `CAPABILITY_MAP_V1.md` | — | — | — |

---

## B. Triage engine & case store

| Name | Status | Impl | Doc | Deploy | Hidden | Abandoned |
|------|--------|------|-----|--------|--------|-----------|
| Greenfield triage (`triage_conversation`) | Production | Yes `triage.py` | Runbooks | Yes paste path | — | — |
| Multi-turn via `conversation_turns` | Production | Yes | API docs | Customer tab N/A trial | Hidden on trial URL | — |
| Append triage (`triage_for_append`) | Production | Yes | PILOT_CONTRACT | API yes; UX weak | Append box after reopen only | — |
| Case boundary (same vs new issue) | Production | Yes | `case_boundary_append_scenarios.json` | Backend | Collapsed UI tags | — |
| Case persist / reopen | Production | Yes `case_store.py` | — | Queue reopen | — | — |
| Session continuity (`session_store`) | Production | Yes | Archive sprint docs | Partial | Session ID invisible | — |
| Case activity timeline | Partial | Yes DB + API | P16-X audit | Collapsed / dev-only | `!productOnlyUi` | — |
| Case messages thread | Partial | Yes backend | — | Not rendered | `getRecentCustomerMessages` unused import | — |
| Follow-up patch (`waiting_on`, `next_contact_by`) | Production | Yes API | Scripts test | Editor hidden trial | `!productOnlyUi` | — |
| Case lifecycle derivation | Production | Yes `case_lifecycle.py` | P16-H | Mirrors UI | — | — |
| Demo queue seed (`FOUNDER_DEMO_QUEUE`) | Trial aid | Yes UI | Founder docs | Yes | — | — |
| State workflow backbone | Lab | Yes | Tests | — | — | — |

---

## C. Multi-turn & conversation (see Phase 2 doc)

| Name | Status | Impl | Doc | Deploy | Hidden | Abandoned |
|------|--------|------|-----|--------|--------|-----------|
| Append follow-up UI (broker) | Partial | Yes `BrokerWorkbenchTab` | P16-X | Undiscoverable | Until queue reopen | — |
| Append summary merge (prior bubbles) | **Not built** | No | P16-Y P0 gap | — | — | Deferred P16-Y |
| Customer mid-flow 提交补充 | Production | Yes | P16-N | Tab hidden trial | `product_only` | — |
| Interactive gap-fill dialogue | **Not built** | No | P16-X audit | — | — | By design (report not chat) |
| `INTENT_TIMELINE_QUESTION` | Partial | Yes rules | — | No visible timeline | — | — |

---

## D. Case intelligence (see Phase 4 doc)

| Name | Status | Impl | Doc | Deploy | Hidden | Abandoned |
|------|--------|------|-----|--------|--------|-----------|
| `collected_fields` / `still_needed_fields` | Production | Yes | P16-Y library | Glance one-shot | — | — |
| Missing info library (20 patterns) | Production | Yes rules | `P16Y_MISSING_INFO_LIBRARY.md` | Yes | — | — |
| Deadline hint extraction | Production | Yes `_extract_deadline_hint` | P16-Y | Indirect copy | — | — |
| `notice_image` gap detection | Production | Yes | P16-Y battery | Text-only trial | — | — |
| Case draft engine (v4 bundle) | Production | Yes | — | Fields only | Risk scores not shown | — |
| v4/v5 error & handoff risk scores | Production | Yes | — | Not in product UI | Simulation/debug | — |
| Assist layer (LLM overlay) | Optional | Yes `assist_layer.py` | — | Off default | `ENABLE_ASSIST_LAYER=1` | — |
| P16-Y 50-case battery | Guardrail | Yes script + config | P16-Y rubric | Local/CI | — | — |
| Truth field guardrails | Dev | Yes | — | — | `DEBUG_TRUTH_GUARDRAILS=1` | — |
| Learning signals JSONL | Backend-only | Yes | — | — | No HTTP | — |
| Audit export | Stub | Scaffold | — | — | — | "Do not use compliance" |

---

## E. Image & OCR (see Phase 5 doc)

| Name | Status | Impl | Doc | Deploy | Hidden | Abandoned |
|------|--------|------|-----|--------|--------|-----------|
| Google Vision OCR pipeline | Optional | Yes `image_input_pipeline.py` | — | Empty without key | — | — |
| Inline image on triage | API-ready | Yes `v6_attachment_sidecar` | — | **No product caller** | Simulation only | — |
| Attachment upload + OCR sidecar | Production | Yes routes | — | Broker workbench | — | — |
| OCR case fusion / v6 signals | Production | Yes | — | When blob present | — | — |
| PDF text extraction | Stub | `pdf_skipped` | P16-L freeze | Accepts file | — | Primary OCR path **frozen** |
| Weak-image clarification branch | Production | Yes `triage.py` | — | — | — | — |
| V6 A/B/C auto-input variants | Lab | Yes env | — | — | `V6_AUTO_INPUT_VARIANT` | — |

---

## F. Role simulation (see Phase 3 doc)

| Name | Status | Impl | Doc | Deploy | Hidden | Abandoned |
|------|--------|------|-----|--------|--------|-----------|
| Role C LLM customer line | Production | Yes API + service | P16-Q/X/Y sims | 503 without key | Simulation tab | — |
| Scenario replay tab | Dev | Yes `ScenarioReplayTab` | — | — | `!productOnlyUi` | — |
| SimulationAssistant component | **Orphan** | Yes file | Archive sprints | — | Zero imports | Effectively abandoned |
| Chen Kui proxy calibration | Test | Yes config | P16-G/L | — | — | — |
| Skeptical broker / Role D sim | Eval only | — | P16-Q/L docs | Failed cold URL | — | — |
| Add-car scenario batteries (many) | Lab | Yes scripts | Archive | — | Lab routes | — |

---

## G. Commercial & trial (see Phase 6 doc)

| Name | Status | Impl | Doc | Deploy | Hidden | Abandoned |
|------|--------|------|-----|--------|--------|-----------|
| Commercial Pack (P16-K) | Doc-complete | — | 10 artifacts | N/A | — | Payment not ready |
| Invoice templates $49/$99 | Template | — | `docs/trial/INVOICE_*` | — | — | IDs empty (FP-009) |
| Observation log v1/v2/v3 | Protocol | — | `docs/trial/TRIAL_OBSERVATION_*` | Not linked UI | — | Zero real rows logged |
| Chen Kui Day 0 script | Ready | — | `CHEN_KUI_DAY0_SCRIPT.md` | Blocked SSO | — | — |
| Day 7 payment checklist | Ready | — | `DAY7_PAYMENT_CHECKLIST.md` | — | — | — |
| trial_readiness_check.sh | Automated | Yes | AGENTS.md | Local CI | — | — |
| trial_launch_check.sh | Automated | Yes | — | — | — | — |
| founder_pre_trial_checklist.sh | Manual | Yes | — | — | — | — |
| deploy_paid_pilot.sh | Ops | Yes | — | — | — | — |
| Stripe / in-app billing | **None** | No | Out of scope | — | — | Constitution lock |

---

## H. UI surfaces & modes

| Name | Status | Impl | Doc | Deploy | Hidden | Abandoned |
|------|--------|------|-----|--------|--------|-----------|
| Broker workbench (`BrokerWorkbenchTab`) | Production | Yes | P16-M/I | Trial default | — | — |
| Customer entry tab | Production | Yes | P16-N/O | Hidden trial | `product_only` | — |
| My Requests tab | Production | Yes | P16-O | Hidden trial | — | — |
| Simulation tab | Dev | Yes | — | Hidden trial | — | — |
| Scenario Logic Center route | Lab | Yes `App.tsx` | — | Unmounted trial | — | — |
| Add Car Rules route | Lab | Yes | — | Unmounted trial | — | — |
| `UNIFIED_INTAKE_PRODUCT_ONLY` | Flag | Yes BE+FE | P16-I | Default trial | — | — |
| WeChat binding (stub/live) | Partial | Yes | — | Stub default | Customer tab off | Live needs env |

---

## I. Health, deploy & guardrails

| Name | Status | Impl | Doc | Deploy | Hidden | Abandoned |
|------|--------|------|-----|--------|--------|-----------|
| guardrail_inbox_triage.sh | Production | Yes | AGENTS.md | Local | — | — |
| P16-T health check runner | Production | Yes | P16-T docs | Preview checks | — | — |
| post_sprint_check.sh | Production | Yes | — | — | — | — |
| unified_intake_release_gate.sh | Production | Yes | — | — | — | — |
| P16-W `getCompactQueuePreview` crash fix | Fixed | Yes | P16-W | Redeploy needed | — | — |
| Preview SSO protection (FP-004) | **Blocker** | — | FP library | 401 cold URL | — | Founder toggle |
| RAG / auto-insurance corpus | Parallel product | Yes | Out of pilot wedge | Docker 8000 | Lab | Not intake |

---

## J. Evaluation-only sprints (docs, no code)

| Name | Status | Impl | Doc | Deploy | Hidden | Abandoned |
|------|--------|------|-----|--------|--------|-----------|
| P16-M TOP50 UI improvements | Evaluation | No code | `P16M_TOP50_UI_IMPROVEMENTS.md` | — | — | Backlog |
| P16-N customer journey map | Evaluation | No code | `P16N_CUSTOMER_JOURNEY_MAP.md` | — | — | Backlog |
| P16-X friction / conversation audits | Diagnosis | No code | P16-X pack | Evidence on Preview | — | — |
| P17 platform work | Blocked | — | Multiple verdicts | — | — | **Explicit freeze** |

---

## K. Scripts inventory (operator-relevant)

| Script | Capability served |
|--------|-------------------|
| `run_demo_local.sh` | Local demo (8001) |
| `guardrail_inbox_triage.sh` | Triage + multi-turn + append batteries |
| `run_p16y_case_battery.py` | Case intelligence regression |
| `run_multi_turn_simulations.py` | Customer multi-turn |
| `run_follow_up_append_simulations.py` | Broker append |
| `run_append_boundary_ab_scenarios.py` | Case boundary |
| `run_cross_client_ab_scenarios.py` | Cross-client append |
| `trial_readiness_check.sh` | Trial gate |
| `trial_launch_check.sh` | First broker trial |
| `health_check.sh` / `post_sprint_check.sh` | Ops posture |
| `run_role_c_add_car_battery.py` | Role C simulation |
| `deploy_paid_pilot.sh` | Paid pilot deploy |

Full script count: **197** `.sh` under `scripts/` (many lab/RAG; see `docs/runbooks/OPERATOR_IGNORE_LIST.md` for pilot scope).

---

## L. Configs inventory (intake-relevant)

| Config | Purpose |
|--------|---------|
| `p16y_50_cases.json` | Case intelligence battery |
| `customer_entry_multi_turn_simulations.json` | Customer multi-turn |
| `case_boundary_append_scenarios.json` | Append boundary A/B |
| `chen_kui_proxy_calibration_cases.json` | Broker proxy calibration |
| `inbox_triage_scenarios.json` | Core triage scenarios |
| `simulation_assistant_scenarios.json` | Simulation assistant (legacy) |
| `realistic_conversation_simulation_pack.json` | Conversation sim pack |
| `configs/clients/chen_kui/` | Client pack + ui_copy |

---

## Summary counts (approximate)

| Bucket | Count |
|--------|-------|
| Named capabilities in inventory | **80+** |
| Implemented in code | **~55** |
| Deployed on trial URL at full strength | **~15** |
| Hidden by `product_only` or flags | **~20** |
| Abandoned / frozen / stub | **~10** |
| Docs-only (evaluation sprint) | **~8** |

---

## Cross-reference

| Phase | Document |
|-------|----------|
| Multi-turn | `P16Z0_MULTITURN_ARCHAEOLOGY.md` |
| Role simulation | `P16Z0_ROLE_SIMULATION_ARCHAEOLOGY.md` |
| Case intelligence | `P16Z0_CASE_INTELLIGENCE_ARCHAEOLOGY.md` |
| Image | `P16Z0_IMAGE_ARCHAEOLOGY.md` |
| Commercial | `P16Z0_COMMERCIAL_ARCHAEOLOGY.md` |
| Duplication | `P16Z0_DUPLICATION_AUDIT.md` |
| Map v2 | `P16Z0_CAPABILITY_MAP_V2.md` |
| Top 20 | `P16Z0_TOP20_REDISCOVERIES.md` |
| Verdict | `P16Z0_FINAL_VERDICT.md` |

---

*End of P16-Z0 Capability Inventory*
