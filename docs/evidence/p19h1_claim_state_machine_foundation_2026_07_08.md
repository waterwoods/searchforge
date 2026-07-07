# P19H-1 — Claim State Machine Foundation Evidence

**Date:** 2026-07-08  
**Branch:** `sprint/p16-trust-layer`  
**Type:** Claim state machine foundation — local unit tests + QA gate  
**Verdict:** **LOCAL PASS** · **REGRESSION PASS** · **QA GATE PASS** · **NO DEPLOY**

---

## 1. Goal

Implement Claim lane **foundation only** per P19H-0 recon: phase model, required/optional fields, slot model, completion predicates, transition suggestion helper, validation/guardrail constants, and unit tests. No WeCom Claim flow, H5, Workbench drawer, OCR, schema migration, or deploy.

---

## 2. P19H-0 source

| Item | Value |
|------|-------|
| Doc | `docs/p19h0_claim_case_builder_state_machine_recon.md` |
| Commit | `21e9573` |

---

## 3. Changed files

| File | Change |
|------|--------|
| `services/fiqa_api/wecom/claim_state.py` | **NEW/UPDATED** — pure claim state foundation |
| `tests/test_p19h1_claim_state_machine_foundation.py` | **NEW/UPDATED** — 25 acceptance tests |
| `docs/evidence/p19h1_claim_state_machine_foundation_2026_07_08.md` | **NEW** — this doc |

---

## 4. Claim phase list

`claim_started` · `accident_basics_in_progress` · `accident_basics_complete` · `photos_in_progress` · `photos_complete` · `other_party_in_progress` · `other_party_complete` · `injury_police_in_progress` · `injury_police_complete` · `claim_summary_ready` · `broker_review` · `broker_needs_more_info` · `broker_done` · `manual_handle`

**Invariants:**

- `claim_summary_ready` ≠ claim filed
- `broker_review` ≠ claim filed
- `broker_done` = broker handoff only (≠ carrier submitted)
- `manual_handle` = urgent/sensitive broker path

---

## 5. Required fields (8)

| Field | Rule |
|-------|------|
| `accident_datetime` | `collected_fields` + non-empty `known_facts` |
| `accident_location` | Same |
| `accident_description` | Same (≤500 chars) |
| `customer_damage_photo` | Slot `received` |
| `other_party_vehicle_or_plate` | `other_party_vehicle_photo` **or** `other_party_plate` text |
| `other_party_info` | ≥1 of: insurance card, license, vehicle photo, plate, phone, name |
| `anyone_injured` | Explicit yes/no |
| `police_involved` | Explicit yes/no |

---

## 6. Optional fields (5)

`scene_photo` · `police_report_photo` · `tow_repair_info` · `witness_info` · `existing_claim_number`

Optional gaps do **not** block `claim_summary_ready`.

---

## 7. Slot model

| Slot | Required in photo phase |
|------|-------------------------|
| `customer_damage_photo` | Yes |
| `other_party_vehicle_photo` | Yes (or plate text fallback) |
| `scene_photo` | Optional |
| `other_party_insurance_card` | Conditional (other-party phase) |
| `other_party_license` | Conditional |
| `police_report_photo` | Optional |

**Statuses:** `empty` · `received` · `skipped` · `needs_retake`

Sources: `case_attachments[].slot_assignment` + optional `claim_attachment_slots` overrides.

---

## 8. Completion predicates

| Helper | True when |
|--------|-----------|
| `is_accident_basics_complete` | 3 basics text fields satisfied |
| `are_claim_photos_complete` | damage photo + (vehicle photo or plate text) |
| `is_other_party_info_complete` | ≥1 other-party artifact (partial OK) |
| `is_injury_police_complete` | both injury + police yes/no set |
| `is_claim_summary_ready` | all 8 required predicates true |

Also: `derive_claim_phase`, `get_claim_collected_fields`, `get_claim_attachment_slots`, `get_claim_missing_items`, `get_claim_progress_snapshot`.

---

## 9. Transition helper

`suggest_next_claim_transition(case_extra, event_type=None)` returns:

```python
{
  "current_phase": "...",
  "next_phase": "...",
  "ready_for_broker_review": bool,
  "needs_broker_manual_handle": bool,
  "missing_items": [...],
  "customer_next_action": "collect_accident_basics | collect_claim_photos | ...",
  "broker_note": "injury_yes_phone_first" | None,
}
```

Does **not** send WeCom replies — routing layers consume this in P19H-2+.

---

## 10. Injury / manual_handle behavior

- `anyone_injured = yes` → `needs_broker_manual_handle=True` in snapshot + transition
- `broker_note = injury_yes_phone_first`
- Does **not** auto-set `broker_done`
- `transition_to_manual_handle()` patch sets `urgent=True`, `manual_handle=True`, `ready_for_broker_review`

---

## 11. Safety guardrails

**Forbidden automation claims** (`CLAIM_FORBIDDEN_AUTOMATION_CLAIMS`):

- 已经帮您报案 · 理赔已经提交 · 是对方责任 · 您的保险一定会赔 · 我们已经联系保险公司 · 不用担心，肯定没问题 · …

**Safe copy invariants** (`CLAIM_SAFE_COPY_INVARIANTS`):

- 我们先帮您收集资料 · 陈总会人工查看 · 这不代表已正式报案 · 我们不能判断责任 · …

Helpers: `normalize_claim_yes_no`, `is_valid_claim_required_text`, `validate_accident_description`, `customer_copy_contains_forbidden_phrase`.

Module docstring notes: production routing must use Postgres read facade (`get_case_for_read`); legacy JSON-only path forbidden.

---

## 12. Tests

```bash
PYTHONPATH=. python3 -m pytest tests/test_p19h1_claim_state_machine_foundation.py -q
# 25 passed
```

**Regression:**

```bash
PYTHONPATH=. python3 -m pytest tests/test_p19g32_phase2_field_validation.py -q
PYTHONPATH=. python3 -m pytest tests/test_p19e2_add_vehicle_progress_card.py -q
PYTHONPATH=. python3 -m pytest tests/test_wecom_active_case.py tests/test_wecom_minimal_lanes.py tests/test_wecom_intent.py tests/test_wecom_slice.py tests/test_wecom_reply.py -q
# All passed
```

---

## 13. QA gate

```bash
bash scripts/check_chen_kui_demo_environment.sh --cloud-api
```

**Result: PASS** — QA UI + Cloud Run API + Cloud SQL aligned (2026-07-08 run).

---

## 14. Constraints (confirmed)

| Constraint | Status |
|------------|--------|
| No WeCom Claim implementation | ✅ |
| No H5 Claim implementation | ✅ |
| No OCR | ✅ |
| No schema migration | ✅ |
| No Cloud config change | ✅ |
| No deploy | ✅ |
| Add Vehicle unchanged | ✅ |

---

## 15. Known limitations

- No real Claim Start Card
- No H5 Claim photo flow
- No Workbench Claim drawer
- Accident datetime parsing not implemented (non-empty only)
- OCR not implemented
- `suggest_next_claim_transition` does not consume `event_type` yet (reserved P19H-2+)
- Foundation helpers only — no routing integration

---

## 16. GO/HOLD for P19H-2

**GO** — Foundation predicates, transition helper, guardrails, and tests are stable. Safe to start P19H-2 (WeCom Start Card + accident basics text + C1) on top of `claim_state.py`.

---

## STOP report

| Item | Value |
|------|-------|
| Module | `services/fiqa_api/wecom/claim_state.py` |
| Tests | `tests/test_p19h1_claim_state_machine_foundation.py` (25) |
| QA gate | PASS |
| Deploy | No |
| OCR | No |
| WeCom Claim flow | No |
| H5 Claim flow | No |
| Schema/cloud | No change |
| P19H-2 | **GO** |
