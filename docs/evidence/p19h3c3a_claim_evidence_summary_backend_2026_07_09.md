# P19H-3c-3A — Claim Evidence Checklist Backend

**Date:** 2026-07-09  
**Branch:** `sprint/p16-trust-layer`  
**Scope:** Backend `claim_evidence_summary` only — no UI, no deploy, no schema change

---

## 1. Goal

Add a stable `claim_evidence_summary` object to Claim Workbench enrichment so Chen can see, per claim case:

- Which evidence slots are received / missing / skipped / needs_retake
- Required vs soft-required vs optional levels
- Source channel per slot
- Attachment counts and latest preview metadata
- Missing slot lists, completion level, broker next action, and summary text

Frontend UI deferred to P19H-3c-3B.

---

## 2. Why this matters commercially

Chen buys a **Broker Claim Service Copilot**, not a form system. After an accident he needs:

- 不漏事 — nothing falls through the cracks
- 不漏资料 — know what evidence is still missing
- 不用翻微信 — one Workbench view instead of scrolling WeChat
- 一打开就知道 — received / missing / next step visible immediately

This sprint delivers the backend truth layer for that checklist.

---

## 3. Backend fields added

`enrich_claim_for_workbench()` now includes `claim_evidence_summary`:

| Field | Type | Purpose |
|-------|------|---------|
| `slots` | array | Per-slot status rows |
| `missing_required_slots` | string[] | Hard-required gaps |
| `missing_soft_required_slots` | string[] | Soft-required gaps |
| `received_slots` | string[] | Slots with attachments |
| `skipped_slots` | string[] | Explicitly skipped slots |
| `completion_level` | string | Overall evidence progress |
| `broker_next_action` | string | Broker-safe next step copy |
| `summary_text` | string | Human-readable one-liner |

Each slot row:

| Field | Purpose |
|-------|---------|
| `slot_key` | Stable key |
| `label` | Chinese display label |
| `required_level` | `required` / `soft_required` / `optional` |
| `status` | `missing` / `received` / `skipped` / `needs_retake` |
| `source_channel` | `h5_task` / `wecom` / `broker_upload` / `none` |
| `attachment_count` | Count for slot |
| `latest_attachment` | Preview metadata or null |
| `skip_reason` | Skip reason when skipped |
| `needs_broker_review` | True when received or needs_retake |

---

## 4. Slot definitions

| slot_key | label | required_level |
|----------|-------|----------------|
| `customer_damage_photo` | 自己车损照片 | required |
| `other_party_vehicle_photo` | 对方车辆 / 车牌照片 | soft_required |
| `scene_photo` | 现场照片 | optional |

---

## 5. Status rules

Priority per slot:

1. Explicit `claim_attachment_slots[slot].status == needs_retake` → `needs_retake`
2. Explicit `skipped` or H5 flow skip → `skipped` (+ `skip_reason` when present)
3. Matching `case_attachments` for claim evidence → `received`
4. Else → `missing`

Attachment relevance:

- `flow == claim_evidence_pack`, OR
- `slot_assignment` / `slot_key` / `claim_slot` in claim evidence slot keys

Add Vehicle attachments (`add_vehicle_photo_flow`, `vin_photo`, etc.) are excluded.

`customer_damage_photo` skipped does **not** satisfy required gate unless `broker_override` is set on the slot.

---

## 6. Completion levels

| Level | Condition |
|-------|-----------|
| `empty` | No received or skipped evidence slots |
| `partial` | Some activity but `customer_damage_photo` not received |
| `required_complete` | `customer_damage_photo` received; soft-required other party still missing |
| `review_ready` | Required + soft-required satisfied (received or skipped); scene may be missing |
| `complete` | All three slots received or skipped |

---

## 7. Broker next action rules

| Condition | Copy |
|-----------|------|
| Any slot `needs_retake` | 有照片需要重新上传，请陈总确认后联系客户补充。 |
| `customer_damage_photo` missing | 请客户补充自己车损照片。 |
| `other_party_vehicle_photo` missing | 请客户补充对方车辆/车牌照片，或记录无法提供原因。 |
| Review-ready, scene missing | 资料基本够陈总先看；现场照片可选，有的话可继续补充。 |
| Review-ready / complete | 资料已基本齐全，请陈总人工确认后决定下一步。 |

Forbidden phrases guarded: 已报案, claim 已正式提交, 已联系保险公司, 是对方责任, 一定会赔, and existing `CLAIM_FORBIDDEN_AUTOMATION_CLAIMS`.

---

## 8. Example output JSON

```json
{
  "claim_evidence_summary": {
    "slots": [
      {
        "slot_key": "customer_damage_photo",
        "label": "自己车损照片",
        "required_level": "required",
        "status": "received",
        "source_channel": "h5_task",
        "attachment_count": 1,
        "latest_attachment": {
          "attachment_id": "att_h5_damage",
          "filename": "damage.jpg",
          "mime_type": "image/jpeg",
          "source": "h5_task",
          "received_at": "2026-07-09T18:00:00+00:00"
        },
        "skip_reason": null,
        "needs_broker_review": true
      },
      {
        "slot_key": "other_party_vehicle_photo",
        "label": "对方车辆 / 车牌照片",
        "required_level": "soft_required",
        "status": "missing",
        "source_channel": "none",
        "attachment_count": 0,
        "latest_attachment": null,
        "skip_reason": null,
        "needs_broker_review": false
      },
      {
        "slot_key": "scene_photo",
        "label": "现场照片",
        "required_level": "optional",
        "status": "missing",
        "source_channel": "none",
        "attachment_count": 0,
        "latest_attachment": null,
        "skip_reason": null,
        "needs_broker_review": false
      }
    ],
    "missing_required_slots": [],
    "missing_soft_required_slots": ["other_party_vehicle_photo"],
    "received_slots": ["customer_damage_photo"],
    "skipped_slots": [],
    "completion_level": "required_complete",
    "broker_next_action": "请客户补充对方车辆/车牌照片，或记录无法提供原因。",
    "summary_text": "已收到自己车损照片；还缺对方车辆 / 车牌照片。"
  }
}
```

---

## 9. Tests

`tests/test_p19h3c3a_claim_evidence_summary_backend.py` — 8 tests:

1. Empty claim evidence
2. H5 customer damage photo received
3. Other-party skipped with `skip_reason`
4. Scene optional does not block review-ready
5. Needs-retake priority over attachment
6. Add Vehicle attachments excluded
7. Enrichment includes summary without breaking existing fields
8. Forbidden copy absent

---

## 10. Regression results

```
PYTHONPATH=. python3 -m pytest tests/test_p19h3c3a_claim_evidence_summary_backend.py -q
# 8 passed

PYTHONPATH=. python3 -m pytest tests/test_p19h3a_claim_workbench_visibility.py -q
PYTHONPATH=. python3 -m pytest tests/test_p19h3c1_claim_h5_evidence_foundation.py -q
PYTHONPATH=. python3 -m pytest tests/test_p19h3c2_claim_c1_h5_button.py -q
PYTHONPATH=. python3 -m pytest tests/test_p19h2_simplified_claim_wecom_basics.py -q
# 43 passed

PYTHONPATH=. python3 -m pytest tests -q -k "h5"
# 78 passed
```

---

## 11. QA gate result

```
bash scripts/check_chen_kui_demo_environment.sh --cloud-api
# Result: PASS — QA UI + Cloud Run API + Cloud SQL aligned
# revision=fiqa-api-00171-hbx (unchanged — no deploy this sprint)
```

---

## 12. Constraints honored

- No deploy
- No schema change
- No frontend UI
- No OCR
- No direct WeCom image binding
- No identity resolver
- No duplicate merge
- No workflow engine

---

## 13. Known limitations

- UI not showing checklist yet (P19H-3c-3B)
- H5 explicit `claim_attachment_slots` persistence still partial; status inferred from attachments + `h5_photo_flow_state` skips
- WeCom direct image binding deferred
- Identity resolver deferred
- Phone summary deferred

---

## 14. Next recommended prompt

1. **P19H-3c-3B** — Workbench Evidence Checklist UI
2. **P19H-3c-3C** — H5 Slot Persistence / Skip Reason (write `claim_attachment_slots` on upload/skip)

---

## 15. GO / HOLD

**GO** — Backend `claim_evidence_summary` is stable, tested, and integrated into Workbench enrichment. Ready for UI sprint.
