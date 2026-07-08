# P19J-1a — Routing Decision Log

**Date:** 2026-07-08  
**Branch:** `sprint/p16-trust-layer`  
**Status:** **IMPLEMENTED** · **NOT DEPLOYED**

---

## 1. Goal

Add a unified structured routing decision log (`wecom_routing_decision_v1`) at key WeCom routing exits so engineers can answer *why* the system chose a given reply — without DB persistence, Workbench UI, or workflow engine changes.

---

## 2. Why this is needed

P19H-2.1 fixed Claim interrupt during active Add Vehicle, but phone smoke exposed that routing priority was invisible. Without a decision log we could not tell whether:

- Claim was deferred as secondary topic
- Lane-switch prompt won
- Injury safety override fired
- Active workflow state blocked Claim start

This sprint adds **observability only** — no behavior change.

---

## 3. User-found workflow confusion

**Context:** User in active Add Vehicle workflow said `我要理赔`.

**Before P19H-2.1:** System replied generic secondary-topic deferral (`先完成当前请求`).

**After P19H-2.1:** Lane-switch prompt or Claim start — but still no structured record of which priority rule applied.

**This sprint:** Every covered exit emits `wecom_routing_decision_v1` with `priority_rule`, `decision`, `reason`, `response_type`.

---

## 4. What was implemented

| File | Change |
|------|--------|
| `services/fiqa_api/wecom/routing_observability.py` | **New** — `RoutingDecision` dataclass, redaction/hashing helpers, `emit_routing_decision()` |
| `services/fiqa_api/wecom/claim_basics.py` | Emit logs at Claim interrupt, confirmed start, injury, basics collection, C1, claim question |
| `services/fiqa_api/wecom/slice.py` | Emit logs at secondary-topic deferral, Add Vehicle progress, Phase 2 collection |
| `tests/test_p19j1a_routing_decision_log.py` | **New** — 12 tests (redaction + 9 routing scenarios) |

**Not changed:** DB schema, Workbench UI, Mermaid generation, deploy, user-facing copy.

---

## 5. RoutingDecision schema

```json
{
  "event": "wecom_routing_decision_v1",
  "route_id": "<msg_id>",
  "priority_rule": "<canonical rule>",
  "decision": "<canonical decision>",
  "reason": "<human-readable why>",
  "response_type": "<reply category>",
  "active_case_id": "...",
  "active_workflow": "add_vehicle | claim",
  "active_state": "...",
  "active_phase": "...",
  "incoming_intent": "...",
  "workflow_id": "claim_simplified | add_vehicle",
  "safety_flags": ["injury_mentioned"],
  "created_case_id": "...",
  "switched_workflow": "claim",
  "external_user_hash": "<sha256>",
  "text_hash": "<sha256>",
  "text_length": 12,
  "text_redacted_preview": "...",
  "source": "wecom",
  "version": "v1"
}
```

---

## 6. Privacy / redaction behavior

| Field | Policy |
|-------|--------|
| `text_redacted_preview` | Max 80 chars; phone runs (10+ digits) → `[PHONE]`; email → `[EMAIL]`; VIN-like 17-char → `[VIN]` |
| `text_hash` | SHA-256 of full message (for dedup/debug without storing raw text) |
| `text_length` | Character count |
| `external_user_hash` | SHA-256 of `wecom_ext:{id}` — raw `external_userid` never logged |

---

## 7. Priority rules covered (first pass)

| priority_rule | When |
|---------------|------|
| `injury_safety_override` | Injury marker during any workflow |
| `claim_interrupt_during_active_add_vehicle` | Claim start while Add Vehicle active → lane-switch prompt |
| `claim_confirmed_start` | User confirms `开始理赔` during active Add Vehicle |
| `claim_question_during_active_add_vehicle` | How-to / liability question during Add Vehicle |
| `lane_switch_continue_add_vehicle` | User chooses continue Add Vehicle |
| `lane_switch_contact_broker` | User chooses contact broker |
| `active_claim_basics_collection` | Collecting basics or sending C1 |
| `claim_start_no_active_case` | Claim start with no active workflow |
| `add_vehicle_active_progress` | Progress card route |
| `add_vehicle_phase2_collection` | Phase 2 text collection |
| `generic_secondary_topic_deferral` | Non-Claim secondary topic during active workflow |

---

## 8. Example log payloads

### Claim interrupt

```json
{
  "event": "wecom_routing_decision_v1",
  "priority_rule": "claim_interrupt_during_active_add_vehicle",
  "decision": "lane_switch_prompt",
  "response_type": "claim_lane_switch",
  "reason": "claim_start_intent_outranks_active_add_vehicle_secondary_topic",
  "active_workflow": "add_vehicle",
  "incoming_intent": "claim_intake"
}
```

### Claim confirmed start

```json
{
  "priority_rule": "claim_confirmed_start",
  "decision": "start_claim_flow",
  "response_type": "claim_start",
  "reason": "user_confirmed_claim_start_during_active_workflow",
  "switched_workflow": "claim"
}
```

### Injury override

```json
{
  "priority_rule": "injury_safety_override",
  "decision": "safety_manual_reply",
  "response_type": "claim_safety_manual",
  "reason": "injury_marker_detected_highest_priority",
  "safety_flags": ["injury_mentioned"]
}
```

### Claim basics C1

```json
{
  "priority_rule": "active_claim_basics_collection",
  "decision": "send_claim_c1",
  "response_type": "claim_c1",
  "reason": "active_claim_waiting_for_accident_basics",
  "workflow_id": "claim_simplified"
}
```

### Secondary-topic deferral

```json
{
  "priority_rule": "generic_secondary_topic_deferral",
  "decision": "defer_secondary_topic",
  "response_type": "secondary_topic_deferred",
  "reason": "non_claim_secondary_topic_during_active_workflow"
}
```

---

## 9. Tests

```bash
PYTHONPATH=. python3 -m pytest tests/test_p19j1a_routing_decision_log.py -q
# 12 passed
```

Regression suites (P19H-2.1, P19H-2, P19I-2, WeCom slice/reply/active_case) — all passed.

---

## 10. QA gate

```bash
bash scripts/check_chen_kui_demo_environment.sh --cloud-api
# Result: PASS — QA UI + Cloud Run API + Cloud SQL aligned
```

No deploy performed this sprint.

---

## 11. Constraints honored

| Constraint | Status |
|------------|--------|
| No DB / schema change | ✅ |
| No Workbench Debug UI | ✅ |
| No Mermaid generation | ✅ |
| No deploy | ✅ |
| No routing behavior change | ✅ |
| No raw PII in logs | ✅ |

---

## 12. Known limitations

- Logs are **not persisted in DB** — rely on Cloud Logging retention/search.
- Not every obscure route covered in first pass (generic menu, fallback, media intake).
- Workbench Debug Panel not implemented.
- Mermaid auto diagrams not implemented.
- No replay / scenario simulator yet.

---

## 13. Next recommended step

- **P19J-1b** — Mermaid auto diagrams from `WorkflowDefinition` + lane constants
- **P19J-1c** — Scenario simulator / replay using captured routing decisions

---

## 14. GO / HOLD

**GO** — Routing decision log is ready for deploy in a follow-up sprint. Next loop should either wire Workbench debug panel (P19J-2) or Mermaid generation (P19J-1b) — not both at once.

**STOP** — P19J-1a scope complete.
