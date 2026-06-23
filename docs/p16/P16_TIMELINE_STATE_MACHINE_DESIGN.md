# P16 Timeline + Case State Machine Design

**Date:** 2026-06-19  
**Sprint:** P16 Timeline Design Review  
**SSOT:** `docs/p16/P16_DECISION_FREEZE_V1.md`  
**Status:** DESIGN ONLY — do not implement until approved  
**Authored by:** Design review pass over full repo codebase

---

## 0. Design Constraints (from SSOT)

This design must comply with P16 Decision Freeze V1:

- No CRM
- No full workflow engine (Temporal/Camunda frozen out)
- No customer accounts or logins
- No PDF generation
- No WeChat integration
- Ant Design 5 only (no UI library migration)
- FastAPI backend (`services/fiqa_api/`)
- Postgres for durable cases (DB-primary on Cloud Run)
- Product stays simple — TurboTax mobile, not Salesforce

---

## TASK 1 — EXISTING_ASSETS_TO_REUSE

After reading all relevant source files, these assets exist and should be reused directly:

### Backend

| Asset | File | Reuse How |
|-------|------|-----------|
| `case_activity` array | `services/fiqa_api/inbox_triage/case_store.py` | Already a proto-timeline. Add P16-specific `activity_type` values. No schema change needed for MVP. |
| `save_case()` function | `case_store.py` | Call from `add_car.py` to create a persisted case record after extraction |
| `update_case_status()` | `case_store.py` | Drive state transitions with existing terminal-state guardrail |
| `_build_activity_entry()` | `case_store.py` | Build timeline event entries (already has `activity_id`, `activity_type`, `message`, `created_at`) |
| `lifecycle_status` field | `case_store.py` | `collecting → handoff_pending → handed_off → office_followup` — map to packet states |
| `append_follow_up_message()` | `case_store.py` | Reuse for broker-side events appended after initial packet |
| `case_status` values | `case_store.py` | `new, reviewing, waiting_client, done, closed` — reuse for broker-side state |
| `state_history` table | `db/schema/stage1_service_record.sql` | Already exists in Postgres. Records from/to status transitions. Reuse for timeline state events. |
| `office_actions` table | `db/schema/stage1_service_record.sql` | Already exists. Use for broker-side actions (BROKER_REVIEWED, QUOTE_SENT). |
| `structured_record_data` table | `db/schema/stage1_service_record.sql` | Already has `structured_payload JSONB`. Store extracted packet here. |
| `service_records` table | `db/schema/stage1_service_record.sql` | Primary case row — `vehicle_key`, `primary_vehicle_summary` already present |
| VIN validation logic | `routes/add_car.py` | `validate_vin()` — already produces `(is_valid, reason)` tuple; reuse for VIN_VALIDATED event |
| `_apply_primary_driver_default()` | `routes/add_car.py` | Already generates `confirmation_notices` — emit as `PRIMARY_DRIVER_DEFAULTED` timeline event |
| `second_vehicle_detected` flag | `ocr_kill_test/packet_builder.py` | Already set when two VINs found — emit as `VIN_CONFLICT_FLAGGED` event |
| `active_case_lookup.py` | `inbox_triage/active_case_lookup.py` | Phone-based active case lookup (Rule 7: one active case per phone) — use to detect duplicate submissions |
| `find_active_add_car_case_by_phone()` | `active_case_lookup.py` | Conflict detection for same-phone, new-upload scenarios |
| `vehicle_key` field | `case_store.py` line 714 | Already stored on case — reuse to link case ↔ vehicle identity |
| `additional_vehicle_mentioned` | `case_store.py` line 715 | Already flags second vehicle on case |

### Frontend

| Asset | File | Reuse How |
|-------|------|-----------|
| `PacketStep` render block | `ui/src/pages/AddCarPage.tsx` | Add `<Timeline>` component inside existing PacketStep Card |
| `PacketResponse` type | `AddCarPage.tsx` line 56 | Add `case_id: string` and `timeline_events: TimelineEvent[]` fields |
| Ant Design imports | `AddCarPage.tsx` lines 11–27 | Already imports Card, Tag, Alert, Button — add `Timeline` |
| `WizardStep` type | `AddCarPage.tsx` line 66 | Already tracks `info → upload → extracting → packet` |
| `confirmation_notices` | `AddCarPage.tsx` line 63 | Already rendered as soft yellow notices — tie to timeline |

### What Does NOT Exist Yet

| Missing Piece | Notes |
|---------------|-------|
| `case_id` returned from `/api/intake/add-car/extract` | Route generates a local ephemeral ID but does NOT persist a case — must wire `save_case()` |
| Timeline events written for add-car flow | `case_activity` exists but `add_car.py` never calls `save_case()` |
| Timeline UI component in PacketStep | No `<Timeline>` in current `AddCarPage.tsx` |
| `p16_packet_state` on case | No dedicated add-car packet state field beyond generic `lifecycle_status` |

---

## TASK 2 — TIMELINE_EVENT_TYPES

### V1 MVP Events (implement now)

These are the events the system can emit automatically without any human action:

| Event Type | Trigger | Actor | Fields |
|------------|---------|-------|--------|
| `CASE_CREATED` | Customer submits name + phone + ZIP | system | `case_id`, `customer_name`, `phone`, `garaging_zip` |
| `DOCUMENT_UPLOADED` | Each file received by the endpoint | customer | `filename`, `file_type`, `size_bytes` |
| `AI_EXTRACTED_PACKET` | Gemini/OpenAI returns structured fields | system | `model_used`, `fields_extracted` (count), `elapsed_ms` |
| `VIN_VALIDATED` | `validate_vin()` runs on extracted VIN | system | `vin`, `valid: bool`, `reason` |
| `PRIMARY_DRIVER_DEFAULTED` | Customer name used as default for primary driver | system | `defaulted_to`, `needs_confirmation: true` |
| `MISSING_ITEM_DETECTED` | Required field not found in any document | system | `field_name`, `field_label` |
| `VIN_CONFLICT_FLAGGED` | Multiple VINs or `second_vehicle_detected` | system | `vin_count`, `conflict_reason` |
| `PACKET_READY` | All required fields present (VIN + year + make + model) | system | `packet_completeness` |

### V2 Events (defer — post-pilot)

These require manual broker action or customer confirmation:

| Event Type | Deferred Until |
|------------|---------------|
| `BROKER_REVIEWED` | After pilot proves value; needs broker login or token |
| `FIELD_COPIED` | After pilot; requires client-side beacon |
| `CUSTOMER_CONFIRMED` | Post-Trust Layer (frozen out in §4) |
| `QUOTE_READY` | Post-10-case gate |
| `QUOTE_SENT` | Post-payment milestone |
| `POLICY_BOUND` | Post-payment milestone |
| `CASE_CLOSED` | After `update_case_status("closed")` wired to UI |

### Event Schema (additive to existing `case_activity` structure)

```python
{
    "activity_id": "act_abc123def456",   # reuse existing format
    "activity_type": "AI_EXTRACTED_PACKET",   # P16-specific type
    "message": "Gemini Flash 2.5 extracted 6 fields from 2 documents.",
    "created_at": "2026-06-19T09:05:00Z",
    # P16-specific payload (optional — carried in "meta" sub-key)
    "meta": {
        "model_used": "gemini-1.5-flash",
        "fields_extracted": 6,
        "vin": "5UXZV4C56BL402905"
    }
}
```

The `meta` field is additive — existing `case_activity` normalization ignores unknown keys, so this does not break existing code.

---

## TASK 3 — RECOMMENDED_CASE_HIERARCHY

### Recommended: `Customer → Case → Vehicle → Timeline Events`

```
Customer (identified by phone, no login)
  └── Case (one per add-car intake session)
        ├── Vehicle (extracted: VIN + year + make + model)
        └── Timeline Events (ordered list of what happened)
              ├── CASE_CREATED
              ├── DOCUMENT_UPLOADED (×N files)
              ├── AI_EXTRACTED_PACKET
              ├── VIN_VALIDATED
              ├── PRIMARY_DRIVER_DEFAULTED
              ├── MISSING_ITEM_DETECTED (×M missing fields)
              └── PACKET_READY (or VIN_CONFLICT_FLAGGED)
```

### Why This Hierarchy

| Decision | Rationale |
|----------|-----------|
| **Customer is by phone** | No login. Phone is the identity key. Already enforced by `active_case_lookup.py` Rule 7. |
| **One Case per intake session** | One upload batch = one case. Prevents silent merging of different vehicles. |
| **Vehicle hangs off Case** | The vehicle (VIN + year + make + model) is the product of one extraction run. Not independent. |
| **Timeline Events hang off Case** | Events are specific to one intake session, not to the customer globally. |
| **Second VIN = new Case** | Never auto-merge two vehicles into one case. Flag, then broker decides. |

### What This Hierarchy Does NOT Do

- Does not create a customer profile (no customer table in V1)
- Does not link multiple cases to one customer record (phone lookup is sufficient for pilot)
- Does not link trade-in vehicle to a separate case automatically
- Does not display all customer cases in a list (deferred — no dashboard in pilot)

### Multi-Vehicle Rule (conflict cases)

| Upload Scenario | Action |
|-----------------|--------|
| Same phone, same VIN, new docs | Append to existing case (add `DOCUMENT_UPLOADED` events) |
| Same phone, different VIN | Create new case; flag `VIN_CONFLICT_FLAGGED` on new case; log in broker view |
| Trade-in VIN detected in upload | Set `additional_vehicle_mentioned=True`; emit `VIN_CONFLICT_FLAGGED`; broker decides |
| Two VINs in same upload batch | `second_vehicle_detected=True` (already coded); use primary VIN; warn broker |

---

## TASK 4 — STATE MACHINE

### Final Case States

```
NEW  →  DOCS_UPLOADED  →  PACKET_BUILT  →  READY_FOR_QUOTE
                                        ↘
                                    MISSING_ITEMS  →  READY_FOR_QUOTE (broker resolves)

READY_FOR_QUOTE  →  CLOSED  (terminal — no QUOTED/BOUND in V1)
```

### States

| State | `p16_packet_state` value | Meaning |
|-------|--------------------------|---------|
| `NEW` | `new` | Case created, no documents yet |
| `DOCS_UPLOADED` | `docs_uploaded` | At least one file uploaded; extraction not yet done |
| `PACKET_BUILT` | `packet_built` | AI extraction complete; packet assembled |
| `MISSING_ITEMS` | `missing_items` | Required field(s) not found: VIN, year, make, or model |
| `READY_FOR_QUOTE` | `ready_for_quote` | All required fields present; broker can act |
| `CLOSED` | `closed` | Terminal — maps to `case_status = "closed"` |

### State Transitions

| From | To | Trigger |
|------|----|---------|
| `NEW` | `DOCS_UPLOADED` | At least one file received in extract endpoint |
| `DOCS_UPLOADED` | `PACKET_BUILT` | Extraction completes without error |
| `PACKET_BUILT` | `MISSING_ITEMS` | Any of VIN, year, make, model is empty after extraction |
| `PACKET_BUILT` | `READY_FOR_QUOTE` | VIN + year + make + model all present |
| `MISSING_ITEMS` | `READY_FOR_QUOTE` | Broker manually marks complete (V2 — defer) |
| `READY_FOR_QUOTE` | `CLOSED` | Broker closes case (V2 UI action) |
| Any | `CLOSED` | `update_case_status("closed")` — existing guardrail applies |

### How This Maps to Existing Fields

| P16 State | Existing `lifecycle_status` | Existing `case_status` |
|-----------|----------------------------|------------------------|
| `NEW` | `collecting` | `new` |
| `DOCS_UPLOADED` | `collecting` | `new` |
| `PACKET_BUILT` | `handoff_pending` | `new` |
| `MISSING_ITEMS` | `handoff_pending` | `waiting_client` |
| `READY_FOR_QUOTE` | `handed_off` | `reviewing` |
| `CLOSED` | `handed_off` | `closed` |

**Implementation note:** Store `p16_packet_state` in `structured_record_data.structured_payload` JSONB for V1. Do not add a new column. In V2, promote to a real column after pilot proves the states are stable.

---

## TASK 5 — MINIMAL_DATABASE_SCHEMA

### What Already Exists (reuse as-is)

| Table | Already Has | Use For |
|-------|-------------|---------|
| `service_records` | `record_id`, `customer_name`, `customer_phone`, `lifecycle_status`, `vehicle_key`, `extra JSONB` | Case row; store `p16_packet_state` in `extra` |
| `state_history` | `from_status`, `to_status`, `triggered_by`, `reason`, `created_at` | State transition events (VIN_VALIDATED state changes) |
| `office_actions` | `action_type`, `note_text`, `actor`, `created_at` | Broker actions in V2 |
| `structured_record_data` | `structured_payload JSONB`, `quote_readiness`, `missing_fields_summary` | Packet JSON storage |

### New Table: `p16_timeline_events`

**Purpose:** Ordered log of everything that happened in one add-car case. Unlike `case_activity` (JSONB in `extra`), this is a proper relational table that can be queried, filtered, and displayed without deserializing the full case blob.

```sql
CREATE TABLE IF NOT EXISTS p16_timeline_events (
    event_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id      TEXT NOT NULL REFERENCES service_records (record_id) ON DELETE CASCADE,
    event_type   TEXT NOT NULL,        -- CASE_CREATED, DOCUMENT_UPLOADED, etc.
    actor        TEXT NOT NULL DEFAULT 'system',   -- 'system', 'customer', 'broker'
    message      TEXT NOT NULL,        -- Human-readable one-liner
    meta         JSONB DEFAULT '{}'::jsonb,   -- Event-specific payload (VIN, filename, etc.)
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_p16_timeline_case_created
    ON p16_timeline_events (case_id, created_at ASC);
```

**Key columns:**

| Column | Type | Notes |
|--------|------|-------|
| `event_id` | UUID | Stable identity for dedup |
| `case_id` | TEXT | FK to `service_records.record_id` |
| `event_type` | TEXT | Enum-like string from TIMELINE_EVENT_TYPES above |
| `actor` | TEXT | Who caused it: `system`, `customer`, `broker` |
| `message` | TEXT | Plain English: "2 files uploaded (insurance_card.png, smog_check.png)" |
| `meta` | JSONB | Event payload: `{"vin": "5UX...", "valid": true}` |
| `created_at` | TIMESTAMPTZ | Ordered timeline |

**What NOT to store yet:**

- `user_id` (no logins in V1)
- `ip_address` (not needed for pilot)
- Complex nested payloads (keep `meta` flat and small)
- Broker-side events (V2 — needs broker auth)

**Why this table is needed:**

The existing `case_activity` is stored as JSONB inside `service_records.extra`. It works fine for JSON-store pilot mode but:
1. Cannot be queried by event type across cases without full table scan + JSONB extraction
2. Cannot be joined with other tables for reporting
3. Cannot be displayed without loading the full case blob

For the pilot (3–10 cases), either approach works. The `p16_timeline_events` table is the right production design; `case_activity` is the right MVP shortcut.

**MVP shortcut (V1):** Write timeline events to `case_activity` in the existing `extra` JSONB. Add the `p16_timeline_events` table migration before the 10-case gate.

### Summary of All Tables

| Table | Status | Use in P16 |
|-------|--------|------------|
| `service_records` | Exists | Case row; add `p16_packet_state` to `extra` |
| `structured_record_data` | Exists | Store extracted packet JSON |
| `state_history` | Exists | State transitions |
| `office_actions` | Exists | Broker actions (V2) |
| `p16_timeline_events` | **New** | Ordered event log (add before 10-case gate) |

---

## TASK 6 — CONFLICT_RULES

### Rule 1: Same Customer, Same VIN, New Upload

**Scenario:** Andy Li (626-555-0000) uploads again with the same BMW VIN `5UXZ...`.

| Decision | Append to existing case |
|----------|------------------------|
| **Merge?** | Yes — same vehicle, same case |
| **New case?** | No |
| **Ask broker?** | No |
| **Ask customer?** | No |
| **Timeline event?** | `DOCUMENT_UPLOADED` on existing case |
| **Warning?** | Soft notice: "Additional documents added to existing case" |

Implementation: `find_active_add_car_case_by_phone()` returns existing case → `add_attachment_to_case()` → append `DOCUMENT_UPLOADED` event.

---

### Rule 2: Same Customer, Different VIN

**Scenario:** Andy Li sends a purchase agreement for a different car (second VIN).

| Decision | Create new case |
|----------|----------------|
| **Merge?** | No — never auto-merge different VINs |
| **New case?** | Yes — new `case_id` for the new vehicle |
| **Ask broker?** | Surface both cases in broker view (V2) |
| **Ask customer?** | No (no customer login) |
| **Timeline event?** | `VIN_CONFLICT_FLAGGED` on both cases |
| **Warning?** | "A different VIN was detected. A new case has been created." |

Implementation: `find_active_add_car_case_by_phone()` returns existing case → VIN mismatch detected → `save_case()` for new case → emit `VIN_CONFLICT_FLAGGED` on new case.

---

### Rule 3: Trade-In VIN Appears

**Scenario:** Customer uploads a document set that includes both a purchase agreement (new car VIN) and an old registration (trade-in VIN).

| Decision | Flag; use primary VIN |
|----------|----------------------|
| **Merge?** | No |
| **New case?** | No — one intake session, one case |
| **Ask broker?** | Yes — `VIN_CONFLICT_FLAGGED` warning in packet |
| **Ask customer?** | No |
| **Timeline event?** | `VIN_CONFLICT_FLAGGED` with `conflict_reason: "trade_in_detected"` |
| **Warning?** | "Multiple VINs detected. Please verify which one is the new vehicle." (existing warning text) |

Implementation: Already coded. `second_vehicle_detected` flag from `packet_builder` + existing warning in `_run_real_extraction()`. Just wire event emission.

---

### Rule 4: Old Insurance Card VIN Appears

**Scenario:** Customer uploads both a new purchase agreement and an old insurance card for a different vehicle.

| Decision | Use newer VIN; flag conflict |
|----------|------------------------------|
| **Merge?** | No |
| **New case?** | No |
| **Ask broker?** | Yes — conflict warning |
| **Ask customer?** | No |
| **Timeline event?** | `VIN_CONFLICT_FLAGGED` with `conflict_reason: "multiple_vins_across_docs"` |
| **Warning?** | Already generated: "Multiple VINs detected. Please verify which one is the new vehicle." |

Implementation: `vin_conflicts` list from `result.conflicts` in `_run_real_extraction()`. Already surfaced in `warnings`. Just emit timeline event.

---

### Rule 5: New Purchase Agreement Conflicts With Old Registration

**Scenario:** Two documents show different effective dates (insurance card March 2026 vs purchase agreement June 2026).

| Decision | Surface conflict; broker resolves |
|----------|-----------------------------------|
| **Merge?** | N/A — same case, field-level conflict |
| **New case?** | No |
| **Ask broker?** | Yes — "Conflicting delivery_or_effective_date values detected" (existing warning) |
| **Ask customer?** | No |
| **Timeline event?** | `MISSING_ITEM_DETECTED` with `field: effective_date, reason: conflict` |
| **Warning?** | Already generated by existing code |

---

### Rule 6: Two Vehicles in Same Upload

**Scenario:** Customer uploads a 4-page PDF that contains both a new car purchase agreement and an existing vehicle title.

| Decision | Use primary VIN; flag secondary |
|----------|--------------------------------|
| **Merge?** | No |
| **New case?** | No — same upload session |
| **Ask broker?** | Yes — primary VIN chosen, broker must verify |
| **Ask customer?** | No |
| **Timeline event?** | `VIN_CONFLICT_FLAGGED` with `conflict_reason: "two_vehicles_in_upload"` |
| **Warning?** | "Multiple VINs detected. Please verify which one is the new vehicle." |

Implementation: `second_vehicle_detected` flag + `additional_vehicle_count_hint`. Already coded.

---

### Conflict Decision Matrix Summary

| Scenario | New Case? | Merge? | Ask Broker? | Timeline Event |
|----------|-----------|--------|-------------|----------------|
| Same VIN, new docs | No | Yes | No | `DOCUMENT_UPLOADED` |
| Different VIN, same phone | **Yes** | No | Yes | `VIN_CONFLICT_FLAGGED` |
| Trade-in VIN detected | No | No | Yes | `VIN_CONFLICT_FLAGGED` |
| Old insurance card VIN | No | No | Yes | `VIN_CONFLICT_FLAGGED` |
| Date conflict across docs | No | N/A | Yes | `MISSING_ITEM_DETECTED` |
| Two vehicles in one upload | No | No | Yes | `VIN_CONFLICT_FLAGGED` |

**Hard rule:** Never overwrite an existing VIN field silently. Never auto-merge two different VINs into one case. When in doubt, flag and let the broker decide.

---

## TASK 7 — TIMELINE_UI_V1

### Placement

The Timeline component lives **inside the PacketStep Card**, below the main packet fields and above the Copy Packet button. It is collapsed by default (behind a `<Collapse>` panel) so it doesn't clutter the primary broker view.

### Components Used

All from Ant Design 5 (already installed):

```tsx
import { Timeline, Tag, Collapse, Card } from 'antd';
import {
  CheckCircleOutlined,
  WarningOutlined,
  FileTextOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons';
```

### Visual Design

```
┌─────────────────────────────────────────────────────┐
│  Trusted Packet   CK-001 · Jun 19, 2026, 9:05 AM   │
│  Andy Li · 91101                                    │
├─────────────────────────────────────────────────────┤
│  [warnings block]                                   │
│  [VIN + vehicle fields]                             │
│  [Copy Packet button]                               │
├─────────────────────────────────────────────────────┤
│  ▶ Case Timeline                          [collapse] │
├─────────────────────────────────────────────────────┤
│  (when expanded):                                   │
│                                                     │
│  ●  9:05 AM  Case created                          │
│     Andy Li · 626-555-0000 · ZIP 91101             │
│                                                     │
│  ●  9:05 AM  2 files uploaded                      │
│     insurance_card.png · smog_check_vir.png        │
│                                                     │
│  ●  9:06 AM  AI extracted packet           [14s]   │
│     6 fields from 2 documents                      │
│                                                     │
│  ●  9:06 AM  VIN validated ✓                       │
│     5UXZV4C56BL402905 — format valid               │
│                                                     │
│  ⚠  9:06 AM  Primary driver defaulted              │
│     Defaulted to customer name — confirm            │
│                                                     │
│  Next: Broker confirm primary driver                │
└─────────────────────────────────────────────────────┘
```

### React Component Sketch

```tsx
// TimelinePanel — add inside PacketStep Card in AddCarPage.tsx

type TimelineEvent = {
  event_type: string;
  actor: 'system' | 'customer' | 'broker';
  message: string;
  created_at: string;
  meta?: Record<string, unknown>;
};

const EVENT_ICONS: Record<string, React.ReactNode> = {
  CASE_CREATED: <CheckCircleOutlined style={{ color: '#52c41a' }} />,
  DOCUMENT_UPLOADED: <FileTextOutlined style={{ color: '#1677ff' }} />,
  AI_EXTRACTED_PACKET: <CheckCircleOutlined style={{ color: '#52c41a' }} />,
  VIN_VALIDATED: <CheckCircleOutlined style={{ color: '#52c41a' }} />,
  PRIMARY_DRIVER_DEFAULTED: <WarningOutlined style={{ color: '#faad14' }} />,
  MISSING_ITEM_DETECTED: <WarningOutlined style={{ color: '#ff4d4f' }} />,
  VIN_CONFLICT_FLAGGED: <WarningOutlined style={{ color: '#ff4d4f' }} />,
  PACKET_READY: <CheckCircleOutlined style={{ color: '#52c41a' }} />,
};

const EVENT_COLORS: Record<string, string> = {
  CASE_CREATED: 'green',
  DOCUMENT_UPLOADED: 'blue',
  AI_EXTRACTED_PACKET: 'green',
  VIN_VALIDATED: 'green',
  PRIMARY_DRIVER_DEFAULTED: 'orange',
  MISSING_ITEM_DETECTED: 'red',
  VIN_CONFLICT_FLAGGED: 'red',
  PACKET_READY: 'green',
};

function formatEventTime(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
}

function TimelinePanel({ events, nextAction }: {
  events: TimelineEvent[];
  nextAction?: string;
}) {
  if (!events || events.length === 0) return null;

  const items = events.map((ev) => ({
    color: EVENT_COLORS[ev.event_type] ?? 'gray',
    dot: EVENT_ICONS[ev.event_type],
    children: (
      <div>
        <Text type="secondary" style={{ fontSize: 12 }}>
          {formatEventTime(ev.created_at)}
        </Text>
        {' '}
        <Text>{ev.message}</Text>
      </div>
    ),
  }));

  if (nextAction) {
    items.push({
      color: 'blue',
      dot: <ClockCircleOutlined style={{ color: '#1677ff' }} />,
      children: (
        <Text strong style={{ color: '#1677ff' }}>
          Next: {nextAction}
        </Text>
      ),
    });
  }

  return (
    <Collapse
      size="small"
      ghost
      items={[{
        key: 'timeline',
        label: 'Case Timeline',
        children: <Timeline items={items} />,
      }]}
    />
  );
}
```

### Rules

- Timeline is **collapsed by default** — primary broker view is still the packet
- Events are **chronological ascending** (oldest at top, newest at bottom)
- `Next Action` is always the last item in blue
- Max 8 events shown in MVP (no pagination needed for pilot)
- No raw timestamps — use friendly time format (`9:06 AM`)

---

## TASK 8 — TIMELINE_MVP_SCOPE

### V1 — Build Now

| Item | Description |
|------|-------------|
| Wire `save_case()` from `add_car.py` | Create a `case_id` when extraction completes; persist case to Postgres |
| Emit timeline events to `case_activity` | CASE_CREATED, DOCUMENT_UPLOADED (×N), AI_EXTRACTED_PACKET, VIN_VALIDATED, PRIMARY_DRIVER_DEFAULTED (if applicable), MISSING_ITEM_DETECTED (×M), VIN_CONFLICT_FLAGGED (if applicable), PACKET_READY |
| Return `case_id` + `timeline_events` in API response | Add to `PacketResponse` schema |
| `TimelinePanel` in PacketStep | Collapsed `<Collapse>` with `<Timeline>` inside |
| `Next Action` line | Derive from packet state: "Broker confirm primary driver" or "All fields present — ready to quote" |

### NOT IN V1 SCOPE

| Item | Reason |
|------|--------|
| Full `p16_timeline_events` Postgres table | MVP uses `case_activity` JSONB; add table before 10-case gate |
| Broker-side events (BROKER_REVIEWED, FIELD_COPIED) | No broker login in V1 |
| Customer confirmation flow | Frozen out in Decision Freeze §4 |
| Quote/policy events (QUOTED, BOUND) | Post-payment milestone |
| Case list / dashboard timeline | Not a CRM — no dashboard in pilot |
| Multi-case view per customer | Deferred; one case per session is sufficient for pilot |
| Timeline filter / search | Overkill for 3–10 pilot cases |
| Pagination of timeline events | Max 8 events per case in V1 |
| Trade-in automation | Frozen out in Decision Freeze §4 |
| Case linking across phones | No customer accounts |

---

## TASK 9 — TWO_DAY_BUILD_PLAN

### Pre-conditions

- Postgres is live (Cloud Run backend with `SERVICE_RECORD_DATABASE_URL` set)
- `UNIFIED_INTAKE_DB_PRIMARY_WRITES=1` configured in Cloud Run env
- `save_case()` and `case_store.py` are fully tested (200+ guardrail tests pass — confirmed)

---

### Day 1 — Backend Data Model + Event Writer

**Goal:** Every successful add-car extraction creates a persisted case with timeline events.

#### Hour 1–2: Wire `save_case()` into `add_car.py`

**File:** `services/fiqa_api/routes/add_car.py`

1. After `_run_real_extraction()` succeeds, build a minimal `triage_result` dict and call `save_case()`.
2. Set `service_lane = "add_car"`, `lifecycle_status = "handed_off"` (packet is ready for broker).
3. Return `case_id` in the extract response.

New helper `_write_add_car_case()`:

```python
def _write_add_car_case(
    customer_name: str,
    phone: str,
    garaging_zip: str,
    packet: dict,
    warnings: list[str],
    sources: list[dict],
    file_names: list[str],
    timeline_events: list[dict],
    model_used: str,
) -> str | None:
    """Persist case + timeline events. Returns case_id or None on failure."""
    try:
        from services.fiqa_api.inbox_triage.case_store import save_case
        from services.fiqa_api.inbox_triage.intake_service_lanes import SERVICE_LANE_ADD_CAR

        vin_val = (packet.get("vin") or {}).get("value") or ""
        year_val = (packet.get("year") or {}).get("value") or ""
        make_val = (packet.get("make") or {}).get("value") or ""
        model_val = (packet.get("model") or {}).get("value") or ""

        missing = [f for f in ["vin", "year", "make", "model"] if not (packet.get(f) or {}).get("value")]
        has_conflict = any("Multiple VINs" in w for w in warnings)
        
        p16_packet_state = (
            "missing_items" if missing else
            "ready_for_quote"
        )

        vehicle_summary = " ".join(filter(None, [year_val, make_val, model_val])).strip() or None
        
        triage_result = {
            "issue_category": "add_car_quote",
            "urgency": "medium",
            "manual_followup_needed": bool(missing or has_conflict),
            "broker_next_step": (
                f"Packet ready — verify {'and '.join(missing)} manually."
                if missing else
                "Packet ready — all required fields extracted."
            ),
            "client_prep": "",
            "client_reply_draft": "",
            "handoff_ready": not bool(missing),
            "lifecycle_status": "handed_off",
            "service_type": "add_car",
            "extracted_contact_name": customer_name,
            "extracted_contact_phone": phone,
            "quote_ready_status": "quote_ready" if not missing else "need_more",
            "collected_fields": [f for f in ["vin", "year", "make", "model"] if f not in missing],
            "still_needed_fields": missing,
            "primary_vehicle_summary": vehicle_summary,
            "case_activity": timeline_events,  # pre-built events
        }

        saved = save_case(
            source_text=f"[客户] P16 Add-Car upload: {', '.join(file_names)}",
            triage_result=triage_result,
            status="reviewing" if not missing else "waiting_client",
            service_lane=SERVICE_LANE_ADD_CAR,
        )
        return str(saved.get("case_id") or "").strip() or None
    except Exception:
        logger.exception("Failed to persist add-car case — non-blocking")
        return None
```

#### Hour 2–3: Build timeline event writer

**File:** `services/fiqa_api/routes/add_car.py`

New helper `_build_add_car_timeline_events()`:

```python
def _build_add_car_timeline_events(
    customer_name: str,
    phone: str,
    garaging_zip: str,
    file_names: list[str],
    packet: dict,
    warnings: list[str],
    model_used: str,
) -> list[dict]:
    from uuid import uuid4
    from datetime import datetime, timezone

    def _now() -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    def _event(event_type: str, message: str, meta: dict | None = None) -> dict:
        return {
            "activity_id": f"act_{uuid4().hex[:12]}",
            "activity_type": event_type,
            "message": message,
            "created_at": _now(),
            "meta": meta or {},
        }

    events: list[dict] = []

    # CASE_CREATED
    events.append(_event(
        "CASE_CREATED",
        f"Case created — {customer_name} · {phone[-4:]} · ZIP {garaging_zip}",
        {"customer_name": customer_name, "garaging_zip": garaging_zip},
    ))

    # DOCUMENT_UPLOADED (×N)
    for fname in file_names:
        events.append(_event(
            "DOCUMENT_UPLOADED",
            f"Document uploaded: {fname}",
            {"filename": fname},
        ))

    # AI_EXTRACTED_PACKET
    fields_extracted = sum(
        1 for k in ["vin", "year", "make", "model", "primary_driver", "effective_date"]
        if (packet.get(k) or {}).get("value")
    )
    events.append(_event(
        "AI_EXTRACTED_PACKET",
        f"{model_used} extracted {fields_extracted} fields from {len(file_names)} document(s).",
        {"model_used": model_used, "fields_extracted": fields_extracted},
    ))

    # VIN_VALIDATED
    vin_val = (packet.get("vin") or {}).get("value") or ""
    if vin_val:
        from services.fiqa_api.routes.add_car import validate_vin
        vin_ok, vin_reason = validate_vin(vin_val)
        events.append(_event(
            "VIN_VALIDATED",
            f"VIN {vin_val} — {'valid' if vin_ok else vin_reason}",
            {"vin": vin_val, "valid": vin_ok, "reason": vin_reason},
        ))
    else:
        events.append(_event(
            "MISSING_ITEM_DETECTED",
            "VIN not found in uploaded documents.",
            {"field": "vin"},
        ))

    # PRIMARY_DRIVER_DEFAULTED
    pd = packet.get("primary_driver") or {}
    if pd.get("source_file") == "default_from_customer_name":
        events.append(_event(
            "PRIMARY_DRIVER_DEFAULTED",
            f"Primary driver defaulted to customer name: {pd.get('value')} — confirm with customer.",
            {"defaulted_to": pd.get("value"), "needs_confirmation": True},
        ))

    # MISSING_ITEM_DETECTED
    missing = [f for f in ["vin", "year", "make", "model"] if not (packet.get(f) or {}).get("value")]
    for field in missing:
        events.append(_event(
            "MISSING_ITEM_DETECTED",
            f"Required field not found: {field}.",
            {"field": field},
        ))

    # VIN_CONFLICT_FLAGGED
    if any("Multiple VINs" in w for w in warnings):
        events.append(_event(
            "VIN_CONFLICT_FLAGGED",
            "Multiple VINs detected across documents — broker must verify correct vehicle.",
            {"conflict_reason": "multiple_vins_across_docs"},
        ))

    # PACKET_READY or MISSING_ITEMS terminal event
    if not missing:
        events.append(_event(
            "PACKET_READY",
            "All required fields extracted — packet ready for broker.",
        ))

    return events
```

#### Hour 3–4: Tests

**File:** `tests/test_add_car_timeline.py` (new)

```python
def test_timeline_events_written_on_successful_extraction():
    """After extraction, case_id returned and timeline events present."""
    ...

def test_timeline_has_vin_validated_event():
    ...

def test_timeline_has_primary_driver_defaulted_event():
    ...

def test_timeline_has_missing_item_when_vin_absent():
    ...

def test_timeline_has_conflict_flag_on_multiple_vins():
    ...

def test_case_persisted_to_postgres_after_extraction():
    """case_id returned by extract endpoint is findable in DB."""
    ...
```

#### Day 1 Acceptance Criteria

- [ ] Extract endpoint returns `case_id` (non-empty string)
- [ ] Extract endpoint returns `timeline_events` list (≥3 events per successful extraction)
- [ ] Case findable in Postgres by `case_id`
- [ ] `lifecycle_status` = `handed_off` for complete packet
- [ ] `lifecycle_status` = `handed_off`, `case_status` = `waiting_client` for missing-item packet
- [ ] All 5 timeline tests pass

---

### Day 2 — UI Timeline + Dry Run

**Goal:** PacketStep shows Timeline; dry run CK-DRY-02 logs timeline to screen.

#### Hour 1–2: UI changes

**File:** `ui/src/pages/AddCarPage.tsx`

1. Add `Timeline` to Ant Design imports
2. Add `TimelineEvent` type and `TimelinePanel` component (see TASK 7 sketch above)
3. Add `case_id: string` and `timeline_events: TimelineEvent[]` to `PacketResponse` type
4. Derive `nextAction` from packet state:
   - If `confirmation_notices.length > 0`: `"Broker confirm primary driver"`
   - If warnings include "VIN": `"Broker verify VIN manually"`
   - Else: `"All fields present — ready to quote"`
5. Render `<TimelinePanel>` inside PacketStep Card, below Copy Packet button

#### Hour 2–3: Dry run

Run CK-DRY-02 end-to-end:

1. Open `/add-car`
2. Enter: Andy Li / 626-555-0001 / 91101
3. Upload: `insurance_card.png` + `smog_check_vir.png`
4. Confirm: Timeline appears in PacketStep with ≥5 events
5. Confirm: `case_id` shown in packet header (e.g., `CK-001`)
6. Confirm: "Next: Broker confirm primary driver" shown at bottom of timeline
7. Confirm: Copy Packet still works cleanly
8. Log result in `docs/trial/P16_TIME_SAVINGS_TRACKER.md`

#### Hour 3–4: Polish + edge cases

- [ ] Timeline renders cleanly with 0 events (hidden, no error)
- [ ] Timeline renders cleanly with 8+ events (no overflow)
- [ ] VIN conflict shown in red (MISSING_ITEM_DETECTED color)
- [ ] All required fields present shown in green (PACKET_READY)
- [ ] Collapsed by default (broker's first view is still the packet)

#### Day 2 Acceptance Criteria

- [ ] Timeline visible in PacketStep (collapsed, expandable)
- [ ] CASE_CREATED event shows customer name + ZIP
- [ ] DOCUMENT_UPLOADED events show filenames
- [ ] AI_EXTRACTED_PACKET event shows model name
- [ ] VIN_VALIDATED event shows VIN value + valid/invalid
- [ ] PRIMARY_DRIVER_DEFAULTED shown in yellow (if applicable)
- [ ] Next Action line shown in blue at bottom
- [ ] Dry run CK-DRY-02 passes all checks

---

## Document Hierarchy

| Priority | Document | Role |
|----------|----------|------|
| 1 | `docs/p16/P16_DECISION_FREEZE_V1.md` | Scope + architecture freeze (SSOT) |
| 2 | **This file** | Timeline + state machine design |
| 3 | `docs/CURRENT_PRODUCT_SHAPE.md` | Runtime + deploy truth |
| 4 | `docs/product_constitution/P16_ADD_CAR_PACKET_FIELD_CONTRACT.md` | Field definitions |

---

*Design authored 2026-06-19. Awaiting GO/NO-GO before any implementation.*  
*SSOT: `docs/p16/P16_DECISION_FREEZE_V1.md`*
