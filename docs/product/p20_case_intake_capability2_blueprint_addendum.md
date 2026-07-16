# P20 Blueprint Addendum — Pre-task Case Intake (Capability 2)

**Date:** 2026-07-15  
**Status:** Additive addendum to `p20_workflow_timeline_blueprint.md`  
**Scope:** Administrative / pre-task events and lifecycle for Broker New Case + Missing Information + Request Draft.  
**Non-goals:** Does not alter frozen canonical workflow states, Slice 1 Request More event semantics, or customer Next Action rules.

## 1. Administrative case lifecycle

| Marker | Meaning |
|---|---|
| `draft` | Pre-task administration. Case record exists; no customer task/invite. |
| `active` | Customer access issued (Capability 3+). |
| `terminal` | Case closed under existing terminal governance. |

`draft` is **not** a canonical workflow state. Canonical workflow remains engine-owned and starts when an invite opens / `task_started` (unchanged).

## 2. Supporting-domain events (broker visibility)

| Event | When | State effect |
|---|---|---|
| `case_created` | Broker `CreateClaim` accepted | Admin lifecycle → `draft`; no canonical transition |
| `missing_information_assessed` | Deterministic checklist computed at create/refresh | Projection only |
| `request_draft_saved` | Broker `SaveRequestDraft` changes selected items | No Request More group; no customer action |
| `fact_status_updated` | Broker marks N/A / needs_correction / etc. | Fact records append-safe; confirmed values never silently deleted |

Required event fields follow the Blueprint catalog pattern: `event_id`, `case_id`, `event_type`, `command_id`, `correlation_id`, `sequence_number`, `aggregate_version`, `actor`, `actor_identity`, `visibility`, `evidence`, `idempotency_key`, `created_at`.

## 3. Commands in this capability

| Command | Durable outcome | Must not |
|---|---|---|
| `CreateClaim` | Case + intake aggregate + `case_created` | Create invite, Request More, or customer next action |
| `SaveRequestDraft` | One draft per case; CAS via `expected_case_version` | Create open request group |
| `UpdateFactStatus` | Fact status with preserved prior value | Demote confirmed → missing |

Draft edits are saved through **explicit broker commands** (`SaveRequestDraft`), not per-keystroke snapshots. Identical content under a new command does not spam events when unchanged within the same accepted version path; duplicate command ids replay the original outcome.

## 4. Missing-information statuses

`missing` | `unknown` | `supplied_unconfirmed` | `confirmed` | `needs_correction` | `not_applicable`

Confirmed facts must not be classified as missing. Needs-correction preserves `previous_value`.

## 5. Slice 1 compatibility

Slice 1 tables/events/UI remain authoritative for active Request More. Capability 2 draft items use compatible `item_type` vocabulary so Capability 3 can promote a draft into `CreateRequestMore` later without renaming.
