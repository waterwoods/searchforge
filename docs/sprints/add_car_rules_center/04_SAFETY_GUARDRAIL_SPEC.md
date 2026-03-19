# Safety / Guardrail Spec

**Sprint:** Minimal Business Rules Center for Add-Car Quote  
**Purpose:** Define what remains locked, what business users may edit, and how to avoid breaking.

---

## 1. What Remains Locked in Code

| Area | Locked | Reason |
|------|--------|--------|
| Collection order | ✓ | Logic in `_get_next_ask_for_add_car`; changing would require code |
| Handoff threshold | ✓ | `_add_car_enough_for_handoff`; vehicle+zip+(delivery/driver) |
| Extraction logic | ✓ | Regex patterns in `_extract_add_car_fields` |
| Intent detection | ✓ | Markers in config; not in Rules Center scope |
| Storage/security | ✓ | Case store, API auth |

---

## 2. What Business Users May Edit

| Field | Editable | Validation |
|-------|----------|------------|
| First reply (zh/en) | ✓ | Max length 500 chars |
| Ask vehicle (zh/en) | ✓ | Max length 200 chars |
| Ask zip (zh/en) | ✓ | Max length 200 chars |
| Ask delivery/driver (zh/en) | ✓ | Max length 200 chars |
| Handoff (zh/en) | ✓ | Max length 500 chars |

---

## 3. Draft vs Publish Model

- **Draft:** Editable in UI; saved to draft storage or localStorage
- **Preview:** Uses draft rules; does not affect live API
- **Publish:** Copies draft → published; live API uses published
- **Restore:** Copies last published → draft; discards draft changes

---

## 4. Revert / Rollback Behavior

- **Restore:** One-click restore to last published version
- **No version history** in v1 (single published version)

---

## 5. How to Avoid Breaking Existing Flow Quality

- **Validation:** Empty strings fall back to defaults
- **Preview first:** Always preview before publish
- **Sanity check:** Publish button shows confirmation
- **Fallback:** If config fails to load, backend uses hardcoded defaults

---

*See also: 03_ADD_CAR_RULES_DATA_MODEL.md*
