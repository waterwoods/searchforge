# ADR-005: Active Case Consolidation & Evidence Append Model

**Date:** 2026-06-29  
**Sprint:** P17 Phase 2 — Architecture Baseline Freeze  
**Status:** Accepted Architecture — **Implementation gated by pilot validation** (Future Vision §4)  
**Authority:** `docs/product_constitution/P16_CUSTOMER_FIRST_CONSTITUTION.md` Rule 7 · `docs/p16/P16_FUTURE_VISION.md` §7  
**Supersedes (partial):** ADR-001 §Rules #7 — see §10 (amendment applied in ADR-001, P17 Phase 2)  
**Does not supersede:** ADR-002 · ADR-003 · ADR-004 (extends Phase 2+ dependency)  
**Related planning:** P17 Active Case Planning (2026-06-28) — case consolidation first; no repo file; captured in sprint review

---

## Decision

**Promote existing `case_id` / `record_id` to Active Case semantics.**

One customer insurance job (same person, same intent, open case) maps to **one broker inbox row**. Multiple customer evidence events (uploads, messages, corrections) **append to the same Active Case** when merge rules pass. **Trusted Packet** is the materialized execution projection of merged evidence. **ADR-001 readiness applies to the Packet only**, not to individual evidence events.

**Phase 1 (build when gated):** Consolidation resolver + packet re-materialization + inbox dedup.  
**Phase 2 (same ADR, later build):** Formal immutable Submission records for audit and Business Loop hooks.

This ADR defines architecture only. It does **not** authorize implementation before the validation gate unless the founder explicitly approves a pilot fragmentation fix (§13).

---

## 1. Context & Problem

### What P16 proves

```
Customer Docs → Readiness → Trusted Packet → Broker (manual action)
```

The packet quality model works. The **case fragmentation model** does not match broker mental model or Constitution Rule 7.

### What is broken today

| Today | Broker mental model |
|-------|---------------------|
| Each extract/upload → new `case_id` via `save_case()` | One endorsement job = one work item |
| Inbox: 3 rows for insurance card + dec page + VIN photo | One row: "Andy Li · Add Vehicle · READY" |
| Document-first extract path bypasses merge primitives | Multi-day thread with corrections and follow-ups |

The legacy Unified Intake path has partial consolidation (`append_follow_up_message`, phone lookup, case boundary). The **P16 primary paths** (`/api/intake/add-car/extract`, policy review extract) always create a new record.

### Why Active Case exists

**Active Case** is the **primary business object** — the broker-facing unit of work. It answers: *"What job exists in my inbox?"*

Without Active Case consolidation:

- Chen Kui's office sees duplicate rows for one add-car job
- Phone Return Key (Constitution Rule 2) resumes a case, but new uploads may fork a second case
- ADR-004 WeCom thread continuity (Phase 2+) would recreate fragmentation on the channel that matters most

Active Case is **not** a CRM. It is intent-scoped work-item identity on top of existing `service_records`.

---

## 2. Definitions

Three layers serve different audiences. Do not collapse them.

| Term | Role | Audience | Maps to (Phase 1) |
|------|------|----------|-------------------|
| **Active Case** | Broker-facing work item | Broker inbox | `service_records.record_id` (= `case_id`) |
| **Evidence Event** | Inbound upload, message, or correction | System (append log) | `extra.evidence_events[]` (lightweight) |
| **Submission** | Immutable persisted evidence event with extraction snapshot | System audit / P18 | Phase 2 — `case_submissions` or equivalent |
| **Case Memory** | Merged field facts + conflict flags (internal truth) | System | Merged state behind packet; mutable on new evidence |
| **Trusted Packet** | Materialized best state for office action | Broker / office | `structured_payload.p16_broker_packet` |

**Alias rule (Phase 1):** `active_case_id` === `case_id` === `record_id`. No second identifier in Phase 1.

```
Broker sees Active Cases.
System records Evidence Events (Submissions in Phase 2).
Office works from Trusted Packet.
```

**TurboTax analogy:** Uploading a W2 does not create a new tax return. Uploading a dec page must not create a new broker case.

---

## 3. Active Case Semantics

### Minimum Active Case attributes (conceptual)

| Field | Purpose |
|-------|---------|
| `active_case_id` | Stable work-item identity (= existing `case_id`) |
| `person_link` | Normalized phone and/or opaque `person_link_key` — not a CRM graph |
| `intent` | Request type / `service_lane` (e.g. `add_vehicle`, `policy_review`) |
| `status` | Existing `case_status` / `lifecycle_status` |
| `readiness_state` | ADR-001 on **current Packet**: READY \| NEED_INFO \| BROKER_REVIEW |
| `source_channel` | `web` \| `wecom` \| `mixed` \| future adapter values |
| `vehicle_key` | Primary VIN for add-car lanes (nullable until known) |
| `conflict_state` | `none` \| `vin_conflict` \| `intent_ambiguous` \| `identity_ambiguous` |
| `merge_review_required` | Fail-closed flag when auto-merge is unsafe |
| `closed_at` | Broker-controlled terminal state (Constitution Rule 5) |

### Constitution Rule 7 relationship

Rule 7 — *One Customer = One Active Case* — governs **active** cases **within a single intent lane**:

- Same normalized phone + same intent + case not closed → merge candidate
- Cross-intent always splits (add-car ≠ policy review ≠ claim)
- Within add-car: conflicting VIN → **BROKER_REVIEW**, never silent second active case
- Historical closed cases may exist; Rule 7 applies to **open** cases only

Rule 7 is **constitutional law**. P16 runtime violates it on the extract path. ADR-005 defines the correction without expanding to CRM or multi-case customer pickers.

### Lifecycle (unchanged from P16)

Broker closes or reopens terminal states (Constitution Rule 5). Customer submits and appends; customer cannot close. No auto-close on idle timeout without broker visibility.

---

## 4. Merge Rules

A new inbound evidence event **attaches to an existing open Active Case** when **all** are true:

| # | Rule |
|---|------|
| M1 | **Same person link** — normalized phone match or bound `person_link_key` |
| M2 | **Same intent** — `service_lane` / request type must match |
| M3 | **Case not closed** — `case_status != closed`, `closed_at` null |
| M4 | **Within open window** — Phase 1 default: **no auto-expiry**; broker close is the terminal boundary. Configurable window deferred to Phase 2 if pilot requires it |
| M5 | **No hard conflict** — no conflicting VIN; no cross-intent boundary hit |

### Vehicle scope (add-car)

| Condition | Merge? |
|-----------|--------|
| No VIN on case; new upload provides VIN | Yes — fills gap |
| Same VIN (normalized) | Yes |
| Case has VIN A; new evidence has VIN B | **No auto-merge** → BROKER_REVIEW or new case |
| Extra vehicle mentioned in same thread | Borderline → reuse case boundary classifier |

### Resolver contract

Every intake write path **must** call a single resolver before creating or updating a case:

```
resolve_active_case_for_evidence(
  person_link,
  intent,
  vehicle_key,
  channel,
  evidence_payload
) → attach | create | broker_review
```

| Outcome | Behavior |
|---------|----------|
| `create` | New Active Case + first evidence event |
| `attach` | Append evidence; re-materialize Packet |
| `broker_review` | Attach evidence for audit if safe; set `merge_review_required`; **do not silently update Packet** until broker resolves |

**Fail closed:** When 2+ open cases match person_link + intent, outcome is `broker_review` — not silent "newest wins."

### Examples

| Scenario | Decision |
|----------|----------|
| Add vehicle + insurance card (same phone, same day) | Merge |
| Add vehicle + VIN follow-up (3 days later) | Merge |
| Policy review + second policy PDF | Merge |
| Claim message + add vehicle message | Split — different intent |
| Second add-car with different VIN while first open | BROKER_REVIEW or split — never silent merge |

---

## 5. Split Rules

Create a **new Active Case** when:

| # | Trigger |
|---|---------|
| S1 | Different intent |
| S2 | Different vehicle (hard conflicting VIN on open case) |
| S3 | Prior case closed |
| S4 | Conflicting VIN — two valid 17-char VINs, neither is correction of the other |
| S5 | Ambiguous identity — same phone, conflicting names; or `person_link_confidence` below threshold |
| S6 | Broker explicit "Start new request" |
| S7 | Case boundary = `new_issue` (reuse append boundary classifier) |

**Precedence:** Constitution Rule 7 applies **within intent lane only**. Cross-intent always splits.

---

## 6. BROKER_REVIEW on Merge Ambiguity

Set `merge_review_required=true` and Packet readiness to **BROKER_REVIEW** when:

| # | Condition |
|---|-----------|
| B1 | 2+ open cases match person_link + intent |
| B2 | Conflicting vehicle identity across evidence |
| B3 | Unclear intent or mixed claim + add-car language |
| B4 | Customer changes goal mid-thread (borderline boundary) |
| B5 | Identity ambiguity (WeCom ID ≠ phone; multiple person_link candidates) |
| B6 | Packet merge would overwrite a broker-trusted field without review |

**Phase 1 broker surface:** Conflict banner — *"New evidence conflicts with current packet — review required."* Full merge/split workbench tools are out of scope; manual case close is the escape hatch.

---

## 7. Packet Materialization

**Trusted Packet remains the execution artifact.** It is a **projection**, not the source of truth.

```
Evidence Events (append-only)
        ↓
Case Memory (merged facts + conflict flags — internal truth)
        ↓
Trusted Packet (materialized best state — broker primary view)
```

### Materialization rules

1. Process evidence chronologically.
2. Field-level merge: latest high-confidence **non-conflicting** value wins per field.
3. **Never silent-resolve VIN conflicts** → readiness = BROKER_REVIEW; retain both values with source attribution.
4. Re-run ADR-001 readiness mapping on merged result (`map_add_car_readiness()` pattern).
5. Write `p16_broker_packet`; bump `updated_at`; optional `packet_changed_since_view` signal (recommended).

**Broker sees Packet, not individual evidence events** by default. Evidence exists for audit and future Business Loop (Future Vision §2); collapsed in workbench.

Re-materialization **may change Packet readiness** when new evidence arrives (e.g. READY → BROKER_REVIEW on VIN conflict). This supersedes ADR-001 session-scoped one-directional readiness — see §10.

---

## 8. Relationship with Existing ADRs

| ADR | Relationship |
|-----|--------------|
| **ADR-001** | Readiness states apply to **Packet** after merge, not per evidence event. VIN conflict → BROKER_REVIEW unchanged. Rule #7 amended for multi-evidence cases (§10). |
| **ADR-002** | Timeline UI remains deferred. Evidence events / Submissions may feed internal `case_activity` later; no timeline panel in P17. |
| **ADR-003** | Packet remains product end state. Customer language unchanged. Broker manual action unchanged. |
| **ADR-004** | Channels remain adapters. Resolver is channel-agnostic. **WeCom Phase 2+ (thread continuity) must not ship without resolver integration.** Phase 4 multi-channel merge depends on this ADR. |

---

## 9. Relationship with Constitution Rule 7

Constitution Rule 7 mandates at most **one active add-car case** per customer phone. ADR-005 operationalizes Rule 7:

| Constitution | ADR-005 |
|--------------|---------|
| One active case per phone | Merge resolver enforces within intent lane |
| No customer case picker | Unchanged — customer resumes via phone |
| No auto second active case | Split on intent / hard conflict / closed prior |
| Broker closes prior before new job | Split rule S3 |

ADR-005 does **not** introduce Household, CRM portfolios, or multi-concurrent-service-record optimization.

---

## 10. Relationship with ADR-001 (Readiness on Multi-Evidence Cases)

ADR-001 Rule #7 states: *"A case does not go from READY back to NEED_INFO after broker opens it (UI constraint only; re-submission creates a new session)."*

That rule assumed **one upload session = one case**. Active Case consolidation invalidates the session-scoped interpretation:

| ADR-001 (today) | ADR-005 (corrected semantics) |
|-----------------|-------------------------------|
| Re-submission creates new session/case | Re-submission **attaches** when merge rules pass |
| Readiness one-directional per session | Readiness on **Packet** may change when new evidence arrives |
| Readiness on request | Readiness on **materialized Packet** |

**ADR-001 Rule #7 amendment (applied P17 Phase 2):**

Rule #7 in `ADR_001_REQUEST_READINESS.md` now reads: *"Readiness is evaluated on the materialized Trusted Packet. New evidence attached to an Active Case may change Packet readiness (including READY → BROKER_REVIEW on conflict). Per-field ✅ / ⚠️ / ❌ symbols remain stable within a single materialization until the next evidence append."*

This section documents the supersession rationale; ADR-001 is the canonical rule text.

---

## 11. AI Worker Philosophy & Business Loop (Structural Only)

**Preserved:**

- AI proposes; broker decides (Future Vision §8 Principle 1)
- Evidence-first — uploads and fields, not chat alone
- Broker Gate explicit before office action
- Business Loop sequencing preserved as **future** — not implemented in P17

**P17 enables (structure only):**

```
Missing info on Packet
  → still_needed_fields
  → [P18] draft follow-up → broker approve → customer reply (new evidence)
  → merge → re-materialize Packet → repeat
```

**P17 does not implement:** autonomous customer replies, auto-send, workflow engine, or carrier action.

---

## 12. Non-Goals (Explicit)

This ADR does **not** introduce or authorize:

| Excluded | See |
|----------|-----|
| CRM / Household | Future Vision §7.6 — P19+ |
| Timeline UI | ADR-002 |
| Bubble Map / Knowledge Graph | Out of scope |
| Business Loop execution | P18; Future Vision §4 gate |
| Worker Orchestration | Future Vision §8 |
| Carrier API / AMS write-back | ADR-003 |
| Multi-tenant platform | Decision Freeze §4 |
| Personal WeChat automation | ADR-004 |
| Customer login / accounts | Constitution Rule 1 |
| Submission drill-down UI (Phase 1) | Phase 2 |
| Mandatory legacy backfill | §14 Migration |

---

## 13. Implementation Gate

**Default gate** (Future Vision §4):

- 10+ real pilot cases (CK-001 … CK-010)
- Time savings documented (average ≥4 min saved)
- Broker feedback collected
- First $49 invoice paid

**Then:** P17 Phase 1 coding (add-car merge on extract first).

**Exception:** Founder explicit GO for a **pilot fragmentation fix** (add-car-only merge or read-only inbox dedup) before full gate — documented in sprint notes, not automatic.

**ADR-004 WeCom Phase 2+ blocked** until ADR-005 Phase 1 resolver is deployed on all write paths.

---

## 14. Storage & Migration (Implementation Notes — Gated)

| Layer | Phase 1 | Phase 2 |
|-------|---------|---------|
| Active Case | Existing `service_records` columns | Same |
| Evidence | `extra.evidence_events[]` lightweight log | Promote to `case_submissions` if audit volume requires |
| Case Memory | Merged fields in structured payload | Explicit conflict flags |
| Trusted Packet | `structured_payload.p16_broker_packet` | Same |

- No mandatory backfill of legacy duplicate rows in Phase 1
- Deprecate silent "newest wins" when multiple open cases match — surface BROKER_REVIEW instead
- Single resolver on: add-car extract, policy review extract, Unified Intake greenfield/append, future Channel Adapters

---

## 15. Acceptance Criteria (Phase 1 — When Built)

**Chen Kui scenario:**

> Same phone, same add-car intent: insurance card + dec page + VIN screenshot  
> → **1 inbox row** · **1 refreshed Trusted Packet** · readiness reflects merged evidence  
> → VIN conflict across evidence → **BROKER_REVIEW**, not silent merge

---

## 16. Risks

| Risk | Mitigation |
|------|------------|
| Silent wrong merge (wrong VIN attached) | Fail closed → BROKER_REVIEW |
| Dual-path divergence (extract vs triage) | Single resolver on all write paths |
| Scope creep toward CRM | No Household; `person_link` only |
| ADR-001 readiness confusion | ADR-001 Rule #7 amended (§10); conflict banner on Packet change |
| Legacy duplicate inbox rows | BROKER_REVIEW when count > 1; optional backfill later |
| WeCom before consolidation | ADR-004 Phase 2+ blocked until resolver exists |

---

## 17. Reconsideration Trigger

Revisit this ADR if:

1. Brokers prefer **separate rows per upload** over consolidation toil
2. BROKER_REVIEW merge conflicts exceed duplicate-row pain in pilot data
3. Validation gate fails — defer all P17 build
4. Paid customer explicitly requests Household / CRM before Active Case is stable

---

*Related: `ADR_001_REQUEST_READINESS.md` · `ADR_002_NO_TIMELINE_V1.md` · `ADR_003_NO_CARRIER_API_V1.md` · `ADR_004_ENTERPRISE_WECOM_CHANNEL_INTEGRATION.md` · `docs/p16/P16_FUTURE_VISION.md` §7 · `docs/product_constitution/P16_CUSTOMER_FIRST_CONSTITUTION.md` Rule 7*
