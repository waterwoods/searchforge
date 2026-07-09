# Live WeCom Add Car Claim Intent — Old Defer Root Cause

**Date:** 2026-07-10  
**Branch:** `sprint/p16-trust-layer`

---

## 1. Symptom (real phone)

Add Car 进行中发送 `我要理赔` / `我要进行理赔` 仍收到：

> Got it — I noted your other question. Let's finish your current request first…  
> 收到，我已记录您的其他问题。我们先完成当前请求，陈总会人工跟进其他事项。

---

## 2. Deployed revision at investigation

| Item | Value |
|------|-------|
| Revision | `fiqa-api-00186-m4w` |
| GIT_SHA | `46c170a3a` |
| Traffic | 100% to latest revision |
| Callback URL | `https://fiqa-api-g7zatxrycq-uw.a.run.app` |

**Real callback DID hit expected revision** — logs confirm `fiqa-api-00186-m4w`.

---

## 3. Cloud Run log evidence (2026-07-09T19:49–19:50Z)

| Field | Value |
|-------|-------|
| `external_userid` | `wmtLevSgAA25eirbmJC3r-nfQBCrmxcw` |
| `text` | `我要理赔` / `我要进行理赔` |
| `revision_name` | `fiqa-api-00186-m4w` |
| `incoming_intent` | `claim_intake` |
| `active_case_id` | `case_b097587cab58` |
| `active_workflow` | `add_vehicle` |
| `active_phase` | `phase_3_broker_review` |
| `active_state` | `ready_for_broker_review` |
| Branch | `wecom_minimal_lane_deferred_v1` → `secondary_topic_deferred` |
| Reply source | `build_secondary_topic_deferred_reply()` in `reply.py` |

Log sequence:

1. `wecom_event_normalized_v1` — text `我要理赔`
2. `wecom_minimal_lane_deferred_v1` — `active_add_car_flow`
3. `wecom_routing_decision_v1` — `defer_secondary_topic` / `secondary_topic_deferred`
4. `wecom_slice_reply_generated_v1` — old defer copy

**Missing logs:** `add_car_claim_lane_switch_v1`, `claim_basics_live_interrupt_v1`, `claim_lane_switch_prompt`

---

## 4. Root cause

`should_route_claim_interrupt_during_add_car()` delegated to `should_route_claim_guided_workflow()`, which returns **False** when the user has an open Claim whose `derive_claim_phase()` is **not** in early intake phases (`claim_started`, `accident_basics_in_progress`, `accident_basics_complete`).

Production user had (or could have) an open Claim in `broker_review` / later phase while Add Car case `case_b097587cab58` remained open in `phase_3_broker_review`.

Result:

- `claim_slice_routing` claim handlers skipped
- `minimal_lane_trigger` fired (`claim_intake` high confidence)
- Safety net `should_route_claim_interrupt_during_add_car` → **False**
- `build_secondary_topic_deferred_reply()` emitted old copy

**Exact old reply source:** `services/fiqa_api/wecom/reply.py` → `build_secondary_topic_deferred_reply()`, called from `slice.py` minimal_lane `secondary_topic_deferred` branch.

---

## 5. Why prior smoke missed it

| Gap | Detail |
|-----|--------|
| Smoke cases | Fresh test users with only Add Car — no coexisting open Claim |
| Production user | Real `case_b097587cab58` in `phase_3_broker_review`; may also have open Claim |
| Test path | `ingest_claim_basics_message` direct calls bypass `should_route_claim_guided_workflow` gate |
| Prior fix | `should_route_claim_interrupt` still depended on `should_route_claim_guided_workflow` |

---

## 6. Fix

1. **`should_route_add_car_to_claim_lane_switch()`** — explicit Add Car + Claim start intent; **independent of open Claim phase**
2. **`should_route_claim_interrupt_during_add_car()`** — calls new helper first
3. **`slice.py`** — early intercept via `should_route_add_car_to_claim_lane_switch()` **before** `minimal_lane_trigger`
4. **Logging** — `add_car_claim_lane_switch_v1`, `secondary_topic_defer_blocked_check_v1`
5. **Tests** — production shape: add_car `phase_3_broker_review` + open Claim + `process_kf_msg_or_event`

---

## 7. Tests

```bash
PYTHONPATH=. python3 -m pytest tests/test_p19h3f2_live_add_car_claim_lane_switch.py -q
```

Includes:

- B0 on/off live slice
- add_car broker_review + open claim repro
- true other question still defers

---

## 8. Constraints

- No schema migration
- No random auto Claim
- Start Card only preserved
- Old defer preserved for genuine other questions (e.g. 续保)

---

## 9. Verdict

**GO** after redeploy + phone retest

---

## 10. Deploy (post-fix)

*(Updated after redeploy)*
