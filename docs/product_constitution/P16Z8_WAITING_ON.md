# P16-Z8 Phase 4 — Waiting-On Archaeology

**Date:** 2026-06-02  
**Sprint:** P16-Z8 Memory Hardening Archaeology  
**Search terms:** `waiting_on`, `follow_up`, `case_activity`, carrier, customer, office  
**Sources:** `case_store.py`, `BrokerWorkbenchTab.tsx`, `intakePure.ts`, P16-Z7 waiting report, archive state_workflow specs

---

## Executive summary

Waiting-on is **already built as a manual state machine** — data model, validation, PATCH API, queue filter, activity logging, and tracking summary all exist. **Zero triage inference.** Role D: **0/9 carrier-wait phrases auto-set responsibility.**

| Component | Status |
|-----------|--------|
| State model (client/carrier/office/none) | **Built** |
| Persistence + validation | **Built** |
| API PATCH | **Built** |
| Activity audit on change | **Built** |
| Queue filter | **Built** |
| Triage → waiting_on inference | **Missing** |
| Auto `next_contact_by` from deadline | **Missing** |
| Prominent UX | **Hidden** (collapsed editor) |

---

## How much state machine already exists?

### Layer 1 — Data model (production-ready)

```python
# case_store.py
VALID_WAITING_ON = frozenset({"none", "client", "carrier", "office"})
update_case_follow_up(case_id, waiting_on, next_contact_by)
```

- Preserved across append: `append_follow_up_message()` L1108
- Normalized on case create: default `waiting_on: none`
- Humanized for activity: `_humanize_waiting_on()`

### Layer 2 — Follow-up type (triage engine)

| `follow_up_type` | Meaning | Sets waiting_on? |
|------------------|---------|------------------|
| `correction` | Customer corrected prior | ❌ |
| `already_sent` | Materials/docs sent | ❌ |
| `clarification_question` | Customer asking meaning | ❌ |
| `new_info` | New facts | ❌ |
| `status_check` | (implicit in Day 3 pings) | ❌ |

`_derive_follow_up_type()` L2462 — **feeds reply policy only**, not responsibility.

### Layer 3 — Case activity audit

| Event type | Trigger |
|------------|---------|
| `follow_up_updated` | PATCH waiting_on |
| `follow_up_added` | Customer append |
| `case_created` | First persist |
| State transitions | `case_lifecycle.py` |

**~15 activity event types** in `case_store.py` — full office audit trail exists.

### Layer 4 — UI surfacing

| Surface | Status |
|---------|--------|
| `getCaseTrackingSummary()` | ✅ Queue one-liner when set |
| Follow-up editor | ⚠️ Collapsed in workbench |
| `waiting_on: client` queue filter | ✅ Built |
| Post-append “who waits?” prompt | ❌ Missing |
| Deadline widget → next_contact_by | ❌ Missing |

### Layer 5 — Archived specs (hidden design)

| Spec | Location | Status |
|------|----------|--------|
| Workflow state contract | `state_workflow_backbone_phase2/04_WORKFLOW_STATE_CONTRACT_SPEC.md` | **Not wired** |
| Transition guardrails | `04_TRANSITION_GUARDRAIL_SPEC.md` | **Not wired** |
| Office follow-up visibility | `WORKBENCH_OFFICE_TOOL_PROFESSIONALIZATION/04_*` | **Partial UI** |
| Handoff office next action | `HANDOFF_OFFICE_NEXT_ACTION_SPEC.md` | **Process doc** |

---

## TOP 20 existing waiting capabilities

| # | Capability | Location | Auto? |
|---|------------|----------|-------|
| 1 | `waiting_on` enum (4 values) | `case_store.py` | Manual |
| 2 | `next_contact_by` date field | `case_store.py` | Manual |
| 3 | `update_case_follow_up()` API | `case_store.py` L773 | Manual |
| 4 | Validation + normalization | `_validate_waiting_on()` | Built |
| 5 | Activity log on change | `follow_up_updated` event | Built |
| 6 | Preserve on append | `append_follow_up_message` | Built |
| 7 | Queue `waiting_on: client` filter | `BrokerWorkbenchTab.tsx` | Built |
| 8 | `getCaseTrackingSummary()` | `intakePure.ts` | Display |
| 9 | `still_needed_fields` → implies client wait | Triage | Implicit |
| 10 | `broker_next_step` → implies office wait | Triage | Implicit |
| 11 | `verify_carrier_received` still_needed | Payment/doc lanes | Implicit |
| 12 | `_derive_follow_up_type()` | `triage.py` | Reply only |
| 13 | `collection_stage` | `triage.py` | Backend |
| 14 | `_extract_deadline_hint()` | Summary prose | No link to next_contact_by |
| 15 | Category urgency drives manual priority | Classifier | Indirect |
| 16 | `case_activity[]` full audit | GET case API | Built |
| 17 | Postgres `state_history` mirror | `service_record_repository.py` | Hidden |
| 18 | `follow_up_type: already_sent` | Materials wait signal | No waiting_on map |
| 19 | Claim adjuster language in summary | Triage prose | No waiting_on map |
| 20 | CAPABILITY_05 lifecycle contract | Docs | Spec only |

---

## TOP 10 missing automations

| # | Automation | Trigger phrases | Suggested value | Effort |
|---|------------|-----------------|-----------------|--------|
| 1 | Carrier wait inference | adjuster, UW, carrier, 保险公司, underwriting | `carrier` | 4 hr |
| 2 | Client wait inference | 还缺, still need, send me, 材料 | `client` | 2 hr |
| 3 | Office wait inference | quote, refund, 报价, 什么时候生效 | `office` | 2 hr |
| 4 | Deadline → next_contact_by | `_extract_deadline_hint()` | ISO date suggest | 4 hr |
| 5 | Day 3 status ping detection | "any update", "有消息吗", "update?" | keep same waiting_on | 2 hr |
| 6 | Post-append responsibility prompt | After append API success | UI modal | 0.5 day |
| 7 | `waiting_on` in triage result (suggest) | New optional field | Engine emit | 4 hr |
| 8 | Auto-set on `verify_carrier_received` | still_needed present | `carrier` | 2 hr |
| 9 | Claim carrier delay | CL04 adjuster phrases | `carrier` | 2 hr |
| 10 | Activity prominence on responsibility change | follow_up_updated | Default-open | 2 hr UI |

---

## Phase 4 verdict

**~70% of waiting-on infrastructure exists.** Missing piece is **triage heuristic → suggest waiting_on** (0.5 day). Do **not** build WaitingOnEngine service — extend `triage.py` + optional PATCH on accept.
