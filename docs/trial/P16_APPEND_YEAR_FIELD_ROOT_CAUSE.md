# P16 — Append Year Field Root Cause

**Sprint:** P16-CUSTOMER-FIRST-CASE-REHYDRATION-ROOT-CAUSE-SPRINT  
**Issue:** Standalone year supplement (`2027`) does not clear **年份** from Still Needed  
**Date:** 2026-06-07

---

## Symptom

Customer flow:

1. `我刚刚买了一台二零二五年的宝马X5，提车日是七月一号二零二六年。`
2. System asks for year (and other slots).
3. Customer replies `2027`.
4. UI / active-case still shows **年份** in `still_needed_fields`.

Live API evidence (`case_9a86a610fb66`, phone `6265550888`):

- After turn 2: `collected_fields` lacks `year`; `still_needed_fields` still includes `year`.
- Persisted case: `collected_fields: []`, `still_needed_fields` unchanged from draft.

---

## Investigation answers

| # | Question | Answer |
|---|----------|--------|
| 1 | Does backend recognize `2027` as year? | **Partially.** Rule layer `text_has_vehicle_year_signal("2027")` → `True`. Structured path still drops it. |
| 2 | Does it reject 2027 as out-of-range? | **No.** Regex `20[12][0-9]` accepts 2027. No future-year cap in guardrails. |
| 3 | Does it overwrite earlier 2025? | **N/A.** Chinese `二零二五年` never becomes a collected year (no ASCII match). |
| 4 | Does append result include year in `collected_fields`? | **No** — live turn 2 and `triage_for_append` local harness. |
| 5 | Does `still_needed_fields` remove year? | **No.** |
| 6 | Is frontend using stale `still_needed_fields`? | **No.** Frontend renders API truth; stale data is because **backend never collects year** and **triage does not persist field updates** to the case row during collecting. |
| 7 | Backend vs frontend? | **Backend** — extraction + strict truth guardrails. Frontend is faithful to API response. |

**Classification:** Backend extraction + truth guardrails (+ secondary: Chinese year numerals unsupported in rule layer).

---

## Root cause chain

### Cause A — Chinese model year not detected on turn 1 (feeds the ask)

`text_has_vehicle_year_signal` only scans ASCII `20[12][0-9]`:

```136:139:services/fiqa_api/inbox_triage/add_car_vehicle_signals.py
def text_has_vehicle_year_signal(t: str) -> bool:
    """True when a 20xx token appears in a non-calendar-date context (vehicle model year)."""
    cleaned = _strip_likely_calendar_dates_for_year_scan(t)
    return bool(re.search(r"(?<![0-9])(20[12][0-9])(?:\s*款)?(?![0-9])", cleaned))
```

`二零二五年` → **False**. Turn 1 collects `make_model` (宝马/X5) but not `year` → system correctly asks for year from customer perspective, but the stated 2025 was ignored.

### Cause B — Standalone `2027` blocked by strict truth guardrails (primary defect)

Rule extraction sets `year=True` for merged text containing `2027`. Guardrails then **zero** the flag:

```571:572:services/fiqa_api/inbox_triage/truth_field_guardrails.py
    if fn == "year":
        return False, "no_explicit_vehicle_identity", "no_explicit_vehicle_identity"
```

Year acceptance requires **both**:

```497:500:services/fiqa_api/inbox_triage/truth_field_guardrails.py
    if fn == "year":
        if utterance_has_explicit_vehicle_identity(last_seg) and text_has_vehicle_year_signal(last_tl):
            return True, "explicit_literal_current_turn"
        return False, None
```

`utterance_has_explicit_vehicle_identity("2027")` is **False** because a lone year token has no make/model/VIN cue:

```154:166:services/fiqa_api/inbox_triage/add_car_vehicle_signals.py
def utterance_has_explicit_vehicle_identity(text: str) -> bool:
    ...
    if text_has_vehicle_year_signal(tl) and text_has_vehicle_make_model_signal(tl):
        return True
    if text_has_vehicle_make_model_signal(tl):
        return True
    return False
```

Thread-level fallback also fails for bubble `2027` (year signal yes, make/model signal no). Bubble 1 has make/model but **no ASCII year signal** (Chinese numerals).

Result in `_add_car_structured_fields`:

```5748:5751:services/fiqa_api/inbox_triage/triage.py
        vehicle_ok = (fields.get("year") and fields.get("model")) or fields.get("vin")
        if not vehicle_ok:
            still_needed.extend(["year", "make_model"])
```

`fields["year"]` is False after guardrails → `year` stays in `still_needed_fields`.

### Cause C — Triage with `case_id` does not persist field updates to Postgres/JSON

During collecting, `POST /api/inbox/triage` with `case_id` returns updated `collected_fields` / `still_needed_fields` in the **HTTP response only**. It does **not** call `append_follow_up_message` or otherwise write slot lists to the service record.

Live proof: after two triage turns, `GET /api/inbox/cases/{id}` shows `collected_fields: []` and draft-default `still_needed_fields`.

`active-case` reads the **persisted** row → still shows year missing even if a future fix corrected the triage response object.

---

## Append merge audit

`_merge_append_field_lists` (case_store) is **not** the failure point — triage never produces `year` in `new_collected` for this scenario.

`_compute_add_car_collected_still_lists` → `_add_car_structured_fields` → `_extract_add_car_fields_truth_safe` → guardrails reject year before lists are built.

---

## Database evidence

| Store | After turn 2 (`2027`) |
|-------|------------------------|
| `service_records` / JSON case | `collected_fields: []` |
| `still_needed_fields` | Draft defaults (includes `year`) |
| `case_messages` | 1 row — draft starter only |
| `source_text` | `[客户] 开始加车申请（Customer First 入口）` |

No year value is persisted anywhere.

---

## UI evidence

- `CustomerFirstEntryScreen` → `StillNeededList` renders `active_case.still_needed_fields` from `GET /api/inbox/customer/active-case` — shows 年份.
- `CustomerEntryTab` triage bubbles use latest `triageResult.still_needed_fields` from `/api/inbox/triage` — also shows 年份 after turn 2.
- No frontend cache bug identified; labels from `customerStatusSurfaceFieldLabel("year")` → 年份.

---

## Severity

**P1**

| Dimension | Impact |
|-----------|--------|
| Customer trust | High — customer answered; system still asks |
| Office trust | Medium — broker sees incomplete vehicle year |
| Broker trust | Medium — quote lane blocked on year |
| First pilot readiness | Blocks realistic Chinese intake |
| North Star | Violates “customer message → structured case” for year slot |

Not P0: add-car lane still functions; customer can retry with year+model in one line. Not P2: blocks core collecting loop for Chinese-speaking customers.

---

## Minimal fix options (do not implement in this sprint)

### Recommended (low risk, constitution-safe)

**Fix B1 — Accept standalone year on supplement turns**

In `truth_field_guardrails.py` `_current_turn_explicit_accepts_field` for `year`:

- If last bubble matches `^20[12][0-9]$` (optional 款) **and** thread already has make/model collected or mentioned → accept as `explicit_year_supplement`.

Keeps strict-truth bar for greenfield noise; allows Customer First “ask then answer” pattern.

**Fix B2 — Chinese year numerals in rule layer**

Map `二零二[零一二三四五六七八九]年` → ASCII year in `text_has_vehicle_year_signal` or pre-normalization step. Fixes turn 1 for the reported scenario (customer said 2025, not only 2027).

### Secondary (persistence alignment)

**Fix C — Persist collecting-phase slot updates when `case_id` is bound**

On `/api/inbox/triage` when `effective_case_id` is set and `append_allowed`:

- Call `append_follow_up_message` (or lightweight field patch) so `collected_fields` / `still_needed_fields` / `case_messages` land on the service record.

Required for active-case phone return to reflect turn-2 truth (pairs with Issue 2).

### Not recommended

- Broad LLM slot layer expansion (scope / token cost).
- Frontend-only hide of 年份 (masks backend truth).
- Removing strict truth guardrails globally.

---

## Recommendation

Ship **B1 + B2** together (extraction + guardrail, ~1 day). Add **C** as paired fix for phone-return status accuracy (~1 day, overlaps Issue 2).

**Root cause statement:** Standalone ASCII year supplements are rejected by `should_accept_field` (`no_explicit_vehicle_identity`); Chinese year text is invisible to the year regex; collecting-phase triage does not persist slot progress to the case row.
