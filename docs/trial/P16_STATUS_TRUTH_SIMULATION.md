# P16 Status Truth — Simulation

**Sprint:** P16-P3-STATUS-TRUTH-SPRINT  
**Date:** 2026-06-07  
**Runner:** `PYTHONPATH=. python3` offline harness (collecting draft + `triage_inbox` + Case Memory)  
**Environment:** Local JSON case store (`UNIFIED_INTAKE_JSON_CASE_WRITES=1`)

---

## Scenarios

All scenarios start from Customer First collecting draft (`lifecycle_status: collecting`, empty `formal_submitted_at`).

### Scenario A — BMW X5 only

**Input:** 「我刚买了一台宝马X5」

| Field | Pre-fix | Post-fix |
|-------|---------|----------|
| `still_needed_fields` | `["year", "vin", "zip", "delivery_date", "primary_driver"]` | same |
| HTTP `lifecycle_status` | `office_followup` | **`collecting`** |
| HTTP `formal_submitted_at` | backfilled from `created_at` | **`""`** |
| `isFormalSubmissionToOfficeComplete` | **true** | **false** |
| `status_label` | `submitted_to_office` | **`saved_not_yet_submitted`** |
| `contact_state` | `waiting_for_customer` | `waiting_for_customer` |
| Green closure card | **Shown (bug)** | **Hidden** |
| Chat reply | 请补年份/车型 | 请补年份/车型 |

**Contradiction:** Pre-fix YES / Post-fix NO

---

### Scenario B — BMW X5 + year

**Input:** prior A + 「2024」

| Field | Post-fix |
|-------|----------|
| `still_needed_fields` | `["year", "vin", "zip", "delivery_date", "primary_driver"]` * |
| `lifecycle_status` | `collecting` |
| `status_label` | `saved_not_yet_submitted` |
| `contact_state` | `waiting_for_customer` |

\* Extraction may still list `year` until make/model resolved — progress truth preserved; submit remains false.

---

### Scenario C — BMW X5 + year + ZIP

**Input:** prior + 「90210」

| Field | Post-fix |
|-------|----------|
| `still_needed_fields` | `["year", "vin", "delivery_date", "primary_driver"]` |
| `lifecycle_status` | `collecting` |
| `status_label` | `saved_not_yet_submitted` |
| `contact_state` | `waiting_for_customer` |

---

### Scenario D — Fully completed formal submission

**Setup:** `handed_off`, `formal_submitted_at` set, `still_needed_fields: []`

| Field | Post-fix |
|-------|----------|
| `status_label` | **`submitted_to_office`** |
| `contact_state` | **`office_reviewing`** |
| Green closure card | Shown (correct) |

---

## Summary matrix (post-fix)

| Scenario | still_needed | status_label | contact_state | Contradiction |
|----------|--------------|--------------|---------------|---------------|
| A BMW only | non-empty | saved_not_yet_submitted | waiting_for_customer | **None** |
| B + year | non-empty | saved_not_yet_submitted | waiting_for_customer | **None** |
| C + ZIP | non-empty | saved_not_yet_submitted | waiting_for_customer | **None** |
| D formal submit | empty | submitted_to_office | office_reviewing | **None** |

---

## Customer-visible status card (post-fix A)

```
Status:        Saved — Not Yet Submitted / 已保存 · 尚未正式提交
Still Needed:  Year, VIN, ZIP, Effective Date, Driver License
Contact State: Waiting For Customer / 等待您补充信息
```

No green 「已提交办公室处理」 banner.

---

## Raw post-fix JSON (harness output)

```json
[
  {
    "scenario": "A",
    "still_needed_fields": ["year", "vin", "zip", "delivery_date", "primary_driver"],
    "http_lifecycle": "collecting",
    "http_formal_complete": false,
    "contradiction": false,
    "status_label": "saved_not_yet_submitted",
    "contact_state": "waiting_for_customer",
    "persisted_lifecycle": "collecting",
    "formal_submitted_at": ""
  },
  {
    "scenario": "D",
    "still_needed_fields": [],
    "status_label": "submitted_to_office",
    "contact_state": "office_reviewing",
    "contradiction": false
  }
]
```

---

## Re-run

```bash
PYTHONPATH=. python3 -m pytest tests/test_active_case_by_phone.py tests/test_collecting_case_memory_persistence.py -q
```

For live API (requires server on 8001):

```bash
bash scripts/run_demo_local.sh
PYTHONPATH=. python3 scripts/run_p16_status_surface_simulations.py
```
