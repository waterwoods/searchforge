# P19H-3f-2 — Live WeCom Add Car → Claim Checkpoint + Confirm Fix

**Date:** 2026-07-10  
**Branch:** `sprint/p16-trust-layer`  
**Type:** Live-path bug fix — no schema migration

---

## 1. Symptom (real phone WeCom)

User in active **Add Car** flow sent:

- `我要理赔`
- `我要进行理赔`

System replied:

> Got it — I noted your other question. Let's finish your current request first…  
> 收到，我已记录您的其他问题。我们先完成当前请求，陈总会人工跟进其他事项。

Expected: **Lane Switch Confirm Card** (checkpoint → confirm → Claim Start Card), not secondary-topic deferral.

---

## 2. Root cause

| Step | What happened |
|------|----------------|
| 1 | Active Add Car case exists for `external_userid` |
| 2 | `classify_wecom_intent` → `claim_intake` / high |
| 3 | **Live callback** enters `process_kf_msg_or_event` → `slice.py` |
| 4 | Claim lane-switch routing was gated behind `WECOM_B0_ACTIVE_WORKSPACE` (`b0_enabled`) |
| 5 | `minimal_lane_trigger` runs **without** that gate for high-confidence `claim_intake` |
| 6 | `ingest_wecom_text_to_minimal_lane` → `secondary_topic_deferred` (active add_car guard) |
| 7 | `build_secondary_topic_deferred_reply()` → “先完成当前请求…” |

**Secondary issue:** prior smoke/tests called `ingest_claim_basics_message()` directly (simulator/helper path), which correctly emitted `claim_lane_switch_prompt`. Production uses `process_kf_msg_or_event` → minimal_lane defer fired first when claim routing was b0-gated.

**Deployed revision at investigation:** `d2e5a10` (lane-switch slice wiring not yet live).

---

## 3. Why previous fix/smoke missed live path

| Gap | Detail |
|-----|--------|
| Simulator vs live | `workflow_scenario_simulator` and `ingest_claim_basics_message` tests bypass `slice.py` minimal_lane branch |
| Deploy smoke | `p19h3f2_deploy_lane_switch_smoke.py` used `ingest_claim_basics_message`, not `process_kf_msg_or_event` |
| B0 gate | Claim interrupt block required `b0_enabled`; minimal_lane defer did not |
| Phrase coverage | `我要进行理赔` relied on substring `进行理赔`; now explicit in markers |

---

## 4. Product rule

```text
Current lane → checkpoint → confirm card → switch → Start Card
```

1. Active Add Car + explicit Claim start → **no immediate Claim**
2. Save checkpoint on Add Car case (`lane_switch_pending`)
3. Send Lane Switch Confirm Card
4. User confirms `开始事故记录` → create Claim + Start Card
5. User cancels `继续加车` → resume Add Car, materials retained
6. Random narrative / insurance Q / photo → **no** confirm card, **no** Claim

---

## 5. Checkpoint behavior

Stored on existing Add Car case JSON (`lane_switch_pending`, no schema migration):

```json
{
  "from_lane": "add_car",
  "to_lane": "claim",
  "state": "pending_confirm",
  "pending_lane_switch": "add_car_to_claim",
  "source_case_id": "<add_car_case_id>",
  "trigger_text": "我要理赔",
  "created_at": "<iso>",
  "status_before": "<guided_workflow_state>",
  "received_material_summary": {
    "photo_received": true,
    "text_received": true
  }
}
```

Repeated explicit Claim while `pending_confirm` → resend confirm card, no duplicate checkpoint / no Claim.

---

## 6. Confirm card copy

```text
您现在是想开始一份新的事故/理赔记录吗？

我会先暂停当前加车资料收集，并保留已收到的加车资料。
如果您确认，我会开始事故记录。

这不代表已经向保险公司正式报案。

您也可以回复「开始事故记录」或「继续加车」。

[开始事故记录]  [继续加车]
```

---

## 7. Fix summary

| Area | Change |
|------|--------|
| `slice.py` | `claim_slice_routing = b0_enabled OR should_route_claim_interrupt_during_add_car()` — claim interrupt wins over minimal_lane defer |
| `slice.py` | Safety net before `ingest_wecom_text_to_minimal_lane` for active Add Car claim interrupt |
| `claim_basics.py` | `should_route_claim_interrupt_during_add_car()` helper |
| `claim_basics.py` | Explicit phrases: `我要进行理赔`, `我现在要理赔` |
| `claim_basics.py` | Rich checkpoint + idempotent pending resend |
| `reply.py` | Updated confirm / cancel copy |
| `tests/test_p19h3f2_live_add_car_claim_lane_switch.py` | **Live callback-equivalent** via `process_kf_msg_or_event` (B0 on + B0 off) |

---

## 8. Tests

```bash
PYTHONPATH=. python3 -m pytest tests/test_p19h3f2_live_add_car_claim_lane_switch.py -q
PYTHONPATH=. python3 -m pytest tests/test_p19h3f2_lane_switch_confirm_card.py -q
PYTHONPATH=. python3 -m pytest tests/test_p19h_state_machine_temporal_invariants.py -q
PYTHONPATH=. python3 -m pytest tests -q -k "claim"
PYTHONPATH=. python3 -m pytest tests -q -k "h5"
```

All passed locally before deploy.

---

## 9. Constraints

- No schema migration / no new DB tables
- No random auto Claim / no OCR / ASR / damage AI
- No fault / coverage / carrier filing / LLM brief
- Start Card only policy preserved
- `broker_done` / True End Card preserved

---

## 10. Known limitations

- Inverse lane switch (active Claim → Add Car) still untested
- Deploy smoke script still uses direct `ingest_claim_basics_message` for some scenarios (live slice covered by pytest)
- H5 cloud token alignment remains env-dependent

---

## 11. Next recommended prompt

- Pilot Demo Script / Chen readiness
- Inverse Claim → Add Car lane switch (confirm card symmetry)
