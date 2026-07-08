# P19J-1c — Workflow Scenario Simulator

**Date:** 2026-07-08  
**Branch:** `sprint/p16-trust-layer`  
**Status:** **DEPLOYED** (`fiqa-api-00169-wjc`) · **PHONE SMOKE PENDING**

---

## 1. Goal

Add a lightweight local **Scenario Simulator** that runs multi-turn WeCom workflow conversations against the real routing code, validating both customer-facing replies and P19J-1a routing decision logs — without deploy, DB, or Workbench UI.

---

## 2. Why simulator is needed

Phone smoke exposed state confusion when Add Vehicle and Claim workflows overlap:

```
Active Add Vehicle → 我要理赔 → 开始理赔 → accident basics → Claim C1
```

Before P19H-2.1, Claim intents were swallowed by secondary-topic deferral. After P19H-2.1 + P19J-1a, routing is correct but regressions are hard to catch without re-running full phone smoke.

The simulator automates this multi-turn path locally in seconds.

---

## 3. Relationship to P19J-1a routing decision log

| P19J-1a | P19J-1c |
|---------|---------|
| Emits `wecom_routing_decision_v1` at routing exits | **Consumes** those logs during scenario runs |
| Single-turn unit tests | Multi-turn scenario harness |
| Documents priority_rule / decision / reason | **Asserts** them per step |

Simulator does not duplicate routing logic — it calls `process_kf_msg_or_event()` (same as production slice) and captures logs from `routing_observability.py`.

---

## 4. Scenario simulator design

**Module:** `services/fiqa_api/wecom/workflow_scenario_simulator.py`

| Component | Purpose |
|-----------|---------|
| `ScenarioStep` | One inbound message + expected response snippets + routing fields |
| `WorkflowScenarioSession` | Maintains `external_userid`, msg IDs, JSON store context across turns |
| `RoutingDecisionCapture` | Logging handler for `wecom_routing_decision_v1` |
| `route_inbound_text()` | Routes via real `slice.py` orchestrator |
| `run_scenario()` | Multi-turn runner with per-step validation |
| Predefined scenario fixtures | Reused by pytest and CLI |

**CLI:** `scripts/run_workflow_scenarios.py` — prints PASS/FAIL per step.

---

## 5. Scenarios covered

| # | Name | Context | Steps |
|---|------|---------|-------|
| 1 | `add_vehicle_to_claim_interrupt` | Active Add Vehicle | 我要理赔 → 开始理赔 → accident basics |
| 2 | `add_vehicle_injury_override` | Active Add Vehicle | 有人受伤了，我要理赔 |
| 3 | `add_vehicle_claim_question` | Active Add Vehicle | 出事故了怎么办 |
| 4 | `add_vehicle_secondary_topic` | Active Add Vehicle | 我还想问一下续保 |
| 5 | `no_active_claim_basics` | No active case | 我要理赔 → accident basics |
| 6 | `add_vehicle_restart` | Clean context | 重新加车 |

---

## 6. Most important scenario

**`add_vehicle_to_claim_interrupt`** — the phone-smoke repro path:

| Step | Input | Expected routing | Expected reply |
|------|-------|------------------|----------------|
| 1 | 我要理赔 | `claim_interrupt_during_active_add_vehicle` / `lane_switch_prompt` | Lane-switch prompt (not deferral) |
| 2 | 开始理赔 | `claim_confirmed_start` / `start_claim_flow` | Claim start card |
| 3 | Accident basics | `active_claim_basics_collection` / `send_claim_c1` | C1 with 时间/地点/描述 |

Each step asserts `priority_rule`, `decision`, `response_type`, and key response substrings.

---

## 7. What bug this prevents

- Claim swallowed by `generic_secondary_topic_deferral` during active Add Vehicle
- Lane-switch prompt skipped after P19H routing changes
- Claim C1 blocked after confirmed start
- Injury override demoted below deferral
- Claim question routed to deferral instead of safe Q&A

---

## 8. Tests

```bash
PYTHONPATH=. python3 -m pytest tests/test_p19j1c_workflow_scenario_simulator.py -q
# 8 passed
```

CLI:

```bash
PYTHONPATH=. python3 scripts/run_workflow_scenarios.py
# All 6 scenarios PASSED
```

Regression (P19J-1a, P19H, P19I, WeCom) — all passed.

---

## 9. QA gate

```bash
bash scripts/check_chen_kui_demo_environment.sh --cloud-api
# Result: PASS
```

## Scenario CLI Pre-Deploy Evidence

```bash
PYTHONPATH=. python3 scripts/run_workflow_scenarios.py
```

**Result:** All 6 scenarios PASS

**Highlight — `add_vehicle_to_claim_interrupt`:**

| Step | Input | Routing |
|------|-------|---------|
| 1 | 我要理赔 | `claim_interrupt_during_active_add_vehicle` / `lane_switch_prompt` |
| 2 | 开始理赔 | `claim_confirmed_start` / `start_claim_flow` |
| 3 | Accident basics | `active_claim_basics_collection` / `send_claim_c1` |

Pre-deploy pytest: 8/8 passed. Regression: all passed.

---

## Deploy Evidence

| Field | Value |
|-------|-------|
| Branch | `sprint/p16-trust-layer` |
| Deployed commit | `f39e46c` |
| GIT_SHA | `f39e46cb6` |
| Backend revision | `fiqa-api-00169-wjc` |
| Backend URL | https://fiqa-api-g7zatxrycq-uw.a.run.app |
| Deploy time (UTC) | 2026-07-08T06:29:17Z |
| `/health/live` | 200 |
| `/readyz` | 200 — `intake_core_readiness: true` |
| Pre-deploy QA gate | PASS |
| Post-deploy QA gate | PASS |
| Log check | Clean — optional Qdrant/Redis warnings only |
| Live routing log | **PENDING** until WeCom phone smoke |
| Frontend deployed | No |
| Schema changed | No |
| DB logging | No |
| Workbench UI | No |
| Mermaid generation | No |

Deploy command: `bash scripts/deploy_paid_pilot.sh`

---

## Andy Phone Retest Checklist

*(Same as P19J-1a evidence — simulator validated these paths locally; phone confirms production.)*

### Smoke A — Active Add Vehicle + Claim interrupt

Context: Active Add Vehicle case open. Input: `我要理赔`

Expected: Lane-switch prompt; offers 开始理赔 / 继续加车 / 联系陈总; NOT「先完成当前请求」

### Smoke B — Confirm Claim start

Input: `开始理赔` → 【理赔资料收集】 + accident basics prompt

### Smoke C — Claim basics C1

Input: accident basics one-liner → 【理赔资料 · 第 1 步完成 ✅】 + 准备事故照片; no Add Vehicle re-blocking

### Smoke D — Injury

Input: `有人受伤了，我要理赔` → 【安全提醒】; no C1; no deferral

### Smoke E — Non-Claim secondary topic

Input: `我还想问一下续保` → secondary-topic deferral

### Smoke F — Routing decision log

After messages, confirm `wecom_routing_decision_v1` in Cloud Logging with expected `priority_rule` values.

**Status:** Deploy **GO** · Phone smoke **PENDING**

---

## 10. Constraints honored

| Constraint | Status |
|------------|--------|
| Backend deploy only (no frontend) | ✅ |
| No schema / DB logging | ✅ |
| No Workbench UI | ✅ |
| No Mermaid generation | ✅ |
| Reuses real routing (not fake engine) | ✅ |
| No production copy changes | ✅ |

---

## 11. Known limitations

- Relies on JSON test store / fake WeCom env (not production replay).
- Not a full production trace replay engine.
- Does not persist runtime traces.
- Does not generate Mermaid diagrams.
- Add Vehicle restart scenario does not yet assert `add_vehicle_*` priority_rule (route not fully logged on generic start).
- Rare/obscure routes not covered.

---

## 12. Next recommended step

- **Phone smoke** — run Andy checklist; confirm live `wecom_routing_decision_v1` in Cloud Logging
- **P19J-1b** — Mermaid auto diagrams from `WorkflowDefinition`

---

## 13. GO / HOLD

**GO** — Deployed with simulator-validated paths. Run phone smoke checklist; then confirm live routing logs.

**STOP** — P19J-1c deploy prep complete; phone smoke pending.
