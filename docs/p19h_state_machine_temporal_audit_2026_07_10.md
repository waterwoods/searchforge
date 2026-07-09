# P19H — Workflow State Machine Temporal Audit

**Date:** 2026-07-10  
**Branch:** `sprint/p16-trust-layer`  
**Type:** Read-only audit + simulation matrix + invariant tests  
**Agent role:** Parallel audit agent (no production code changes)

---

## 1. Executive Summary

This audit verifies P19H Claim Story Recorder / Add Car / Workbench workflow against the **Start Card / End Card trust contract** (P19H-3f-1b, 3f-1c, 3f-2). The codebase has shipped the major boundary fixes; most historical risks are now **PASS**. Remaining gaps are narrow (H5 cloud smoke env, browser automation, post-`broker_done` customer restart flows).

| Metric | Count |
|--------|-------|
| Simulation matrix rows | 24 |
| **PASS** | 21 |
| **FAIL** | 0 |
| **UNKNOWN** | 2 |
| **NEEDS TEST** | 1 |

**Verdict: GO** — core temporal invariants hold. **HOLD** only for human-pending browser smoke and H5 cloud token alignment (known env issue, not workflow logic).

**Production code changed by this audit:** No  
**Conflict with main Agent:** No (docs + tests only; main Agent owns `intent.py`, `slice.py`, `reply.py`, `claim_basics.py`, `case_store.py`, `workflow_scenario_simulator.py`)

---

## 2. Current State Model

### Customer / channel states

| # | State | System representation | Customer label |
|---|-------|----------------------|----------------|
| 1 | `idle` / consultation | No open formal lane | （无）/ 咨询中 |
| 2 | `raw_inbound_only` | `service_lane=wecom_media_intake` or holding ack (no claim row) | 待确认 / 技术收件 |
| 3 | `pending_lane_switch_confirm` | `lane_switch_pending` on active Add Car; `claim_lane_switch_prompt` outcome | 跨流程确认 |
| 4 | `claim_started` | `service_lane=claim`, Start Card sent, `claim_started` timeline event | 记录已开始 |
| 5 | `claim_recording` | `claim_phase` in progress, timeline append | 记录中 |
| 6 | `broker_review` | Materials sufficient, `ready_for_broker_review` | 待陈总确认 |
| 7 | `broker_done` | `claim_phase=broker_done`, True End Card preview/send | 已交接 |
| 8 | `add_car_started` | `service_lane=add_car`, H5 Start Card or explicit restart | 加车已开始 |
| 9 | `add_car_recording` | Phase2 / progress card / draft merge | 加车收集中 |
| 10 | `add_car_done` (future) | Not fully shipped as terminal ceremony | — |

### State transition diagram (simplified)

```text
idle ──random inbound──► raw_inbound_only / holding
idle ──我要理赔───────► claim_started ──story/photo──► claim_recording
add_car_recording ──我要理赔──► pending_lane_switch_confirm ──confirm──► claim_started
claim_recording ──broker_done──► broker_done (End Card)
broker_done ──新事故──► claim_started (new case)
```

---

## 3. Invariants (A–K)

| ID | Invariant | Status |
|----|-----------|--------|
| A | No Start Card → no formal customer-facing case | **PASS** |
| B | No Start Card → no broker default queue item | **PASS** |
| C | Random photo/text → raw inbound only | **PASS** |
| D | Explicit start without active lane → Start Card + formal case | **PASS** |
| E | Explicit start during another active lane → confirm card first | **PASS** |
| F | Start Card before `claim_timeline` business recording | **PASS** |
| G | End Card only after `broker_done` | **PASS** |
| H | `broker_done` only for formal Claim | **PASS** |
| I | Done cases leave default active queue | **PASS** |
| J | Idempotency: duplicate clicks/messages no duplicate case/timeline/end | **PASS** |
| K | H5 appends to existing task/case; no silent random Claim | **PASS** (local pytest) |

---

## 4. Simulation Matrix

| # | Current State | Input | Expected Output | Expected Case Change | Queue Effect | Risk | Status |
|---|---------------|-------|-----------------|---------------------|--------------|------|--------|
| 1 | Idle | Random photo | Tier C ack, no Start Card | `wecom_media_intake` only | Hidden default | Low | **PASS** |
| 2 | Idle | Random text「看看这个」 | Generic ack / clarify, no claim | None or holding | Hidden | Low | **UNKNOWN** |
| 3 | Idle | Narrative「昨晚 Costco 被追尾了」 | Holding ack, no Start Card | No `claim` row | Hidden | Was High | **PASS** |
| 4 | Idle | Insurance Q「这个要不要报保险？」 | Safe consultation reply | No claim | Hidden | Low | **PASS** |
| 5 | Idle | Explicit「我要理赔」 | Start Card + injury buttons | `claim` created | Visible | — | **PASS** |
| 6 | Idle | Explicit「我要加车」 | Add Car H5 Start / intent route | `add_car` created | Visible | — | **PASS** |
| 7 | Active Claim | Customer photo | Bind to claim, timeline `customer_photo` | Append | Visible | Low | **PASS** |
| 8 | Active Claim | Customer story | C1 / basics_complete | Append timeline | Visible | Low | **PASS** |
| 9 | Active Claim |「我要理赔」again | Append existing, no new case | Same case_id | Visible | Med | **PASS** |
| 10 | Active Claim |「我要加车」 | Add Car route (defer or new lane) | Add Car path | Both lanes possible | Med | **NEEDS TEST** |
| 11 | Active Claim | Injury quick reply | Update injury status | Append | Visible | Low | **PASS** |
| 12 | Active Add Car | Add Car photo | Bind to add_car | Append add_car | Visible | Low | **PASS** |
| 13 | Active Add Car | Random accident narrative | Holding ack, not lane switch | No claim | Add Car visible | Was High | **PASS** |
| 14 | Active Add Car |「我要理赔」 | Lane switch confirm card | No claim until confirm | Add Car visible | Was High | **PASS** |
| 15 | Active Add Car | Confirm「开始事故记录」 | Start Card + new claim | `claim` created | Both (claim new) | Med | **PASS** |
| 16 | Active Add Car | Cancel「继续加车」 | Resume add car copy | No claim | Add Car visible | Low | **PASS** |
| 17 | Active Add Car |「我要理赔」×2 | Lane switch prompt then idempotent confirm | Single claim | — | Med | **PASS** |
| 18 | Raw inbound | `broker_done` attempt | 400 `broker_done_blocked_raw_inbound` | Unchanged | Hidden | High | **PASS** |
| 19 | Raw inbound | Open drawer GET | 200 detail works | Unchanged | Hidden default | Low | **PASS** |
| 20 | Raw inbound | `include_raw_inbound=true` | Visible as Raw Inbound Log | Unchanged | Debug visible | Low | **PASS** |
| 21 | Broker review | `broker_done` first click | `broker_done` phase + End Card preview | Timeline + phase | Leaves queue | High | **PASS** |
| 22 | Broker review | `broker_done` second click | `already_done=true`, no duplicate timeline | Idempotent | Stays hidden | High | **PASS** |
| 23 | Broker done | Customer new photo | Append or holding (no auto End) | No auto close | Hidden | Med | **UNKNOWN** |
| 24 | Broker done | Customer「我要理赔」 | New case or append per identity rules | Depends on「新事故」| — | Med | **PASS** (新事故) |

---

## 5. PASS / FAIL / UNKNOWN Summary

### PASS (21)

Random photo/narrative boundary, explicit start ceremony, raw inbound queue filter, active claim photo bind, lane switch confirm during Add Car, injury holding gate, `broker_done` guards + idempotency, done-case queue exclusion, duplicate start idempotency, End Card broker-only trigger.

### FAIL (0)

No active temporal bugs reproduced in this audit battery.

### UNKNOWN (2)

- **Row 2** —「看看这个」generic idle text: no dedicated scenario; likely routes to generic assistant / holding but untested explicitly.
- **Row 23** — Post-`broker_done` inbound photo: no dedicated test; policy says read-only / append; low pilot risk.

### NEEDS TEST (1)

- **Row 10** — Active Claim +「我要加车」cross-lane interrupt from Claim → Add Car (inverse of shipped Add Car → Claim lane switch).

---

## 6. High-Risk Temporal Bugs — Historical vs Current

| Bug pattern | Historical risk | Current status | Evidence |
|-------------|-----------------|---------------|----------|
| Active Add Car +「我要理赔」→ other question / swallowed | **High** | **Fixed** — `claim_lane_switch_prompt` | `test_p19h21`, `test_p19h3f2_lane_switch_confirm_card`, deploy smoke |
| Start Card before formal case | **High** | **Fixed** — ceremony on explicit start only | `test_p19h3f1`, deploy 3f-1c smoke |
| Random inbound in broker queue | **High** | **Fixed** — `filter_broker_workbench_cases` | `test_p19h3f1c`, deploy smoke |
| End Card auto-triggered | **High** | **Fixed** — only `mark_claim_broker_done` | `claim_end_card.py`, `test_p19h3f2` |
| `broker_done` on raw inbound | **High** | **Fixed** — `ClaimBrokerDoneError` | deploy 3f-2 smoke E |
| Duplicate case / timeline | **Medium** | **Fixed** — msg_id dedup + `claim_started` idempotency | `case_store._claim_timeline_is_duplicate` |
| Cross-lane without confirm | **High** | **Fixed** — confirm card + menu buttons | `test_p19h3f2_lane_switch_confirm_card` |
| Narrative auto-start claim | **High** | **Fixed** — holding ack path | `should_route_claim_holding_ack` |
| State order错乱 (End before broker) | **High** | **Not observed** | Invariant 04 test |

**Highest residual risk:** Inverse lane switch (Claim active → Add Car start) untested; pilot impact low if Chen rarely starts Add Car mid-claim.

---

## 7. Tests Added

**File:** `tests/test_p19h_state_machine_temporal_invariants.py`

| Test | Theme |
|------|-------|
| `test_invariant_01_*` | Random narrative → no formal claim |
| `test_invariant_02_*` | Random photo → hidden from broker queue |
| `test_invariant_03_*` | Explicit start → Start Card before story timeline |
| `test_invariant_04_*` | End Card cannot precede `broker_done` |
| `test_invariant_05_*` | `broker_done` rejects raw inbound |
| `test_invariant_06_*` | `broker_done` idempotent |
| `test_invariant_07_*` | Done claim hidden from queue, GET works |
| `test_invariant_08_*` | Add Car + narrative → holding, not claim |
| `test_invariant_09_*` | Add Car + explicit claim → lane switch prompt |
| `test_invariant_10_*` | Duplicate「我要理赔」→ single claim |
| `test_invariant_11_*` | Lane switch confirm temporal order |
| `test_invariant_12_*` | Start Card ceremony copy |

**Run:** `PYTHONPATH=. python3 -m pytest tests/test_p19h_state_machine_temporal_invariants.py -q` → **12 passed**

**Regression:** `pytest -k claim` and `pytest -k h5` → **all passed**

---

## 8. Main Agent Work in Progress

Main Agent is actively modifying (per `git status`):

- `services/fiqa_api/wecom/intent.py`
- `services/fiqa_api/wecom/slice.py`
- `services/fiqa_api/wecom/reply.py`
- `services/fiqa_api/wecom/claim_basics.py`
- `services/fiqa_api/inbox_triage/case_store.py`
- `services/fiqa_api/wecom/workflow_scenario_simulator.py`
- `tests/test_p19h21_claim_interrupt_lane_switch.py`
- `tests/test_p19h3f2_lane_switch_confirm_card.py` (new)

**Focus:** Add Car active context + explicit Claim start → confirm card polish (menu click path `ingest_claim_lane_switch_confirm`, repeated confirm idempotency).

This audit agent did **not** edit those files.

---

## 9. Recommended Next Fixes

1. **Claim → Add Car lane switch** — Add scenario + test for row 10 (inverse interrupt).
2. **「看看这个」idle text** — One simulator step for generic ambiguous text (row 2).
3. **Post-`broker_done` inbound** — Document expected behavior (append vs new「新事故」) + one test (row 23).
4. **H5 cloud smoke** — Align local mint secret with Cloud Run Secret Manager (env, not workflow).
5. **Browser automation** — Workbench drawer `broker-done` click (human-pending in deploy smokes).

---

## 10. GO / HOLD

| Verdict | Scope |
|---------|-------|
| **GO** | Start Card only intake, lane switch confirm, `broker_done` + True End Card temporal order |
| **GO** | Audit test battery + simulation matrix for pilot demo |
| **HOLD** | H5 cloud token 403 in deploy smoke (env) |
| **HOLD** | Browser drawer visual click (human-pending) |
| **STOP** | No further production edits from audit agent |

---

## Related

- `docs/p19h3f1b_start_card_case_creation_ceremony.md`
- `docs/p19h3f1c_start_card_only_intake_policy.md`
- `docs/p19h3f_case_boundary_start_end_card_trust_contract_recon.md`
- `docs/evidence/p19h_state_machine_temporal_audit_2026_07_10.md`
