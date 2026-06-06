# P16-Z10B Phase 1 — Waiting-On Archaeology Refresh

**Date:** 2026-06-02  
**Sprint:** P16-Z10B Memory Completion  
**Sources:** P16-Z6–Z10A, `case_store.py`, `triage.py`, `ROLE_D_WAITING_ON_REPORT.md`

---

## Executive summary

Waiting-on is a **manual PATCH state machine** with full persistence, validation, queue filter, and activity audit. **Triage did not infer responsibility** until Z10B. Role D baseline: **0/9** carrier-wait phrases auto-suggested.

---

## What already exists?

| Layer | Artifact | Auto? |
|-------|----------|-------|
| Data model | `waiting_on`: none · client · broker · carrier · underwriting | Manual PATCH |
| Date | `next_contact_by` | Manual |
| API | `update_case_follow_up()` in `case_store.py` | Manual |
| Validation | `_validate_waiting_on()` | Built |
| Append preserve | `append_follow_up_message` keeps waiting_on | Built |
| Activity | `follow_up_updated`, `follow_up_added` | Built |
| Queue | `waiting_on: client` filter in workbench | Built |
| Display | `getCaseTrackingSummary()` | Built if set |
| Triage signals | `still_needed_fields`, `broker_next_step`, `follow_up_type` | Implicit only |
| Deadline prose | `_extract_deadline_hint()` in summary | No → `next_contact_by` |
| Spec (unwired) | CAPABILITY_05 lifecycle contract | Docs only |

**Note:** Z8 docs used `office`; production enum uses **`broker`** for back-office work.

---

## What is manual today?

1. Broker selects `waiting_on` in collapsed follow-up editor after every append  
2. `next_contact_by` never suggested from deadline hint  
3. Day-3 status pings (“有回复吗”) do not tag carrier vs UW vs office  
4. Claim adjuster-delay language ignored for responsibility  
5. `verify_carrier_received` in still_needed does not set `waiting_on: carrier`  
6. No triage field for assistant paste workflow  

---

## TOP 20 waiting_on capabilities already built

| # | Capability | Location |
|---|------------|----------|
| 1 | `waiting_on` enum (5 values incl. underwriting) | `case_store.py` |
| 2 | `next_contact_by` ISO/date string | `case_store.py` |
| 3 | `update_case_follow_up()` | `case_store.py` L773 |
| 4 | Normalization + validation | `_validate_waiting_on()` |
| 5 | Activity log on responsibility change | `follow_up_updated` |
| 6 | Preserve on customer append | `append_follow_up_message` |
| 7 | Default `waiting_on: none` on create | `save_case_from_triage` |
| 8 | Queue filter `waiting_on: client` | `BrokerWorkbenchTab.tsx` |
| 9 | Tracking summary one-liner | `intakePure.ts` |
| 10 | `still_needed_fields` → client wait implied | `triage.py` |
| 11 | `broker_next_step` → office work implied | `triage.py` |
| 12 | `verify_carrier_received` still_needed | payment/doc lanes |
| 13 | `_derive_follow_up_type()` | reply policy only |
| 14 | `collection_stage` | backend |
| 15 | `_extract_deadline_hint()` | summary prose |
| 16 | Category urgency | classifier |
| 17 | `case_activity[]` full audit | GET case API |
| 18 | Postgres `waiting_on` mirror | `service_record_repository.py` |
| 19 | `follow_up_type: already_sent` | materials signal |
| 20 | Claim adjuster language in summary | prose only (pre-Z10B) |

---

## TOP 10 missing automations (pre-Z10B)

| # | Gap | Z10B status |
|---|-----|-------------|
| 1 | Carrier wait inference | **Shipped** — `_suggest_waiting_on` |
| 2 | Client wait inference | **Shipped** |
| 3 | Office/broker wait inference | **Shipped** (`broker`) |
| 4 | Underwriting wait inference | **Shipped** |
| 5 | Deadline → `next_contact_by` | Not built (out of scope) |
| 6 | Day-3 status ping routing | **Partial** — via status-check branch |
| 7 | `suggested_waiting_on` on triage result | **Shipped** |
| 8 | Auto-set on `verify_carrier_received` | **Partial** — suggests carrier |
| 9 | Claim carrier delay → carrier | **Shipped** |
| 10 | Post-append UX prompt | Not built (UI out of scope) |

---

## Phase 1 verdict

**~75% infrastructure existed; 0% inference.** Z10B adds suggest-only triage field — no new service, table, or API.
