# Add-Car Flow Deep Dive — Flagship Path

**Goal:** Explain add-car **start → extract → state → reply → handoff → post-handoff** in plain language, with a clear **code vs config vs UI** split.

---

## 1. How Add-Car starts

| Trigger | Where |
|---------|--------|
| Customer text matches **add vehicle** intent | `_is_add_vehicle_request` in `triage.py` uses merged conversation text (lower-cased) plus markers from `configs/industries/insurance/markers.json` (with `_FALLBACK_MARKERS` if needed). |
| **Quick-start button** “获取报价” | UI sends `soft_route: "add_car"` with a starter message; `routes/inbox_triage.py` can reroute if text conflicts (`REROUTE_MESSAGES`, `SOFT_ROUTE_STARTER_REPLIES`). |

**Category note:** Under LLM/rule triage, add-car often surfaces as `customer_question` with add-vehicle markers — special cases in `triage_conversation` then treat it as the quote workflow.

---

## 2. How fields are extracted

**Function:** `_extract_add_car_fields(merged_text)` in `triage.py`.

- Parses **only `[客户]` segments** from the merged thread.
- **Heuristic signals:** year regex (`20[12][0-9]`), CA zip helpers, long **make/model keyword lists** (EN + 中文), delivery/pickup markers, driver markers (`_text_has_add_car_driver_signal`), VIN pattern, add-to-existing vs new-customer flags, additional drivers / “only me.”

**Concrete vehicle string** for broker summaries: `_extract_add_car_vehicle_concrete` + `_is_add_car_vehicle_correction_signal` so **corrections** (e.g. X5 → X3) override earlier bubbles.

**Contact (lite):** `_extract_contact_fields` adds name/phone when regex matches.

**Config role:** **Not** the slot definitions — those are code. Config supplies **next-step question wording** for three keys via `get_add_car_rules()` → `configs/industries/insurance/add_car_rules.json` (`ask_vehicle`, `ask_zip`, `ask_delivery_driver`).

> **Eng accuracy note:** The repo’s `add_car_rules.json` may list **`ask_driver_only`**, but `config_loader.get_add_car_rules()` currently **only** copies the three keys above into the dict passed to triage. `_get_next_ask_for_add_car` still supports `ask_driver_only` when present (e.g. preview override). If product wants that string editable from disk, extend `get_add_car_rules` / `save_add_car_rules` to include it.

---

## 3. How state advances

**No separate state machine library.** Progress is derived each request from:

1. **Merged conversation text**
2. **Customer turn count**
3. **`_add_car_enough_for_handoff(fields)`** — vehicle (year+model or VIN) + zip + (delivery **or** driver)
4. **`_should_handoff`** — generally hand off after 2+ customer turns if still `manual_followup_needed`, with an exception for **single-turn** add-car when slots are already full

**Exposed fields** (for UI / broker):

- `collected_fields` / `still_needed_fields` from `_add_car_structured_fields`
- `quote_ready_status`: `quote_ready` | `almost_ready` | `need_more`
- `collection_stage`, `lifecycle_status`, `follow_up_type`, `next_best_question` (when not handed off, the “next ask” often becomes client-visible draft)

**Turn-2 nuance:** `_get_next_ask_for_add_car` may ask for **driver only** when delivery exists but driver missing — unless doc clarification, coverage side-question, or “materials sent” patterns say “hand off now.”

---

## 4. How the customer reply is generated

| Phase | Mechanism |
|-------|-----------|
| Base draft | From `_rule_based_triage` / `_llm_triage` → `client_reply_draft` |
| Collecting | `would_handoff && next_ask` → **not** handoff; `result_draft` = composed **acknowledgement + config ask** (`_get_add_car_acknowledgement`, `_get_prospective_send_materials_lead`, `add_car_rules`) |
| Handoff | Replace draft with **handoff phrase** keyed by `add_car` from `handoff_phrases.json`, with **hardcoded fallbacks** in `triage.py` |
| Patches | Same function applies add-car-specific **suffixes** and **leads** (doc clarification, coverage question, materials sent, vehicle correction prefix) |

**Language:** `_detect_client_language` / `_contains_chinese` on merged text.

---

## 5. How handoff works

- **`handoff_ready: true`** when the orchestration decides the broker/office should take over.
- **Customer-facing line** prefers client config: `configs/clients/chen_kui/handoff_phrases.json` → `handoff.add_car` (`zh` / `en`).
- **Broker-facing line** `broker_next_step` is **rewritten** for add-car when slots are sufficient — e.g. “Run quote for {vehicle}…”, materials-sent branch “Verify materials received…”, plus contact hints.

---

## 6. Post-handoff continuation / boundary

| Mechanism | Where |
|-----------|--------|
| Append API | `triage_for_append` → always treats append as broker-facing update; sets `handoff_ready` true; runs `_apply_append_case_boundary` |
| Boundary classification | `_classify_append_case_boundary` — compares **prior case domain** (inferred from `source_text`) vs **domains in last message**; add-car thread has **special cases** (coverage questions, short slot fills stay same case) |
| UI | Post-handoff panels (“same request” vs new issue) driven by `case_boundary` + `ui_copy.json` strings; `UnifiedIntakePage.tsx` |

---

## 7. Code vs config vs UI (add-car)

| Concern | Code (`triage.py`) | Config | UI |
|---------|-------------------|--------|-----|
| Intent / markers | Detection helpers + fallbacks | `markers.json` | Button `soft_route` |
| Slot extraction | Regex / keyword lists | — | — |
| Ask **order** | Hardcoded priority | — | — |
| Ask **wording** | Fallback strings | `add_car_rules.json` | — |
| Handoff **wording** | Fallback strings | `handoff_phrases.json` | Toasts / closure copy from `ui_copy.json` |
| Transaction chrome | — | `ui_copy.json` | Ribbons, progress card, submit label |
| Broker next step text | Tailored branches | — | Display only |

---

## 8. Founder takeaway

Add-car is **strong** because the **commercial edge cases** (correction, materials sent, doc question in same turn, coverage side question) are **explicitly coded** next to the handoff decision — but that strength is also why **`triage.py` is long**: the flagship flow’s “policy” is **mostly in Python**, not in a declarative workflow file.
