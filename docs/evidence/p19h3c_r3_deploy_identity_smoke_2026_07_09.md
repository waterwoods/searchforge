# P19H-3c-R3 — Deploy + Identity Smoke

**Date:** 2026-07-09  
**Branch:** `sprint/p16-trust-layer`  
**Verdict:** **GO**

---

## 1. Goal

Deploy Claim Identity Resolver Foundation (`a9b1567`), fix outdated C1 copy regression test, run full Claim/H5/identity regressions, and validate append/create/broker-confirm behavior on QA Cloud SQL + Cloud Run health.

---

## 2. Deployed commit

| Field | Value |
|-------|-------|
| Commit | `a9b1567` — feat: add Claim identity resolver foundation |
| Pre-deploy HEAD | `a9b1567` (already pushed) |

---

## 3. Backend revision / GIT_SHA

| Field | Value |
|-------|-------|
| Revision | **`fiqa-api-00176-njk`** |
| URL | `https://fiqa-api-g7zatxrycq-uw.a.run.app` |
| GIT_SHA | **`a9b156719`** (`GET /version`) |
| Script | `bash scripts/deploy_paid_pilot.sh` |
| Prior revision | `fiqa-api-00175-4p6` |

---

## 4. Health / ready

| Endpoint | Result |
|----------|--------|
| `GET /health/live` | **200** |
| `GET /readyz` | **200** |
| `GET /version` | `{"commit":"a9b156719",...}` |

---

## 5. Test fix summary

**File:** `tests/test_p19h2_claim_wecom_basics.py`

| Issue | Fix |
|-------|-----|
| `test_full_basics_message_sends_c1` asserted outdated `下一步` copy | Assert `上传事故照片` + `事故基本信息已收到` (P19H-3c-2 H5 button flow) |
| `_assert_no_forbidden_copy` false-positive on negated disclaimer | Scrub `不代表 claim 已正式提交` before forbidden-phrase scan (aligned with `test_p19h2_simplified_claim_wecom_basics.py`) |

Production copy unchanged.

---

## 6. Full regression results

| Suite | Result |
|-------|--------|
| `test_p19h3c_r3_claim_identity_resolver_foundation.py` | **PASS** (9/9) |
| `test_p19h2_claim_wecom_basics.py` | **PASS** (14/14) |
| `test_p19h21_claim_interrupt_lane_switch.py` | **PASS** |
| `test_p19j1a_routing_decision_log.py` | **PASS** |
| `test_p19j1c_workflow_scenario_simulator.py` | **PASS** |
| `test_p19h3c3c_h5_claim_slot_persistence.py` | **PASS** (8/8) |
| `test_p19h3c3a_claim_evidence_summary_backend.py` | **PASS** |
| `test_p19h3c3ab_get_case_enrichment_parity.py` | **PASS** |
| `pytest -k claim` | **PASS** (185) |
| `pytest -k h5` | **PASS** (86) |

---

## 7. QA gate

| When | Command | Result |
|------|---------|--------|
| Pre-deploy | `bash scripts/check_chen_kui_demo_environment.sh --cloud-api` | **PASS** (rev `00175-4p6`) |
| Post-deploy | same | **PASS** (rev `00176-njk`) |

---

## 8. Identity smoke A/B/C/D

**Method:** QA Cloud SQL ingest path — same `ingest_claim_basics_message()` + `resolve_claim_identity()` code as deployed revision. Ephemeral `workbench_test` cases; unique `external_userid` prefix `wm_p19h3c_r3_smoke_*`. Cloud Run API readback for append case.

**Smoke suffix:** `545146` · **ext tail:** `…545146`

### Smoke A — no open claim / explicit claim start

| Check | Result |
|-------|--------|
| Input | `我要理赔` |
| Outcome | `claim_start_card_sent` |
| Case created | **Yes** — `case_a4de36a24881` |
| Start card copy | **Yes** (`【理赔资料收集】`) |
| Identity | `create_new` / `no_open_claim` (implicit on first create) |

### Smoke B — one recent open claim → append

| Check | Result |
|-------|--------|
| Input | `今天上午10点，在 Irvine Blvd 和 Culver 附近，对方变道刮到我左前门` |
| Outcome | `claim_c1_sent` |
| Same case as A | **Yes** — `case_a4de36a24881` |
| C1 copy | **Yes** (`第 1 步完成`) |
| `identity_tier` | **A** |
| `identity_action` | **append_existing** |
| `identity_score` | **90** |
| `identity_reasons` | **single_recent_open_claim** |
| Cloud API readback | `service_lane=claim`, accident basics present, `workbench_test=true` |

### Smoke C — explicit new accident

| Check | Result |
|-------|--------|
| Input | `这是新的事故，我要理赔` |
| Outcome | `claim_start_card_sent` |
| New case (not A) | **Yes** — `case_d5d2313f2106` |
| `identity_action` | **create_new** |
| `identity_reasons` | **customer_said_new_accident** |
| Safe reply | **Yes** — no filed/fault/coverage language |

### Smoke D — multiple open claims → broker_confirm

| Check | Result |
|-------|--------|
| Setup | 2 open claim cases, same `external_userid` tail `…i_545146` |
| Input | `我要理赔` |
| Outcome | `claim_identity_broker_confirm` |
| Silent newest-wins | **No** — `case_created=false` |
| `identity_action` | **broker_confirm** |
| `identity_reasons` | **multiple_open_claims** |
| Broker-confirm copy | **Yes** — `未完成的理赔记录` + `同一个事故` + `新的事故` |

**Note:** Smoke D safe to simulate on QA Cloud SQL (workbench_test only). Not sent via live WeCom callback.

---

## 9. Routing log identity fields

### Local / QA ingest capture (deployed code path)

Sample `wecom_routing_decision_v1` from append path (Smoke B):

```json
{
  "identity_tier": "A",
  "identity_action": "append_existing",
  "identity_score": 90,
  "identity_rule_ids": ["ID-A3"],
  "identity_reasons": ["single_recent_open_claim"],
  "identity_case_id": "case_93c38ad2b718",
  "decision": "send_claim_c1",
  "response_type": "claim_c1"
}
```

Fields present: **identity_tier**, **identity_action**, **identity_score**, **identity_reasons**, **identity_case_id** — **YES**

### Cloud Run Logging (`fiqa-api-00176-njk`)

| Check | Result |
|-------|--------|
| `identity_action` on new revision | **PROD-PENDING** — no live WeCom Claim traffic on `00176-njk` yet |
| Pre-deploy routing logs | Lack identity fields (expected — resolver not deployed) |
| `claim_identity` errors | **None** |
| Import / traceback on claim path | **None** |

Live WeCom phone smoke on new revision deferred; QA Cloud SQL + unit test `test_08_routing_log_includes_identity_fields` confirm field emission.

---

## 10. Log check result

Scanned Cloud Run logs post-deploy (`fiqa-api-00176-njk`, limit 250):

| Finding | Result |
|---------|--------|
| `claim_identity` errors | **None** |
| Workbench 500s | **None** |
| H5 / claim regressions in logs | **None** |
| Qdrant embedding warmup gRPC errors | Expected optional warnings (intake-only deploy) |
| Import errors | **None** on claim path |

---

## 11. Constraints

| Constraint | Status |
|------------|--------|
| No schema change | ✅ |
| No WeCom image binding | ✅ |
| No merge UI | ✅ |
| No phone summary | ✅ |
| No OCR/ASR/ML | ✅ |

---

## 12. Known limitations

- No full broker duplicate banner in Workbench
- No follow-up `1` / `2` broker-confirm state machine yet
- No WeCom direct image binding yet
- Cloud Run routing logs with identity fields await next live WeCom Claim message on `00176-njk`

---

## 13. Next recommended sprint

1. **P19H-3d WeCom Direct Image Binding** — wire `resolve_claim_identity()` into media intake
2. **P19H-3c-R3b Broker Confirm UX** — if `broker_confirm` reply parsing feels too rough in live WeCom

---

## 14. GO / HOLD

**GO** — Deploy successful, regressions pass, QA gate PASS, identity smoke A/B/C/D PASS on QA Cloud SQL, routing identity fields confirmed on deployed code path.

**STOP**
