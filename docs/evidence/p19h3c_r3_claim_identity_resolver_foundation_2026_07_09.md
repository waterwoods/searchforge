# P19H-3c-R3 — Claim Identity Resolver Foundation

**Date:** 2026-07-09  
**Branch:** `sprint/p16-trust-layer`  
**Status:** GO (local + tests; **no deploy**)

---

## 1. Goal

Add a lightweight Claim identity resolution gate before WeCom text basics append/create, so the same accident is not silently merged into the wrong case when multiple open claims exist or when an old open claim is ambiguous.

---

## 2. Why this matters

P19H-3c-3C closed the Claim Evidence Pack loop (H5 upload/skip → Cloud SQL → Workbench checklist). The next risk before WeCom image binding (P19H-3d) is **duplicate / false-merge**: same `wecom_external_userid` with 2+ open claim cases previously used **newest-wins** in `find_active_claim_case_for_basics()`.

False merge is worse than duplicate case — this sprint replaces silent newest-wins with explicit tier A/B/C decisions.

---

## 3. New resolver function

**File:** `services/fiqa_api/wecom/claim_identity.py`

Pure helpers:

- `ClaimIdentityCandidate` — case snapshot for matching
- `ClaimIdentityDecision` — tier, action, score, rule_ids, reasons
- `resolve_claim_identity()` — main entry
- `is_explicit_new_accident()` — customer restart markers
- `is_open_claim_candidate_for_basics()` — excludes closed / broker_done

---

## 4. Rules implemented

| Rule | Condition | Tier | Action | Reason |
|------|-----------|------|--------|--------|
| A1 | Explicit new accident markers (`新事故`, `另一次事故`, `重新理赔`, `新的事故`, `new accident`, `another accident`) | C | `create_new` | `customer_said_new_accident` |
| A2 | No open claim for user | C | `create_new` | `no_open_claim` |
| A3 | Exactly one open claim updated/created within 72h | A | `append_existing` | `single_recent_open_claim` (score ≥ 90) |
| A4 | Exactly one open claim older than 72h | B | `broker_confirm` | `old_open_claim_requires_confirmation` (score 75) |
| A5 | 2+ open claims | B | `broker_confirm` | `multiple_open_claims` (score 50) |
| A6 | H5 signed `case_id` | — | Out of scope | Documented as tier A; H5 path unchanged |

**Injury override:** single open claim + injury mention still appends (safety escalation) even if age would otherwise be B.

---

## 5. What changed vs newest-wins

| Before | After |
|--------|-------|
| `find_active_claim_case_for_basics()` returned newest open claim silently | `list_open_claim_candidates_for_basics()` lists all; ingestion uses `resolve_claim_identity()` |
| 2 open claims → newest absorbed new text | 2 open claims → `broker_confirm`; no silent append |
| Old open claim → auto-append | Old open claim → customer asked same vs new accident |

`find_active_claim_case_for_basics()` retained for routing **checks only** (boolean “has open claim”), not for ingestion append.

---

## 6. Broker-confirm / ambiguous behavior

When tier B / `broker_confirm`:

- **No silent append** to newest case
- WeCom reply (`build_claim_identity_broker_confirm_reply()`):

  > 我看到您这边可能已经有一个未完成的理赔记录。  
  > 为了避免把两次事故资料混在一起，请回复：  
  > 1 同一个事故，继续补资料  
  > 2 新的事故，重新开始  
  > 或直接联系陈总。

- Outcome: `claim_identity_broker_confirm`
- `needs_broker_manual_handle: true`
- **No full customer confirmation state machine** in this sprint — follow-up reply parsing deferred

---

## 7. Routing log fields

Extended `wecom_routing_decision_v1` where Claim basics resolves identity:

```json
{
  "identity_tier": "A|B|C",
  "identity_action": "append_existing|create_new|broker_confirm",
  "identity_score": 90,
  "identity_rule_ids": ["ID-A3"],
  "identity_reasons": ["single_recent_open_claim"],
  "identity_case_id": "case_..."
}
```

No raw PII logged. Helper: `identity_context_for_decision()`.

New routing constants: `PRIORITY_CLAIM_IDENTITY_BROKER_CONFIRM`, `DECISION_CLAIM_IDENTITY_BROKER_CONFIRM`, `RESPONSE_CLAIM_IDENTITY_BROKER_CONFIRM`.

---

## 8. Tests

**File:** `tests/test_p19h3c_r3_claim_identity_resolver_foundation.py`

| Test | Coverage |
|------|----------|
| 7.1 | No open claim → `create_new` |
| 7.2 | One recent open claim → `append_existing` |
| 7.3 | Explicit new accident → `create_new` |
| 7.4 | Multiple open claims → `broker_confirm` |
| 7.5 | Old open claim → `broker_confirm` |
| 7.6 | Closed / broker_done excluded |
| 7.7 | Claim basics path — no silent newest-wins with 2 cases |
| 7.8 | Routing log identity fields emitted |
| 7.9 | Single recent claim append integration |

---

## 9. Regressions

| Suite | Result |
|-------|--------|
| `test_p19h3c_r3_claim_identity_resolver_foundation.py` | PASS (9) |
| `test_p19h2_simplified_claim_wecom_basics.py` | PASS |
| `test_p19h21_claim_interrupt_lane_switch.py` | PASS |
| `test_p19j1a_routing_decision_log.py` | PASS |
| `test_p19j1c_workflow_scenario_simulator.py` | PASS |
| `test_p19h3c3c_h5_claim_slot_persistence.py` | PASS |
| `pytest -k h5` | PASS |
| `pytest -k claim` | 1 pre-existing failure in `test_p19h2_claim_wecom_basics.py::test_full_basics_message_sends_c1` (outdated reply copy assertion `下一步`; C1 outcome still passes) |

---

## 10. QA gate

```bash
bash scripts/check_chen_kui_demo_environment.sh --cloud-api
```

**Result:** PASS — QA UI + Cloud Run API + Cloud SQL aligned (no deploy performed).

---

## 11. Constraints honored

| Constraint | Status |
|------------|--------|
| No deploy | ✅ |
| No schema change | ✅ |
| No new DB table | ✅ |
| No Workbench duplicate banner UI | ✅ |
| No WeCom image binding | ✅ |
| No merge UI | ✅ |
| No ML / vector / OCR | ✅ |

---

## 12. Known limitations

- No Workbench duplicate suggestion banner yet
- No full merge/split UI
- No WeCom direct image binding (P19H-3d)
- Broker-confirm follow-up (reply `1` / `2`) not parsed — customer must use explicit `新事故` or contact Chen
- Medium confidence uses customer-safe reply, not full broker Workbench UX

---

## 13. Next recommended prompt

1. **Deploy + WeCom claim identity smoke** — verify `broker_confirm` reply and routing log fields on Cloud Run
2. **P19H-3d WeCom Direct Image Binding** — wire `resolve_claim_identity()` into media intake path

---

## 14. GO / HOLD

**GO** — foundation complete; safe to deploy identity resolver in a follow-up sprint.

**STOP** — no deploy in this sprint.
