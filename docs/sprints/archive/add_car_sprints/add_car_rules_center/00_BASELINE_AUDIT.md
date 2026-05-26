# Baseline Audit — Add-Car Quote Flow

**Sprint:** Minimal Business Rules Center for Add-Car Quote  
**Purpose:** Document current Add-Car logic, what is hardcoded, what is config-driven.

---

## 1. Where Add-Car Quote Logic Lives

| Location | Purpose |
|----------|---------|
| `services/fiqa_api/inbox_triage/triage.py` | Core logic: `_get_next_ask_for_add_car`, `_add_car_enough_for_handoff`, `_extract_add_car_fields`, `_add_car_structured_fields`, `_get_add_car_acknowledgement` |
| `_build_client_reply_draft` (triage.py ~506–545 zh, ~650–688 en) | First-turn reply; uses `templates.get("add_car")` but has many inline branches |
| `configs/industries/insurance/reply_templates.json` | add_car.zh, add_car.en (first reply fallback) |
| `configs/clients/chen_kui/handoff_phrases.json` | add_car.zh, add_car.en (handoff message) |
| `configs/clients/chen_kui/reply_overrides.json` | Optional overrides (empty) |

---

## 2. What Is Hardcoded

| Item | Location | Hardcoded Value |
|------|----------|-----------------|
| Ask vehicle (zh) | `_get_next_ask_for_add_car` | "先把年份和车型发我，我就能帮你算。" |
| Ask vehicle (en) | " | "Send me the year and make/model first so I can run the quote." |
| Ask zip (zh) | " | "先把地址邮编发我，我就能帮你算。" |
| Ask zip (en) | " | "Send me the zip or address first and I will run the quote." |
| Ask delivery/driver (zh) | " | "提车日期和主要驾驶人发我一下，我好安排报价。" |
| Ask delivery/driver (en) | " | "Send me the delivery date and main driver so I can prepare the quote." |
| First-turn branches | `_build_client_reply_draft` | 6+ inline branches (vehicle_ok+no zip, vehicle_ok+zip+no delivery, etc.) with hardcoded strings |
| Handoff threshold | `_add_car_enough_for_handoff` | vehicle + zip + (delivery or driver) |

---

## 3. What Is Already Config-Driven

| Item | Config | Used |
|------|--------|------|
| add_car first reply (zh/en) | reply_templates.json | `templates.get("add_car")` — used as fallback when no inline branch matches |
| add_car handoff message | handoff_phrases.json | Used when handoff_ready |

---

## 4. Classification (Easy / Risky / Locked)

| Item | Classification | Notes |
|------|----------------|-------|
| First reply (zh/en) | ✓ Easy | Already in reply_templates; UI can edit via overrides |
| Next-step prompts (ask_vehicle, ask_zip, ask_delivery_driver) | ✓ Easy | Add new config; triage reads from config |
| Handoff message | ✓ Easy | Already in handoff_phrases |
| Collection order | Locked | Logic in code; changing requires refactor |
| Handoff threshold | Locked | `_add_car_enough_for_handoff`; business risk if changed |
| Extraction logic | Locked | Regex patterns |

---

## 5. Biggest Current Weakness

**Next-step prompts are fully hardcoded.** Business users cannot change "先把年份和车型发我" or "先把地址邮编发我" without a code change. The first reply is partially configurable (reply_templates) but the progressive-ask logic in `_build_client_reply_draft` has many inline branches that override the template.

---

## 6. Realistic First Externalization

1. **Add `add_car_rules.json`** — ask_vehicle, ask_zip, ask_delivery_driver (zh/en)
2. **Update `_get_next_ask_for_add_car`** — read from config; fallback to hardcoded
3. **Rules Center UI** — edit these + first reply + handoff; preview via triage API

---

*End of baseline audit*
