# P19J-1a — Routing Decision Log

**Date:** 2026-07-08  
**Branch:** `sprint/p16-trust-layer`  
**Status:** **DEPLOYED** (`fiqa-api-00169-wjc`) · **PHONE SMOKE PENDING**

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
- No replay / scenario simulator yet. *(P19J-1c simulator added locally — see `p19j1c_workflow_scenario_simulator_2026_07_08.md`)*

---

## Deploy Evidence

| Field | Value |
|-------|-------|
| Branch | `sprint/p16-trust-layer` |
| Deployed commit | `f39e46c` (includes `a773dc3` routing log) |
| GIT_SHA | `f39e46cb6` |
| Backend revision | `fiqa-api-00169-wjc` |
| Backend URL | https://fiqa-api-g7zatxrycq-uw.a.run.app |
| Deploy time (UTC) | 2026-07-08T06:29:17Z |
| `/health/live` | 200 — `{"ok":true}` |
| `/readyz` | 200 — `intake_core_readiness: true` |
| Pre-deploy QA gate | PASS |
| Post-deploy QA gate | PASS |
| Log check | Clean — Qdrant/Redis/embedding optional warnings only; no `routing_observability` import errors |
| Live `wecom_routing_decision_v1` | **PENDING** — no WeCom message since deploy at log check time |
| Frontend deployed | No |
| Schema changed | No |
| DB logging | No |
| Workbench UI | No |
| Mermaid generation | No |
| OCR / H5 Claim / Workbench Claim | No |

---

## Andy Phone Retest Checklist

### Smoke A — Active Add Vehicle + Claim interrupt

**Context:** Active Add Vehicle case open.

**Input:** `我要理赔`

**Expected:**

- Lane-switch prompt
- Mentions current Add Vehicle flow
- Offers: 1. 开始理赔 · 2. 继续加车 · 3. 联系陈总
- Does **NOT** say「先完成当前请求」

**Log check:** `priority_rule = claim_interrupt_during_active_add_vehicle`

### Smoke B — Confirm Claim start

**Input:** `开始理赔`

**Expected:**

- 【理赔资料收集】
- Asks for accident time / location / description
- Not generic menu

**Log check:** `priority_rule = claim_confirmed_start`

### Smoke C — Claim basics C1

**Input:** `今天上午10点，在 Irvine Blvd 和 Culver 附近，对方变道刮到我左前门`

**Expected:**

- 【理赔资料 · 第 1 步完成 ✅】
- Shows time / location / description
- Next step: 准备事故照片
- No Add Vehicle re-blocking
- No H5 broken link
- No claim-filed language (e.g.「理赔已经提交」)

**Log check:** `priority_rule = active_claim_basics_collection`, `decision = send_claim_c1`

### Smoke D — Injury

**Input:** `有人受伤了，我要理赔`

**Expected:**

- 【安全提醒】
- No C1
- No「先完成当前请求」
- No liability / coverage promise

**Log check:** `priority_rule = injury_safety_override`

### Smoke E — Non-Claim secondary topic

**Input:** `我还想问一下续保`

**Expected:** Secondary-topic deferral still works

**Log check:** `priority_rule = generic_secondary_topic_deferral`

### Smoke F — Routing decision log check

After phone messages, query Cloud Logging:

```bash
gcloud logging read \
  'resource.type="cloud_run_revision" AND resource.labels.service_name="fiqa-api" AND textPayload:"wecom_routing_decision_v1"' \
  --project optimal-disk-472305-e2 \
  --limit 50 \
  --format='value(timestamp,textPayload)'
```

Confirm:

- `wecom_routing_decision_v1` appears per message
- `priority_rule` values match smoke path
- No raw phone / email / VIN in `text_redacted_preview`
- `external_user_hash` present (not raw `external_userid`)

**Status:** Deploy **GO** · Phone smoke **PENDING** · Live routing log **PENDING**

---

## 13. Next recommended step

- **P19J-1b** — Mermaid auto diagrams from `WorkflowDefinition` + lane constants
- **P19J-1c** — Scenario simulator / replay using captured routing decisions

---

## 14. GO / HOLD

**GO** — Deployed (`fiqa-api-00169-wjc`). Phone smoke pending to confirm live `wecom_routing_decision_v1` in Cloud Logging.

**STOP** — P19J-1a deploy complete; await phone retest.
