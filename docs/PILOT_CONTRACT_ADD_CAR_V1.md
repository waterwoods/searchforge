# Add-Car Pilot Contract v1

Authoritative product contract for the **Add-Car** lane (Unified Intake).  
Implementation must conform; tests and guardrails validate this document—not the reverse.

---

## 1. Scope

**In scope**

- Add-car quote intake: structured truth, broker readiness signals, customer-facing replies, optional Assist Layer suggestions, persistence to service record.
- Single case / same-thread continuation, including post–formal-submit follow-ups.

**Out of scope (pilot)**

- Binding, rating engine integration, multi-vehicle quote splitting logic, auth/multi-tenant, new product features beyond contract alignment.

---

## 2. Truth rules

### 2.1 What counts as truth

**Truth** is what may appear in durable structured outputs: `collected_fields`, `still_needed_fields`, persisted service-record fields, and the boolean slots that feed `quote_ready_status` / `handoff_ready` (after guardrails).

Truth is **customer-utterance grounded**. System bubbles do not backfill structured slots.

### 2.2 Canonical field ids (API / persistence)

Use ids from `configs/common/add_car_stage1_field_contract.json` (`canonical_field_ids`). Structural quote slots for Stage 1:

| Id | Meaning |
|----|--------|
| `vin` | 17-character VIN |
| `zip` | California garaging ZIP (5 digits, leading 9) |
| `delivery_date` | **Coverage start / pickup / effective date** — pilot uses one slot; broker-facing copy may say “提车/effective” but storage is `delivery_date` |
| `primary_driver` | Primary driver identity (non-ambiguous) |
| `year`, `make_model` | Vehicle description (only when explicit vehicle identity is present per truth rules) |
| `name`, `phone` | Contact for office follow-up |

**Naming:** All layers (API, Assist, tests) use **`zip`** and **`delivery_date`**. Legacy inputs to `should_accept_field` may still normalize `garaging_zip` / `effective_date` internally in guardrails only.

### 2.3 What may be stored in `collected_fields`

- Only canonical ids (or allowed dynamic patterns: `requested_*`, `customer_says_sent_*`).
- A field may be listed as collected only if the **Truth Layer** would accept it: explicit literals or allowed inference paths (see guardrails), not vague reuse, partial VIN, relative-only dates, or ambiguous driver language.

### 2.4 What must stay missing / null

- Slots without acceptable evidence remain out of `collected_fields` and stay in `still_needed_fields` (or are implied by downstream gates).
- **Relative-only** delivery language (“下周”, “tomorrow”) without an absolute calendar date does **not** satisfy `delivery_date` for truth.

### 2.5 Explicitly forbidden in truth

- Inferred VIN from “maybe” / incomplete / deferred VIN.
- ZIP from non–CA pattern or vague area.
- `delivery_date` from relative phrases alone.
- `primary_driver` when ambiguity markers apply and no disambiguating literal.
- `year` / `make_model` without explicit vehicle identity in the evaluated utterance(s).
- **Context-reuse** phrases (“same as my other car”, “you already have it”) **blocking** structural slots until explicit literals appear (per guardrail policy).

### 2.6 Ambiguity, deferral, context reuse

- **Deferral** (“VIN later”) → do not mark `vin` collected.
- **Context reuse** → reject structural fills until the customer supplies literals (current-turn precedence: latest bubble can unlock a slot if it contains an explicit accept).
- **Thread vs current turn:** explicit literals in an **earlier** customer bubble may still accept a field; **primary_driver** is evaluated per bubble so a reuse line does not erase a later identity line.

---

## 3. Required fields by stage

### 3.1 Categories

| Category | Fields | Role |
|----------|--------|------|
| **Structurally useful** | `year`, `make_model` | Vehicle description, continuity, operator clarity; **not** sufficient alone for broker handoff. |
| **Pilot-required (quote truth)** | `vin`, `zip`, `delivery_date`, `primary_driver` | Required for **structural handoff** and for `quote_ready`. |
| **Pilot-required (office contact)** | `name`, `phone` (in thread or on record) | Required so the office can reach the customer; gated for **handoff** under pilot rules (see §4). |
| **Optional / auxiliary** | insurance status flags, materials sent / pending, `customer_requested_human`, doc-request keys | Broker visibility and workflow; do not replace quote slots. |

### 3.2 By stage (pilot semantics)

| Stage | What must be true |
|-------|-------------------|
| **Collecting** | Any pilot-required quote or contact slot missing or blocked by guardrails. |
| **Enough for handoff (structural)** | All four: `vin`, `zip`, `delivery_date`, `primary_driver` accepted in truth **and** routing allows handoff phrasing. |
| **Contact-complete for handoff** | `name` and `phone` present **in thread** or already on service record / post–formal-submit exception (see §4). |
| **Post–formal-submit** | Identity gaps may be satisfied by the service record; chat-only gaps should not contradict persisted record. |

---

## 4. Readiness semantics

Terms are **non-overlapping responsibilities**:

| Signal | Definition |
|--------|------------|
| `collection_stage` | `collecting` ↔ `enough_for_handoff` — coarse UI/engine position (whether structural completion warrants handoff phrasing). |
| `quote_ready_status` | Broker-facing **quote data completeness** (truth + persisted augmentation): `need_more` \| `almost_ready` \| `quote_ready`. |
| `handoff_ready` | **Greenfield:** true only when `quote_ready_status` is `quote_ready`, contact gate passes, and routing allows handoff. **Append:** see `triage_mode`. |
| `triage_mode` | `greenfield` \| `append` — append responses set `handoff_ready=true` to mean “broker-visible update”, not greenfield quote completion. |
| `lifecycle_status` | Pipeline position: `collecting`, `handoff_pending`, `handed_off`, `office_followup`. Not interchangeable with `quote_ready_status`. |

### 4.1 `quote_ready_status` (add-car)

- **`need_more`:** no truth-accepted VIN yet, or pre-VIN state.
- **`almost_ready`:** VIN accepted; at least one of `zip`, `primary_driver`, `delivery_date` still missing in truth.
- **`quote_ready`:** VIN + `zip` + `primary_driver` + `delivery_date` all truth-satisfied (calendar date for delivery).

Invariant: `quote_ready` must not contradict `still_needed_fields` for structural ids (enforced by `quote_ready_matches_still_needed`).

### 4.2 `handoff_ready` vs contact gate

- **Default:** `handoff_ready` may be true when structural completion and phrase routing say handoff, **even if** name/phone are only urged in reply (early turns).
- **Tightening:** from **customer turn count ≥ 4**, if `name` or `phone` is still missing from thread and there is no post-submit record exception, **`handoff_ready` must be false** and lifecycle returns to `collecting` until contact is supplied.

### 4.3 Append API (`triage_for_append`)

- **Contract:** `triage_mode=append` and **`handoff_ready=true`** mean the append payload is broker-visible; they **do not** re-run greenfield quote/contact completion checks. Interpreting readiness **requires** checking `triage_mode`.

### 4.4 `office_ready` (conceptual)

- Not a separate API flag in v1. **Operational “office has the record”** = formal submit completed / `lifecycle_status` in `handed_off` \| `office_followup` and persisted service record. UI derives “formal submission complete” from triage history, not from `handoff_ready` alone.

---

## 5. Assist behavior rules

### 5.1 Allowed

- Read-only use of triage output: suggest next questions, rephrase, flag ambiguity, propose **non-binding** interpretations.
- Ask for **all** critical missing fields in one message when multiple gaps exist (pilot UX).
- Use same-case context **only** for phrasing; never as silent truth.

### 5.2 Forbidden

- Mutate `collected_fields`, `still_needed_fields`, readiness flags, or any persisted truth.
- Imply `quote_ready` or `handoff_ready` beyond what truth already established.
- Convert relative dates to concrete dates in suggestions as if they were facts.

### 5.3 Field naming in Assist payloads

- Assist may expose `effective_date` / `garaging_zip` to the model for readability; implementation **must map** to `delivery_date` / `zip` when interpreting truth. Drift between prompt labels and API ids is not allowed in new code—prefer documenting the mapping (this section) and testing it.

---

## 6. Guardrail / debug rules

When `DEBUG_TRUTH_GUARDRAILS` is enabled:

| Field | Meaning |
|-------|--------|
| `truth_guardrail_debug` | Per-field rows: `decision` (`accept` \| `reject`), `reason`, `input` snippet. |
| `truth_guardrail_accepted` | Filtered accepts only. |

**Precedence:** collapse keeps **accept** over **reject** for the same field when both appear (e.g. layered checks).  
**Decisive reason:** the third tuple value from `should_accept_field` documents the winning rule (`explicit_literal_current_turn`, `context_reuse_block`, etc.).

**Blocked** = reject decision; **accepted** = accept. **Decision** is the final per-field outcome after thread vs current-turn evaluation.

---

## 7. Runtime / release invariants

1. **API shape:** Same JSON keys for triage responses in local and deployed pilots (`collected_fields`, `still_needed_fields`, `quote_ready_status`, `handoff_ready`, `lifecycle_status`, `collection_stage`, optional `assist` attachment per route contract).
2. **Flags:** `ENABLE_ASSIST_LAYER`, `DEBUG_TRUTH_GUARDRAILS`, `ADD_CAR_CONTRACT_STRICT` must be **documented per environment**; staging and pilot prod should match **intended** pilot promises (e.g. assist on if UX promises it).
3. **Semantics:** Readiness definitions in §4 do not change per environment; only **presence of assist text** and **debug arrays** may vary with flags.
4. **Persistence:** Post-submit reconciliation must not regress `quote_ready_status` or office-visible slots without explicit correction handling.

---

## 8. Non-goals

- Perfect natural-language understanding of every partial utterance.
- Replacing broker judgment on bindable quotes.
- Unifying append and greenfield triage to identical `handoff_ready` behavior without an explicit API mode.

---

## 9. Acceptance criteria

1. **Truth:** No `collected_fields` entry for a slot that `should_accept_field` would reject.
2. **Readiness:** `quote_ready_status` always consistent with structural `still_needed_fields` per `quote_ready_matches_still_needed`.
3. **Contact gate:** Turn ≥ 4 without name/phone in thread ⇒ `handoff_ready=false` (pre-submit, no record exception).
4. **Assist:** Never persists model output into truth; suggestions align with missing-field list mapping (`delivery_date`/`zip`).
5. **Release:** Pilot environment matrix lists flag values; API contract matches between local and deployed smoke.

---

*Version: 1.0 — Add-Car pilot. Amend via PR with synchronized code + tests.*
