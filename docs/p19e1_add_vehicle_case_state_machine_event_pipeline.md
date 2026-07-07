# P19E-1 — Add Vehicle Case State Machine & Event Pipeline

**Date:** 2026-07-06  
**Related:** `p19e0_spark_style_binary_step_model_recon.md`, `p19e1_add_vehicle_text_field_collection_loop`

---

## 1. Case State Machine

```mermaid
stateDiagram-v2
    [*] --> NoCase
    NoCase --> Phase1_Photos_InProgress: WeCom Start Card / 重新加车
    Phase1_Photos_InProgress --> Phase1_Photos_Complete: H5 flow_complete
    Phase1_Photos_Complete --> Phase2_Text_InProgress: Stage Complete S1 sent
    Phase2_Text_InProgress --> Phase2_Text_Complete: delivery_date + zip + phone collected
    Phase2_Text_Complete --> Phase3_Broker_Review: ready_for_broker_review
    Phase3_Broker_Review --> Broker_Done: broker confirm
    Broker_Done --> [*]
```

| State | `add_vehicle_phase` | `guided_workflow_state` |
|-------|---------------------|-------------------------|
| Phase 1 in progress | `phase_1_photos_in_progress` | — |
| Phase 1 complete | `phase_1_photos_complete` | — |
| Phase 2 in progress | `phase_2_text_in_progress` | `collecting_text_fields` |
| Phase 2 complete | `phase_3_broker_review` | `ready_for_broker_review` |
| Broker done | `phase_3_broker_done` | — |

---

## 2. Event Pipeline (with live bug annotation)

**System model:** case state machine + event pipeline. P19E-1 goal = wire WeCom text into Phase 2 after H5 photos complete.

```mermaid
flowchart TD
    A[WeCom text: date + ZIP + phone] --> B[Find active add_car case]
    B --> C{Photo phase complete?}
    C -- yes --> D{Phase 2 incomplete?}
    D -- yes --> E[Run Phase 2 extractor]
    E --> F[Write collected_fields / known_facts]
    F --> G{All 3 fields collected?}
    G -- yes --> H[Send Stage Complete S2]
    G -- no --> I[Send Current Step Card]
    C -- no --> J[Route to existing Add Vehicle flow]
    B -- no case --> K[Generic greeting menu]

    BUG["LIVE BUG fiqa-api-00160-44g: Postgres binding found case but JSON-only get_case_by_id returned None → stale_draft_binding_cleared → greeting menu"] -.-> K
```

**Fixed path (post `9cb7e5f`):** `get_case_for_read` + `find_phase2_eligible_add_car_case` — binding id resolves to Cloud SQL row → Phase 2 handler runs.

### Detailed routing (post-fix)

```mermaid
flowchart TD
    A[WeCom text message] --> B[normalize_text_message]
    B --> C{classify_wecom_intent}
    C --> D{explicit 重新加车?}
    D -->|yes| E[new add_car draft + H5 Start Card]
    D -->|no| F{Premium / Claim / Coverage high-confidence?}
    F -->|yes| G[minimal_lane handler]
    F -->|no| H[resolve_add_car_case_for_phase2]
    H --> I{photo complete AND phase2 incomplete?}
    I -->|yes| J[ingest_phase2_text_collection]
    J --> K{all 3 fields?}
    K -->|yes| L[Stage Complete S2 + ready_for_broker_review]
    K -->|no| M[Current Step Card / format hint]
    I -->|no| N{add_car high-confidence?}
    N -->|yes| O[H5 Start or S1 follow-up]
    N -->|no| P{guided_menu / unclear?}
    P -->|yes| Q[greeting menu]
    P -->|no| R[active_case / draft merge]
```

**Routing priority (P19E-1):**

1. Start Card click intents  
2. Premium / Claim / Coverage minimal lanes  
3. **Phase 2 text collection** (photo complete, text incomplete)  
4. Draft merge / add_car H5 Start  
5. Generic greeting / unclear menu  

---

## 3. Case Resolution (Cloud SQL)

| Step | Function | Read path |
|------|----------|-----------|
| Channel binding lookup | `find_open_draft_case_by_external_userid` | `list_all_cases_for_read()` → Postgres |
| Load case by id | `get_case_for_read(case_id)` | Postgres-first |
| Phase 2 fallback scan | `find_phase2_eligible_add_car_case` | Newest open add_car + photos complete |

**P19E-1 debug fix:** `slice.py` must **not** use JSON-only `get_case_by_id` on Cloud Run — that caused `stale_draft_binding_cleared` and greeting menu takeover.

---

## 4. Field Extraction (Phase 2)

| Field | Extractor | Example |
|-------|-----------|---------|
| `delivery_date` | `extract_delivery_date_from_text` | `7月10号提车` → `7月10日` |
| `zip` | `extract_zip_from_text` | `zip. 92705` → `92705` |
| `phone` | `extract_phone_from_text` | `电话2031234567` → `2031234567` |

Stored in: `collected_fields`, `known_facts`, `customer_phone` (phone).

---

## 5. WeCom Reply Cards

| Trigger | Card |
|---------|------|
| H5 `flow_complete` | Stage Complete **S1** |
| Partial Phase 2 text | Current Step Card |
| Zero fields parsed | Format hint (not greeting menu) |
| All 3 Phase 2 fields | Stage Complete **S2** |
| Broker Confirm (B0) | Done Card (true end) |

---

## 6. Live Smoke Failure (2026-07-07) — Root Cause

**Symptom:** After S1, Andy sent `7月10号提车，zip. 92705。电话2031234567` → greeting menu.

**Log evidence (`case_e341aa97b8c8`):**

```
stale_draft_binding_cleared_v1 → case_id found but get_case_by_id returned None
intent_v1 → unclear / guided_menu_required: true
reply → 您好，请选择您要办理的事项
```

**Root cause:** Postgres binding lookup succeeded; JSON-only `get_case_by_id` missed Cloud SQL row → Phase 2 handler skipped.

**Fix:** `get_case_for_read` + `find_phase2_eligible_add_car_case` fallback.
