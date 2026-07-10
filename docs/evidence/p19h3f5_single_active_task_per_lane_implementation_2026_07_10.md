# P19H-3f-5 — Single Active Task per Lane Implementation Evidence

**Date:** 2026-07-10  
**Sprint:** P19H-3f-5  
**Branch:** `sprint/p16-trust-layer`

---

## 1. Goal

Replace multi-open Claim customer picker / blanket Collision Resolver with **Single Active Task per Lane**:

- One implicit active task per lane (newest open case)
- Ordinary supplements default **append** to active task
- Strong new-accident / cross-lane signals → **Confirm Card** only
- Multiple open cases → broker-side `possible_multi_claim_context` flag

---

## 2. Product policy

| Principle | Customer | Broker |
|-----------|----------|--------|
| Single active Claim | Keeps sending photos/text; system appends | Sees risk flag when multiple open |
| Strong signal | Confirm: continue / new / contact | Can merge/close duplicates |
| No picker | Never asked “which case #?” | Workbench warning + timeline note |

---

## 3. What changed

- `resolve_claim_identity`: removed ID-A5 blanket `broker_confirm` on ordinary multi-open traffic; added ID-A8 `active_append_newest`
- Explicit new accident with open Claim → Confirm Card (not silent `create_new`)
- Collision Resolver copy unified to **【请确认】** with 3 choices (multi-open dead-end removed)
- Collision choice 1/2 work with multiple open Claims (append newest / create new)
- Status Card footnote when multiple open Claims
- `add_case_risk_flag()` helper; wired on multi-open text/media append
- Workbench brief highlights multi-open warning
- Narrowed `is_collision_triggering_input` (no bare `has_accident_basics_signals` false positives)

---

## 4. What did not change

- No schema / DB table changes
- Start Card / Holding ack / raw inbound hidden policy
- broker_done End Card
- Add Car → Claim lane-switch Confirm
- No Multi-Open Picker
- No OCR / ASR / damage AI / carrier filing

---

## 5. Claim lane behavior

| Scenario | Result |
|----------|--------|
| Single open + ordinary supplement | Append, no Confirm |
| Single/multi open + strong new accident | Confirm Card |
| Multi open + ordinary supplement | Append newest + `possible_multi_claim_context` |
| Multi open + status request | Status Card newest + gentle footnote |
| Post-basics accident narrative | Confirm (unchanged safety) |

---

## 6. Add Car lane behavior

- Existing draft discovery unchanged
- Restart markers recognized (`再加一辆车`, etc.) — full Add Car Confirm Card deferred
- Lane-switch Add Car → Claim preserved

---

## 7. Media behavior

- Multiple open Claims + ordinary photo → bind newest active Claim + risk flag
- No open Claim + photo → raw/unassigned (no formal Claim)

---

## 8. Risk flag behavior

- Flag: `possible_multi_claim_context`
- Workbench tag + activity note on case
- Brief highlight: “该客户有多份未完成事故记录…”

---

## 9. Tests result

```
PYTHONPATH=. python3 -m pytest tests/test_p19h3f5_single_active_task_per_lane.py -q  → PASS (20)
PYTHONPATH=. python3 -m pytest tests/test_p19h3f4_unified_status_card.py -q          → PASS
PYTHONPATH=. python3 -m pytest tests/test_p19h3f3_claim_collision_resolver.py -q     → PASS
PYTHONPATH=. python3 -m pytest tests/test_p19h3f2_true_end_card_on_broker_done.py -q → PASS
PYTHONPATH=. python3 -m pytest tests/test_p19h3f1_case_boundary_policy.py -q         → PASS
PYTHONPATH=. python3 -m pytest tests/test_p19h3f1c_start_card_only_intake_policy.py -q → PASS
PYTHONPATH=. python3 -m pytest tests -q -k "claim"                                   → PASS
PYTHONPATH=. python3 -m pytest tests -q -k "h5"                                      → PASS
```

---

## 10. Simulation result

- Script: `scripts/p19h3f5_single_active_task_simulation.py`
- Evidence: `docs/evidence/p19h3f5_single_active_task_simulation_2026_07_10.json`
- Verdict: **PASS** (scenarios A–J)

---

## 11. Deployment result

| Field | Value |
|-------|-------|
| Deployed revision | `fiqa-api-00191-xx7` |
| GIT_SHA | `7ec685527` |
| Implementation commit | `7ec6855` |
| Service URL | `https://fiqa-api-g7zatxrycq-uw.a.run.app` |
| `/health/live` | 200 OK |
| `/readyz` | 200 OK (`intake_core_readiness: true`) |
| Frontend deployed | **No** (no UI files changed) |

### Cloud smoke (`scripts/p19h3f5_deploy_single_active_task_smoke.py`)

| Check | Result |
|-------|--------|
| Start Card framed | PASS |
| Status Card | PASS |
| Multi-open ordinary append (no picker) | PASS |
| Multi-open「新的事故」→ Confirm | PASS |
| Confirm 2 → new Claim + Start Card | PASS |
| Random photo before start hidden | PASS |
| Add Car → Claim lane-switch | PASS |
| Broker Done End Card preview | PASS |
| **Overall** | **PASS** |

### QA gate (`check_chen_kui_demo_environment.sh --cloud-api`)

- API health / readyz: **PASS**
- Core P19H-3f-5 smoke: **PASS**
- Known seed drift (demo names / field tags): **FAIL** — pre-existing; does not block this sprint's routing policy

### Logs

- Deploy smoke + ingest paths: **no claim-route 500s observed**
- Live WeChat validation: **pending** (Andy)

---

*STOP — evidence post-deploy*

- Add Car “another vehicle” Confirm Card not fully implemented (restart markers only)
- Broker merge/move UI deferred
- Real WeChat validation required post-deploy

---

## 13. Rollback plan

```bash
gcloud run services update-traffic fiqa-api \
  --region=us-west1 \
  --project=optimal-disk-472305-e2 \
  --to-revisions=<prior-revision>=100
```

Prior known-good: `fiqa-api-00190-989` @ `a425fa461`

---

## 14. Next recommendation

**Final Chen Demo Run** — live WeChat walkthrough with Chen Kui after cloud smoke PASS.

---

*STOP — evidence pre-deploy baseline*
