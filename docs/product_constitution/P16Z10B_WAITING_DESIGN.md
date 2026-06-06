# P16-Z10B Phase 2 — Waiting-On Heuristic Design

**Date:** 2026-06-02  
**Constraint:** Extend `triage.py` only · suggest-only · no auto-PATCH

---

## Design principle

Emit optional `suggested_waiting_on` on triage/append results. Broker (or assistant SOP) confirms via existing `update_case_follow_up()` PATCH. Values match `CASE_WAITING_ON_VALUES`: `none`, `client`, `broker`, `carrier`, `underwriting`.

Mission label `office` → production value **`broker`**.

---

## Phrase → value mapping

### `carrier`

| Language | Examples |
|----------|----------|
| Chinese | 保险公司还没回复 · adjuster还没联系我 · carrier那边有回复吗 · carrier确认恢复了吗 · 对方保险拖 |
| English | carrier has not responded · waiting for adjuster · still no adjuster · Did carrier accept · roof leaking / escalate |

### `underwriting`

| Language | Examples |
|----------|----------|
| Chinese | UW还有别的要求吗 · 核保还在 |
| English | UW still reviewing · waiting for underwriting · update from underwriting or billing |

**Disambiguation:** If adjuster/carrier tokens present with UW phrase → **carrier** wins.

### `client`

| Language | Examples |
|----------|----------|
| Chinese | 还缺什么材料 · 材料还没 |
| English | customer has not replied · waiting for documents · send me (with still_needed) |

Also: non-empty `still_needed_fields` for photos/VIN/name + “还缺/still need” language.

### `broker` (office)

| Language | Examples |
|----------|----------|
| Chinese | quote出来了吗 · refund什么时候 · 便宜方案 |
| English | waiting for quote · waiting for refund · when will it take effect |

### Status pings (Day 3)

| Pattern | Routing |
|---------|---------|
| “有回复吗 / any update” + payment/lapse context | `carrier` |
| Same + underwriting category | `underwriting` |
| Same + adjuster/carrier in thread | `carrier` |

---

## Priority order

1. Carrier markers (unless pure UW-only ping)  
2. Underwriting markers / `underwriting_followup` category  
3. Client markers / still_needed  
4. `verify_carrier_received` in still_needed → carrier  
5. Broker/office markers  
6. Status-ping fallback by category  

Empty string → omit field (broker leaves `none`).

---

## Non-goals (Z10B)

- No `next_contact_by` suggestion  
- No auto-PATCH on triage accept  
- No WaitingOnEngine service  
- No UI modal (“谁在等谁?”)  

---

## Acceptance target

Role D waiting battery: **≥7/9** phrases → **9/9 achieved** in validation.
