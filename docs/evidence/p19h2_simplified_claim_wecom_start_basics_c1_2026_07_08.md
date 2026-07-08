# P19H-2' — Simplified Claim WeCom Start + Basics + C1 Evidence

**Date:** 2026-07-08  
**Branch:** `sprint/p16-trust-layer`  
**Type:** Simplified Claim WeCom — Safety Gate + Phase 1 Accident Basics + C1  
**Verdict:** **LOCAL PASS** · **REGRESSION PASS** · **QA GATE PASS** · **NO DEPLOY**

---

## 1. Goal

Implement simplified Claim WeCom workflow Phase 0–1 on top of P19I workflow kernel:

- Safety Gate + start reply
- Accident basics collection (3 fields)
- C1 stage-complete card
- Next-step hint toward Evidence Pack (no H5 photo flow this sprint)

---

## 2. Source commits

| Sprint | Commit | Artifact |
|--------|--------|----------|
| P19I-2b | `d7f8b0b` | Thin workflow kernel helpers |
| P19I-2c | `85fbd09` | Claim state kernel parity refactor |
| P19H-2 (base) | `935a0f1` | Initial Claim WeCom basics flow |

---

## 3. Changed files

| File | Change |
|------|--------|
| `services/fiqa_api/wecom/claim_basics.py` | P19H-2' kernel integration, injury safety path |
| `services/fiqa_api/wecom/claim_extractors.py` | Extended injury/start markers |
| `services/fiqa_api/wecom/claim_state.py` | `evaluate_claim_simplified_snapshot()`, `get_claim_simplified_current_step()` |
| `services/fiqa_api/wecom/reply.py` | Safety manual reply, C1 copy polish |
| `tests/test_p19h2_simplified_claim_wecom_basics.py` | **NEW** — 15 acceptance tests |
| `docs/evidence/p19h2_simplified_claim_wecom_start_basics_c1_2026_07_08.md` | **NEW** — this doc |

**Not changed:** schema, Cloud SQL, callback URL, H5 Claim photos, Workbench drawer, deploy config.

---

## 4. Simplified Claim model

```text
Step 0 — Safety Gate (injury / manual_handle)
Phase 1 — Accident Basics (this sprint) ✅
Phase 2 — Evidence Pack (next — not implemented)
Phase 3 — Risk Confirmation (later)
→ intake_ready_for_broker (later)
→ Broker Review → broker_done
```

---

## 5. Start trigger behavior

High-confidence phrases route to guided Claim intake:

- 我要理赔 · 我撞车了 · 出事故了 · 发生事故了 · 车祸了 · 事故理赔
- file a claim · I had an accident · accident claim · claim / accident (exact)

Creates `service_lane=claim`, sends safety/start reply — not generic menu.

---

## 6. Claim question behavior

Phrases like「出事故了怎么办」with liability/coverage questions:

- `should_route_claim_question_safe_reply()` → safe non-committal reply
- No guided case creation
- Offers optional资料收集 without promising filing

---

## 7. Safety / start copy

`build_claim_start_card_reply()`:

- 【理赔资料收集】
- 人是否安全
- 事故时间 / 地点 / 简单描述
- 我们先帮您整理资料，陈总会人工确认
- 这不代表已经正式报案

Forbidden phrases guarded via `CLAIM_FORBIDDEN_AUTOMATION_CLAIMS`.

---

## 8. Accident basics extraction

Deterministic `extract_accident_basics_fields()`:

| Field | Signals |
|-------|---------|
| `accident_datetime` | 今天/昨天/上午/下午/点/号/月, yyyy-mm-dd, mm/dd |
| `accident_location` | 在/附近/Blvd/Ave/St/Irvine/Culver/高速/路口 |
| `accident_description` | Meaningful remainder after stripping command phrases |

No LLM. No hallucination.

---

## 9. Partial collection behavior

`build_claim_missing_basics_reply()`:

- Shows ✅ collected + ○ still needed
- No C1 until all 3 basics present
- Disclaimer: 这只是资料收集，不代表已经正式报案

---

## 10. C1 completion behavior

When all 3 basics satisfied:

- Phase → `accident_basics_complete`
- C1 card: 【理赔资料 · 第 1 步完成 ✅】
- Lists time/location/description
- Next step: 准备事故照片 (no H5 link)
- Does NOT mark `intake_ready_for_broker` or broker review

---

## 11. Injury / manual behavior

`message_mentions_injury()` triggers:

- `transition_to_manual_handle()` patch
- `build_claim_safety_manual_reply()` — no normal C1
- Safety flags in kernel snapshot (`injury_yes`)

Markers: 有人受伤, ambulance, hospital, 医院, 紧急, injured, etc.

---

## 12. Kernel usage

| Helper | Purpose |
|--------|---------|
| `evaluate_claim_simplified_snapshot()` | Aggregate kernel view via `CLAIM_SIMPLIFIED_DEFINITION` |
| `get_claim_simplified_current_step()` | Current step after basics (→ `collect_evidence_pack`) |
| `_kernel_basics_missing_keys()` | Missing basics from kernel missing list |
| `_claim_snapshot_from_case_extra()` | Adapter (from P19I-2c) |

Logged in `wecom_claim_basics_ingest_v1` events.

---

## 13. Tests

```bash
PYTHONPATH=. python3 -m pytest tests/test_p19h2_simplified_claim_wecom_basics.py -q
# 15 passed

PYTHONPATH=. python3 -m pytest tests/test_p19h2_claim_wecom_basics.py -q
# 14 passed (legacy P19H-2 suite)
```

---

## 14. Regression

| Suite | Result |
|-------|--------|
| `test_p19i2b_workflow_kernel.py` | PASS |
| `test_p19i2c_claim_state_kernel_parity.py` | PASS |
| `test_p19h1_claim_state_machine_foundation.py` | PASS |
| `test_p19g32_phase2_field_validation.py` | PASS |
| `test_p19e2_add_vehicle_progress_card.py` | PASS |
| `test_wecom_*.py` (5 files) | PASS |

---

## 15. QA gate

```bash
bash scripts/check_chen_kui_demo_environment.sh --cloud-api
```

---

## 16. Constraints honored

| Constraint | Status |
|------------|--------|
| No H5 Claim photos | ✅ |
| No Workbench Claim drawer | ✅ |
| No OCR | ✅ |
| No schema migration | ✅ |
| No deploy | ✅ |
| No orchestration framework | ✅ |
| Add Vehicle flow preserved | ✅ |

---

## 17. Known limitations

- Deterministic extraction only — not LLM
- H5 Claim Evidence Pack not implemented
- Claim Progress Card full flow not implemented
- Workbench Claim drawer not implemented
- `intake_ready_for_broker` not used in phase derivation yet
- Active media/photo behavior uses generic existing media ack

---

## 18. GO/HOLD for next step

**GO** for P19H-3 when approved:

1. H5 Claim Evidence Pack photo flow
2. Risk Confirmation (injury/police buttons)
3. Claim Progress Card
4. Migrate phase naming toward `intake_ready_for_broker`

**HOLD** on deploy, schema migration, OCR, carrier filing.

---

## STOP

| Item | Value |
|------|-------|
| Handler | `services/fiqa_api/wecom/claim_basics.py` |
| Tests | `tests/test_p19h2_simplified_claim_wecom_basics.py` |
| Deploy | **No** |
| Routing | **Changed** (Claim guided basics in slice.py — existing P19H-2 path) |
| Schema | **Unchanged** |
| Framework | **None** |
