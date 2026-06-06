# P16-Z7 Phase 6 — Waiting-On Simulation

**Date:** 2026-06-02  
**Scope:** `waiting_on` responsibility tracking — customer · carrier · office  
**Method:** Desk review of case lifecycle + Role D journey language + engine behavior  
**Constraint:** No code changes — validation only

---

## System model

| Value | Meaning | Set by |
|-------|---------|--------|
| `client` | Waiting on customer materials/payment | Broker manual PATCH |
| `carrier` | Waiting on insurer/UW/adjuster | Broker manual PATCH |
| `office` | Waiting on broker/back-office action | Broker manual PATCH |
| `none` | No explicit wait state | Default |

**API:** `update_case_follow_up(case_id, waiting_on, next_contact_by)` in `case_store.py`  
**UI:** Follow-up editor in `BrokerWorkbenchTab.tsx` (collapsed; not auto-filled from triage)

**Triage engine does not emit `waiting_on`** — responsibility must be inferred by broker.

---

## Simulated scenarios (from Role D journeys)

| Journey | Day | Client language | Correct waiting_on | Engine suggests? | Broker must set? |
|---------|-----|-----------------|-------------------|------------------|------------------|
| D01 | 3 | carrier还没回复吗 | **carrier** | ❌ | **Yes** |
| D02 | 3 | update from underwriting or billing | **carrier** | ❌ | **Yes** |
| D03 | 3 | UW还有别的要求吗 | **carrier** or **client** | ❌ | **Yes** |
| D04 | 3 | Did carrier accept forms? | **carrier** | ❌ | **Yes** |
| D05 | 3 | adjuster有联系我吗 | **carrier** | ❌ | **Yes** |
| D06 | 3 | quote出来了吗 | **office** | ❌ | **Yes** |
| D07 | 3 | refund什么时候 | **office** | ❌ | **Yes** |
| D08 | 3 | 有便宜方案了吗 | **office** | ❌ | **Yes** |
| D10 | 3 | carrier确认恢复了吗 | **carrier** | ❌ | **Yes** |

**Auto-detection: 0/9** — broker or assistant must manually select waiting party.

---

## Claims battery (waiting language)

| Case | Waiting signal | Expected | Auto? |
|------|----------------|----------|-------|
| CL04 | adjuster still no / roof leaking | carrier | ❌ |
| CL05 | other insurance dragging | carrier | ❌ |
| CL10 | rental extension / carrier says total loss | carrier | ❌ |
| CL03 | adjuster还没联系我 | carrier | ❌ |

P16-Z6 noted: **`waiting_on: carrier` never auto-set** — confirmed in Z7.

---

## Three-party tracking assessment

| Party | Can system track? | Evidence in product |
|-------|-------------------|---------------------|
| **waiting_on customer** | ⚠️ Partial | `still_needed_fields`, client draft — broker must map to `client` |
| **waiting_on carrier** | ❌ Manual only | No triage→carrier link; D01/D04/D05 language ignored |
| **waiting_on office** | ⚠️ Partial | `broker_next_step` implies office work; not synced to `waiting_on` |

**Queue filter:** `waiting_on === 'client'` count exists in workbench — useful **if** broker maintained field.

---

## UX friction (P16-Z4/Z5 carryover)

| Issue | Impact |
|-------|--------|
| Follow-up editor collapsed | Broker skips responsibility tagging |
| No post-append prompt “谁在等谁?” | Day 3 pings look like new work |
| `tracking_summary` uses waiting_on OR latest text | Good display **if** set — garbage in, garbage out |
| No carrier-delay template in next action | CL04-style anxiety → generic step |

---

## TOP 5 waiting_on gaps

1. No triage heuristic → `carrier` on adjuster/UW/carrier-delay phrases  
2. No triage heuristic → `client` on “还缺材料” with still_needed  
3. No triage heuristic → `office` on quote/refund/office-confirm phrases  
4. `next_contact_by` not suggested from deadline in summary  
5. Activity log does not record “responsibility changed” prominently

---

## TOP 5 waiting_on strengths

1. Data model + PATCH API **production-ready**  
2. Valid values enforced in `case_store`  
3. Queue can filter `waiting_on: client`  
4. `getCaseTrackingSummary()` surfaces label when set  
5. Zero new infra needed for **manual** pilot discipline

---

## Phase 6 verdict

**Can the system track responsibility correctly?**

> **If broker sets it: Yes.**  
> **If relying on paste/append alone: No** — engine never assigns `waiting_on`.

**3-day case risk:** Day 3 “any update?” messages **look like new urgency** but are **wait-state checks** — without `waiting_on: carrier`, queue prioritization wrong.

**Pilot recommendation:** Assistant SOP: after append with carrier/adjuster language → set `waiting_on` + `next_contact_by` (1 day). Auto-suggest is **highest ROI non-UI engine tune** for Z8.
