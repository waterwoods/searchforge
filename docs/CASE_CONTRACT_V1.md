# CASE_CONTRACT_V1

**SearchForge → Unified Intake → Add-Car Pilot — single source of truth**

This document is authoritative for product definition, backend behavior, API response shape, guardrails, and frontend interpretation. It **supersedes** conflicting prose in older docs; where those docs disagree with this file, **this file wins** until they are updated.

**Normative references (implementation must conform):**

- `docs/PILOT_CONTRACT_ADD_CAR_V1.md` — Add-Car truth, readiness, assist, guardrails (aligned with this contract).
- `configs/common/add_car_stage1_field_contract.json` — canonical field ids and labels.

---

## DISCOVERED_CORE_DOCS

| File path | Short description |
|-----------|-------------------|
| `docs/UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md` | Macro blueprint: identity/session/service record, formal submit, commercial anchors, dual-state semantics. |
| `docs/PROJECT_TRUTH_SWITCH.md` | Runtime map: routes, persistence flags (JSON vs Postgres), env matrix, structured-truth vs reply layer. |
| `docs/PILOT_CONTRACT_ADD_CAR_V1.md` | Add-Car pilot: truth rules, readiness, append semantics, assist rules, acceptance criteria. |
| `docs/CASE_CONTRACT_V1.md` | **This file** — consolidated Case contract across layers. |
| `configs/common/add_car_stage1_field_contract.json` | Canonical Add-Car field ids for API lists and UI. |
| `docs/guardrails/UNIFIED_INTAKE_MVP_GUARDRAILS.md` | Drift risks; scenario and persistence checks (partially superseded for Add-Car shape — see gaps). |
| `docs/runbooks/INDEX.md` | Runbook index. |
| `docs/runbooks/UNIFIED_INTAKE_MVP_RUNBOOK.md` | MVP operational runbook. |
| `docs/runbooks/BROKER_INBOX_TRIAGE_RUNBOOK.md` | Broker inbox triage operations. |
| `docs/runbooks/RELEASE_CHECKLIST.md` | Release discipline. |
| `docs/runbooks/RUNTIME_PATH_STANDARD.md` | Ports and runtime paths. |
| `docs/runbooks/DEPLOYMENT_PLAYBOOK.md` | Deployment steps. |
| `docs/runbooks/KNOWN_DEPLOYMENT_GOTCHAS.md` | Deploy pitfalls. |
| `docs/runbooks/UNIFIED_INTAKE_DB_OBSERVABILITY_SIGNALS.md` | DB observability for intake. |
| `docs/goals/UNIFIED_INTAKE_MVP_MASTER_GOAL.md` | MVP goal statement. |
| `docs/standards/UNIFIED_INTAKE_MVP_STANDARD.md` | MVP quality standard. |
| `docs/UNIFIED_INTAKE_MVP_BOUNDARIES.md` | MVP boundaries. |
| `docs/MATURE_INTAKE_SKELETON.md` | Shared intake flow skeleton (referenced from guardrails). |
| `docs/PRODUCT_AUDIT_UNIFIED_INTAKE_2026.md` | Product audit snapshot. |
| `docs/sprints/TRUTH_LAYER_REPLY_LAYER_INDUSTRIAL_STANDARD_SPRINT/02_TWO_LAYER_STANDARD_SPEC.md` | Truth vs reply non-overreach (cited from PROJECT_TRUTH_SWITCH). |
| `docs/sprints/TRUTH_INTENT_REPLY_THREE_LAYER_STANDARD_SPRINT/02_THREE_LAYER_STANDARD_SPEC.md` | Three-layer truth/intent/reply standard. |
| `services/fiqa_api/routes/inbox_triage.py` | HTTP API: `POST /api/inbox/triage`, case CRUD, append-message. |
| `services/fiqa_api/inbox_triage/triage.py` | Triage engine: truth extraction, readiness, boundaries, append. |
| `services/fiqa_api/inbox_triage/case_store.py` | Case persistence (JSON path), messages, activity. |
| `services/fiqa_api/inbox_triage/session_store.py` | In-progress session persistence (pre-formal-submit continuity). |
| `services/fiqa_api/inbox_triage/case_truth_repository.py` | Read path: Postgres-primary vs JSON fallback. |
| `services/fiqa_api/inbox_triage/add_car_field_contract.py` | Field validation + `quote_ready_matches_still_needed`. |
| `services/fiqa_api/inbox_triage/assist_layer.py` | Non-mutating assist payload (`ENABLE_ASSIST_LAYER`). |
| `scripts/guardrail_inbox_triage.sh` | Primary regression gate for inbox triage. |

---

## CURRENT_CONTRACT_SUMMARY

1. **Case / Service record**  
   **Service record** (persisted **Case**) is the durable Add-Car object the office uses: structured fields, lifecycle, message history, identifiers. It is **not** the raw chat for truth claims—chat is evidence; structured fields and gates are authoritative (`PROJECT_TRUTH_SWITCH` §6A–6B, master outline §2A).  
   **Case** in API/storage terms is that persisted record (JSON file and/or Postgres row per env flags).

2. **Structured truth fields**  
   Canonical ids: `configs/common/add_car_stage1_field_contract.json`. Pilot quote spine: `vin`, `zip`, `delivery_date`, `primary_driver`; vehicle description: `year`, `make_model`; contact: `name`, `phone`; auxiliary flags per contract (`PILOT_CONTRACT_ADD_CAR_V1` §2–3).

3. **Readiness signals**  
   - **`collection_stage`**: `collecting` \| `enough_for_handoff` — coarse UI position from routing/handoff candidate (not quote completeness alone).  
   - **`quote_ready_status`** (Add-Car): `need_more` \| `almost_ready` \| `quote_ready` — broker-facing **quote data completeness** (truth + persisted augmentation).  
   - **`handoff_ready`**: **Greenfield:** true only when quote structural bar, contact gate, and routing align per pilot rules. **Append:** `triage_mode=append` forces broker-visible semantics; **`handoff_ready=true` means “update is broker-visible,” not greenfield quote completion** (`PILOT_CONTRACT_ADD_CAR_V1` §4.3).  
   - **`triage_mode`**: `greenfield` \| `append` — disambiguates `handoff_ready`.  
   - **`lifecycle_status`**: process spine — e.g. `collecting`, `handoff_pending`, `handed_off`, `office_followup` (`PILOT_CONTRACT_ADD_CAR_V1` §4).

4. **Session vs case**  
   **Session** = temporary conversational container: messages, in-flight structured state **before** formal submit promotes to office-visible record (`master outline` §2A, `PROJECT_TRUTH_SWITCH` §6B). **Case** = durable service record after promotion rules fire.

5. **Boundary logic (new issue / new vehicle)**  
   Same thread may contain a **new matter**. Append triage classifies `case_boundary`: `same_case`, `new_issue`, `borderline` and `case_boundary_action`: `append_allowed`, `requires_new_case`, `requires_confirmation`. **Clear `new_issue` on append API must not mutate the existing case** (blocked response — see behavior/API sections).

6. **Persist vs append**  
   - **Persist new case:** `POST /api/inbox/triage` with `persist_case` and lane-specific rules (Add-Car: **`formal_submit` + structural completion or `handoff_ready`**).  
   - **Append to existing case:** `POST /api/inbox/cases/{case_id}/append-message` runs `triage_for_append`, sets `triage_mode=append`, and updates the record unless append is blocked for `new_issue`.

---

## CONTRACT_GAPS_AND_CONFLICTS

| Area | Conflict / gap | Resolution in CASE_CONTRACT_V1 |
|------|----------------|----------------------------------|
| **Storage primary** | Master outline §3.2 still says “JSON-first runtime truth unchanged” while `PROJECT_TRUTH_SWITCH` documents Postgres-primary reads/writes for pilot. | **Office-visible Case truth for production pilot: Postgres is primary** when `SERVICE_RECORD_DATABASE_URL` / `DATABASE_URL` is set and DB-primary flags are on; JSON case files are **legacy / transitional** (see MIGRATION_RULES). |
| **MVP guardrails doc** | States “6 required fields” for triage output; Add-Car pilot requires additional keys (`quote_ready_status`, `triage_mode`, lifecycle/collection, etc.). | **Add-Car triage responses MUST include the field set in API_CONTRACT**; update `UNIFIED_INTAKE_MVP_GUARDRAILS.md` in a follow-up PR. |
| **Soft-route starter** | `routes/inbox_triage.py` may seed `still_needed_fields` with `model` for generic add_car button path. | **Non-conformant id**; canonical id is **`make_model`**. Implementation should be fixed to match `add_car_stage1_field_contract.json` (do not treat `model` as stable API). |
| **`handoff_ready` on append** | Same boolean as greenfield but different meaning. | **Always pair interpretation with `triage_mode`** (`PILOT_CONTRACT_ADD_CAR_V1` §4.3). |
| **`collection_stage` vs contact gate** | `collection_stage` can be `enough_for_handoff` while contact gate forces `handoff_ready=false` (turn ≥ 4). | **Allowed:** `collection_stage` reflects routing width; **`handoff_ready` is the strict broker handoff signal** with contact tightening. |
| **Human-request shortcut** | `customer_requested_human` path can set `handoff_ready=true` without Add-Car quote completeness. | **Intentional lane exception**; not quote_ready gating. |
| **Append + `new_issue` (historical)** | Older notes suggested “append still persists for traceability” on new_issue. | **Authoritative behavior:** append endpoint **does not mutate** case when `case_boundary=new_issue`; returns blocked payload (`routes/inbox_triage.py`). |

---

## CANONICAL_CASE_MODEL

### 1. Case identity

| Field | Meaning |
|-------|---------|
| `case_id` | Stable server-issued id for the service record (present once persisted). |
| `client_id` | Client pack / tenant selector for config and copy. |
| `service_type` | High-level service classification from triage (Add-Car lane sets add-car types). |
| `service_lane` | Lane marker (formal Add-Car records: `add_car`). |
| `subject_key` | **Alias of `vehicle_key`** — normalized subject for “one case, one vehicle unit” in Add-Car. |

### 2. Truth snapshot

| Field | Meaning |
|-------|---------|
| `collected_fields` | List of canonical field ids accepted by the truth layer. |
| `still_needed_fields` | Canonical ids still missing or blocked. |
| `quote_ready_status` | `need_more` \| `almost_ready` \| `quote_ready` (Add-Car). |
| `handoff_ready` | Broker handoff / visibility signal; interpret with `triage_mode`. |
| `collection_stage` | `collecting` \| `enough_for_handoff`. |

### 3. Conversation

| Field | Meaning |
|-------|---------|
| `case_messages` | **Append-only** ordered messages (customer/system), with metadata (`message_id`, `created_at`, `sequence`). |
| `source_text` | Serialized thread (`[客户]` / `[系统]` lines) for extraction and migration. |

### 4. Lifecycle

| Field | Meaning |
|-------|---------|
| `case_status` | Operator queue label (`new`, `reviewing`, `waiting_client`, …) — **not** the intake process spine. |
| `lifecycle_status` | Intake/process spine (`collecting`, `handoff_pending`, `handed_off`, `office_followup`). |
| `formal_submitted_at` | Immutable first office-visible persist timestamp for the record. |
| `created_at` / `updated_at` | Record creation and last activity. |

### 5. Boundary signals (append / continuation)

| Field | Meaning |
|-------|---------|
| `triage_mode` | `greenfield` \| `append`. |
| `case_boundary` | `same_case` \| `new_issue` \| `borderline` (when classified). |
| `case_boundary_action` | `append_allowed` \| `requires_new_case` \| `requires_confirmation`. |

### 6. Optional / operational

| Field | Meaning |
|-------|---------|
| `case_notes`, `contact_note`, `case_activity` | Operator notes and coarse activity log. |
| `case_attachments` | Attachment metadata and files (pilot limits per `case_store`). |
| `workbench_test` / `extra.workbench_*` | Test and workbench flags (env-specific authority when DB-only). |
| `human_confirmation_fields` | Broker-visible “confirm with customer” flags. |

### What is **not** part of Case

- **Ephemeral session blob** (pre-submit in-progress state keyed by `session_id`) — not office-visible.  
- **LLM assist text** — suggestions only; never persisted as truth.  
- **Policy / rating engine outputs** — out of pilot scope.

### What **session** is

Temporary continuity: message turns + last triage result **until** formal submit creates or binds to a Case (`session_store.py`). May expose `conversation_id` echoing `session_id` on triage responses.

### What **Policy** is (brief)

Insurance **policy** objects (carrier policy numbers, billing, coverage) are **not** modeled as the Case spine in Stage 1. Case = intake/service record for the **matter** (e.g., add this vehicle), not full policy admin.

---

## FIELD_LEVEL_CONTRACT

Fields below are **Add-Car pilot / triage contract**. Operators: **truth layer + persistence merge** (`triage.py`, `add_car_field_contract.py`).

### `collected_fields`

- **Meaning:** Canonical field ids accepted under `should_accept_field` / guardrails.  
- **Allowed values:** Subset of `canonical_field_ids` + dynamic doc keys (`requested_*`, `customer_says_sent_*`) per JSON contract.  
- **Source of truth:** Structured extraction from **customer** utterances only; system bubbles do not backfill (`PILOT_CONTRACT_ADD_CAR_V1` §2.1).  
- **Update rules:** Merge on each triage; reconcile with persisted record on reopen/post-submit (`_reconcile_add_car_lists_with_persisted_record`).

### `still_needed_fields`

- **Meaning:** Canonical ids not yet satisfied in truth for this turn (after reconciliation).  
- **Allowed values:** Same id universe as collected.  
- **Source of truth:** Derived from structural + contact rules minus collected; post-submit may clear `name`/`phone` from chat-only gaps when record holds them.  
- **Update rules:** Must stay **consistent** with `quote_ready_status` (see invariant).

### `quote_ready_status`

- **Meaning:** Quote data completeness for brokers.  
- **Allowed values:** `need_more` \| `almost_ready` \| `quote_ready`.  
  - `need_more`: no truth-accepted VIN.  
  - `almost_ready`: VIN accepted; at least one of `zip`, `primary_driver`, `delivery_date` missing.  
  - `quote_ready`: all four truth-satisfied; **calendar** `delivery_date` (not relative-only).  
- **Source of truth:** `_add_car_quote_ready_status` + persisted structural augmentation.  
- **Invariant:** `quote_ready` MUST NOT contradict structural gaps in `still_needed_fields` (`quote_ready_matches_still_needed`).

### `handoff_ready`

- **Meaning:** Whether the broker should treat the response as handoff-worthy (**greenfield**) or broker-visible (**append**).  
- **Allowed values:** boolean.  
- **Source of truth:** Triage routing + Add-Car quote gate + contact gate (turn ≥ 4 pre-submit) + exceptions (`PILOT_CONTRACT_ADD_CAR_V1` §4.2).  
- **Update rules:** For `triage_mode=append`, forced true for visibility **except** blocked new-issue responses (no mutation).

### `triage_mode`

- **Meaning:** Distinguishes greenfield vs continuation append.  
- **Allowed values:** `greenfield` \| `append`.  
- **Source of truth:** `triage_conversation` vs `triage_for_append`.  
- **Update rules:** Append endpoint always sets `append`.

### `case_boundary`

- **Meaning:** Whether the latest customer message belongs to the same matter as the existing record.  
- **Allowed values:** `same_case` \| `new_issue` \| `borderline` \| unset (greenfield).  
- **Source of truth:** `_classify_append_case_boundary` on append.  
- **Update rules:** When `new_issue`, append persist is **blocked**; operator opens a **new** Case.

### `formal_submitted_at`

- **Meaning:** First office-visible persist time for this Case.  
- **Allowed values:** ISO-8601 string (server-generated).  
- **Source of truth:** Set on initial `save_case` / DB insert; **immutable**.  
- **Update rules:** Later updates change `updated_at` and message history, not this timestamp.

### `lifecycle_status` / `collection_stage`

- **lifecycle_status (typical):** `collecting`, `handoff_pending`, `handed_off`, `office_followup`.  
- **collection_stage:** `collecting`, `enough_for_handoff`.  
- **Rule:** Do not interchange with `quote_ready_status` or `case_status` (`master outline` §3.2).

---

## BEHAVIOR_CONTRACT

### Persistence

- **Always persist conversation** on Case: `case_messages` / `source_text` grow append-only for customer/system turns.  
- **Case MAY exist in draft/incomplete state** only in **session** pre-submit; **office-visible Case** requires formal submit rules for Add-Car.

### Readiness (strict definitions)

| State | Meaning |
|-------|---------|
| **Collecting** | Any pilot-required quote or contact slot missing, blocked, or contact gate failing. |
| **Almost ready** | VIN truth-complete; other quote slots incomplete. |
| **Quote ready** | `vin` + `zip` + `primary_driver` + `delivery_date` truth-complete (calendar date). |
| **Handoff ready (greenfield)** | `quote_ready_status == quote_ready` AND contact gate pass AND routing allows handoff — **unless** lane-specific exception (e.g. human request). |
| **Handoff ready (append)** | Broker-visible update; **does not** re-prove greenfield quote completion. |

### Append vs new case

- **Same vehicle / same matter** → append allowed (`case_boundary_action=append_allowed`).  
- **New vehicle or new issue** → **new Case**; append API **must not** silently merge (`requires_new_case` → blocked response).  
- **Borderline** → `requires_confirmation`; message may still append per product policy **only when** implementation explicitly allows; current blocked path applies to **clear `new_issue`** only.

### VIN deferral

Phrases like “VIN later” **must not** set `vin` in `collected_fields` or flip VIN truth true (`PILOT_CONTRACT_ADD_CAR_V1` §2.6).

### Relative date

Relative-only delivery language **does not** satisfy `delivery_date` for truth or `quote_ready` (`PILOT_CONTRACT_ADD_CAR_V1` §2.4–2.5).

---

## API_CONTRACT

### `POST /api/inbox/triage`

**Core triage (always present after successful 200):**

- `issue_category`, `urgency`, `manual_followup_needed`, `broker_next_step`, `client_prep`, `client_reply_draft`, `conversation_summary`, `handoff_ready`, `triage_mode` (`greenfield` for this route).

**Add-Car lane (when add-vehicle intent / soft route is Add-Car): MUST present**

- `collected_fields` (list, may be empty)  
- `still_needed_fields` (list)  
- `quote_ready_status` (`need_more` \| `almost_ready` \| `quote_ready`)  
- `collection_stage` (`collecting` \| `enough_for_handoff`)  
- `lifecycle_status`  
- `next_best_question` (string; empty when `handoff_ready`)  
- `service_type`, `vehicle_key` (subject key; nullable if unknown), `primary_vehicle_summary` (nullable), `additional_vehicle_mentioned` (nullable bool), `additional_vehicle_count_hint` (nullable)

**When `case_id` is present**

- Omitted on response **unless** `persist_case` successfully created a case **or** handler merges identity into a saved record.  
- If `case_id` is returned, it references the durable Case / service record id.

**Optional / flag-gated**

- `assist` — **always present** as an object; when `ENABLE_ASSIST_LAYER` is off or LLM unavailable, values are safe placeholders (`assist_layer.DEFAULT_ASSIST`).  
- `truth_guardrail_debug` — only when `DEBUG_TRUTH_GUARDRAILS` enabled.

**Null rule**

- Prefer **empty list** over null for `collected_fields` / `still_needed_fields`.  
- Use **null** only for explicitly optional scalars (`vehicle_key`, summaries) where no value exists.

**Frontend may rely on**

- For Add-Car: **`still_needed_fields` + `quote_ready_status`** as the progress truth.  
- **`handoff_ready` only with `triage_mode`** (greenfield vs append).  
- **`formal_submitted_at`** on Case reads as “office has a durable record” (not from chat claims).

### `POST /api/inbox/cases/{case_id}/append-message`

Response is the **updated Case** or a **blocked** payload:

- On success: includes **`triage_mode=append`** and full triage fields as today’s implementation.  
- On `new_issue`: `append_blocked_new_issue=true`, `old_case_mutated=false`, plus boundary fields — **no silent append**.

---

## UI_CONTRACT

### Case list

- **One Case = one subject (vehicle unit)** for Add-Car; if multiple vehicles are mentioned, UI must surface ambiguity (`additional_vehicle_mentioned`, broker_next_step suffix).  
- Show **progress** from `quote_ready_status` and **gaps** from `still_needed_fields`.  
- Show **status** via `lifecycle_status` + `case_status` (queue).

### Case detail

- **Conversation:** render `case_messages` or reconstruct from `source_text`.  
- **Progress panel:** truth snapshot from `collected_fields` / `still_needed_fields` / `quote_ready_status`.  
- **Missing field guidance:** drive copy and checklist **only** from canonical ids (labels from client pack / `labels_zh`).

### Progress UI

- **Dynamic checklist** derived from `still_needed_fields` — **no hard-coded static checklist** that can drift from API.  
- When `triage_mode=append`, do **not** show greenfield “submit” completion off `handoff_ready` alone.

---

## MIGRATION_RULES

1. **JSON cases (`unified_intake_cases.json`)** — **deprecated** as **system of record** for production pilot; acceptable for local/dev only or transitional dual-write.  
2. **Postgres (Stage 1 service record schema)** — **primary truth** for office-visible Cases when DB URL and DB-primary flags are enabled (`PROJECT_TRUTH_SWITCH` §0, §6C).  
3. **Session** — **temporary continuity only**; never authoritative for “office has the record.”  
4. **Safe rollout order**  
   - Enable dual-write + verify `scripts/check_add_car_service_record_consistency.py`.  
   - Turn on DB-primary reads; keep JSON read fallback until verified.  
   - Turn on DB-primary writes; disable JSON case writes (`UNIFIED_INTAKE_JSON_CASE_WRITES=0`) when ready.  
   - Disable JSON read fallback for strict pilot (`UNIFIED_INTAKE_JSON_READ_FALLBACK=0`).  
   - Migrate historical JSON cases only via controlled scripts; do not split truth between two masters in production.

---

## ALIGNMENT_CHECKLIST

| Layer | Check |
|-------|-------|
| **Backend / triage** | Add-Car truth rules match §2–3 `PILOT_CONTRACT_ADD_CAR_V1`; `quote_ready_matches_still_needed` never contradicted in prod logs; contact gate at turn ≥ 4; VIN deferral and relative date rules enforced. |
| **Backend / routes** | `POST /triage` returns API_CONTRACT field set; Add-Car persist requires `formal_submit`; append blocks `new_issue`; soft-route ids use **`make_model` not `model`**. |
| **Backend / persistence** | `formal_submitted_at` immutable; `case_messages` append-only; Postgres-primary flags behave per `PROJECT_TRUTH_SWITCH`. |
| **Guardrails** | `bash scripts/guardrail_inbox_triage.sh` passes; first-turn continuity and pre/post-submit reply regressions green; state/workflow backbone tests green. |
| **Tests** | Scenario + API tests cover handoff, append, boundary block, quote_ready vs still_needed, relative date, VIN deferral. |
| **Frontend** | Progress UI driven by `still_needed_fields`; interprets `handoff_ready` with `triage_mode`; does not claim office receipt without `formal_submitted_at` / server Case. |
| **Docs** | Master outline “JSON-first” line updated to reflect Postgres-primary pilot; MVP guardrails updated to Add-Car response shape. |

---

*Version: 1.0 — Unified Intake Add-Car Case contract. Amend via PR with synchronized code, tests, and dependent docs.*
