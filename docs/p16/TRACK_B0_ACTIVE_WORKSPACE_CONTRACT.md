# Track B0 — Active Workspace Contract (Chen Kui Demo v1)

**Date:** 2026-07-03
**Status:** Approved for implementation
**Prerequisite:** Track A (WeCom transport/networking) — ✅ accepted (`docs/trial/TRACK_A_ACCEPTANCE_REPORT.md`)
**Does not supersede:** ADR-001 (Readiness) · ADR-002 (No Timeline) · ADR-003 (No Carrier API) · ADR-004 (Channel Adapter Contract) · ADR-005 (Active Case Consolidation)
**Governed by:** `docs/product_constitution/P16_CUSTOMER_FIRST_CONSTITUTION.md` Rule 7 (One Customer = One Active Case) and **Rule 8 (One Business Flow At A Time)** — this contract is the concrete B0 implementation of Rule 8.
**Authority:** This document is the single source of truth for B0 implementation. Where it conflicts with older prose docs, this file wins until they are updated.

---

## 1. North Star

> **A customer's WeChat message becomes a broker-ready draft the moment they ask — and a real case only the moment the broker says yes.**

This is **not** a chatbot (every reply exists to move a request toward broker-ready, not to converse). This is **not** a form (the customer never sees fields or a submit button — just a conversation, with one button when it matters). This is **not** autonomous insurance processing (nothing becomes an active case without explicit broker confirmation). This is **not** a multi-tasking assistant (it advances **one business flow at a time** per customer — Constitution Rule 8; a second topic raised mid-flow is acknowledged and flagged for the broker, never processed alongside the first). It is an **AI workspace** that organizes a customer's chat into something a broker can act on in seconds.

A customer's thread may contain many topics. The AI's job is to help the customer land on **one** flow, stay inside it until it is done, and defer the rest — not to become a smarter system that juggles several at once.

---

## 2. What already exists (do not rebuild)

B0 is small precisely because most of the pipeline is already built and tested:

| Capability | File | Status |
|---|---|---|
| Rule-based intent classification (add_car / claim_intake / policy_review) | `services/fiqa_api/wecom/intent.py` | ✅ Built |
| Phone + VIN extraction from free text | `services/fiqa_api/wecom/identity.py` | ✅ Built |
| Deterministic create/attach/broker_review resolver | `services/fiqa_api/inbox_triage/active_case_resolver.py` | ✅ Built |
| WeCom text → case bridge (create/attach) | `services/fiqa_api/wecom/active_case_bridge.py` | ✅ Built, tested (`tests/test_wecom_active_case.py`) |
| Outbound text + native clickable menu (`msgmenu`) send | `services/fiqa_api/wecom/send_msg.py`, `reply.py` | ✅ Built, env-gated (`WECOM_SLICE_SEND_REPLY`) |
| Broker workbench case list/detail UI | `ui/src/features/intake/components/BrokerWorkbenchTab.tsx` | ✅ Built |
| Lightweight case flags (no new table) | `case_store.update_case_workbench_flags()` | ✅ Built — **this is the pattern B0 reuses** |
| Case status transitions | `case_store.update_case_status()` + `PATCH /cases/{id}/status` | ✅ Built |

**What B0 actually adds:** two gates (explicit Start, explicit Broker Confirm) that don't exist yet, three small field extractors, one boolean-style flag, and one outbound message template.

---

## 3. MVP v1 Scope (exact, buildable)

```
1.  Customer says hello                         → intent=unclear/menu   → no case
2.  Customer expresses add-car intent            → intent=add_car, high  → no case yet
3.  System sends START CARD                      → msgmenu, no case yet
4.  Customer taps "Start"                        → click id = start_add_car
5.  System creates Draft Case                    → case_status=new, broker_confirmed_at=null
                                                     bound to external_userid (see §4.1)
6.  Customer provides VIN/ZIP/date/driver/phone
    naturally, across turns                      → each turn = evidence event
7.  System updates Draft Case                    → collected_fields / still_needed_fields merge
8.  Customer mentions a claim                     → intent=claim_intake inside open add-car thread
9.  System sets claim_mentioned_at (broker only)  → NO new case, NO claim intake flow
10. Broker opens case, clicks "Confirm"           → broker_confirmed_at set
11. Customer receives DONE CARD                   → send_text_reply(), canned bilingual copy
12. No Active Case exists before step 10          → invariant, tested explicitly
```

Steps 8–9 are the concrete proof of Constitution Rule 8 (One Business Flow At A Time): the claim mention is acknowledged and flagged, but the open add-car flow is never paused, branched, or run alongside a second flow.

Everything not required to prove these 12 steps is **out of scope** (§4).

---

## 4. Explicit Out-of-Scope (v1)

| Item | Disposition |
|---|---|
| Timeline UI | Not built (ADR-002 unchanged) |
| New Workspace database table | Not built — reuse `service_records` / case JSON, same as Active Case |
| Generic workflow / rules engine | Not built — one named flag, not a `flags[]` framework |
| Multi-topic conversation splitting | **Not built, and not a v1-only cut — permanent principle.** One open business flow per customer thread at a time (Constitution Rule 8). Additional flow types (claim, policy review, billing, renewal) may be added in later tracks; the "one at a time" discipline does not change when they are. |
| Full claim intake (FNOL) | Not built — claim mention is a **flag only** |
| Media / OCR extraction | Not built — image messages logged as unprocessed evidence at most |
| Proactive follow-up ("Later" button, reminders) | Not built |
| Customer login / verification | Not built — WeCom `external_userid` + phone is identity |
| CRM / household model | Not built |
| Manual Promote (broker force-creates/activates outside resolver) | Not built — would be a resolver bypass |
| "Talk to a broker" escalation button | Not built |
| Full V4/V5 `case_draft_engine.py` reuse in WeCom path | Not built for v1 — see §4.2 decision |

### 4.1 Identity before phone is known (decision)

The existing resolver keys strictly on normalized phone (`resolve_active_case_for_evidence`). But the demo requires a Draft Case to exist **before** the customer has given a phone number (Start press happens before phone).

**Decision:** at Start press, bind the Draft Case to the WeCom `external_userid` (already present on every event) via a new, narrow lookup `find_open_draft_case_by_external_userid()` in `active_case_bridge.py`. This is channel-identity binding, not a resolver change — the phone-based resolver contract (`active_case_resolver.py`) is untouched and still governs cross-channel merge once a phone is known. Once phone arrives, call the existing `update_case_customer()` to attach it, same as today.

**Guardrail:** Broker Confirm is blocked until a phone is present on the case (prevents confirming an unidentifiable case).

### 4.2 Field extraction: adapter-local regex, not the full engine

`wecom/identity.py` already extracts phone and VIN with small, deterministic regexes, explicitly decoupled from `triage.py` ("adapter-local, no triage import"). B0 extends this file with the same pattern for **ZIP, delivery date, and primary driver name only** — not by importing `case_draft_engine.py` (970+ lines, V4/V5 confidence machinery designed for the web flow). Reusing the full engine here is the refactor trap: high coupling, wrong abstraction level, no demo benefit. Revisit after the pilot gate if WeCom needs the same intelligence depth as web.

---

## 5. State Model (additive only — no schema refactor)

Two new fields on the existing case record (JSON file and/or Postgres `extra`, same as `workbench_test`/`workbench_archived`):

| Field | Type | Meaning |
|---|---|---|
| `broker_confirmed_at` | ISO-8601 string \| null | Set once, by broker action only. Presence = "Active Case." Absence = "Draft Case." Immutable once set (mirrors `formal_submitted_at` pattern). |
| `claim_mentioned_at` | ISO-8601 string \| null | Set when `claim_intake` intent is detected inside an open add-car thread. Broker-only visibility. Does not gate or block the add-car flow. |

New function in `case_store.py`, same shape as `update_case_workbench_flags()`:

```python
def update_case_workspace_flags(
    case_id: str,
    *,
    broker_confirmed_at: str | None = None,   # sentinel: pass explicit ISO string to set
    claim_mentioned: bool | None = None,
) -> dict[str, Any] | None:
    ...
```

No new table. No new status enum values required — "Draft" vs "Active" is derived (`broker_confirmed_at is None` vs not), not a `case_status` transition, so it cannot collide with existing queue statuses (`new`, `reviewing`, `waiting_client`, …).

---

## 6. Customer UX Copy

**Start Card** (new `msgmenu`, sent once per detected add-car intent, before any case exists):

```
Head: I can help you add a vehicle to your policy. Want me to start a request for your broker?
      我可以帮您把新车加到保单里。要现在开始一个请求给经纪人吗？
Buttons: [ Start / 开始 ]  [ Not now / 稍后 ]
Tail: Your broker reviews everything before anything changes.
      经纪人会先审核，任何变更前都会确认。
```

- "Start" → click id `start_add_car` → creates Draft Case.
- "Not now" → click id `start_add_car_decline` → no case, no state stored beyond existing intent log. (Do not build a "Later" tracking feature — see §4.)

**Claim mention reply** — reuse existing `_INTENT_REPLIES["claim_intake"]` verbatim (already correct, cautious language). No new customer-facing copy needed for step 8–9; only the broker-side flag is new.

**Done Card** (new, sent once on Broker Confirm):

```
Your request has been reviewed and confirmed by your broker. We'll follow up with next steps.
您的请求已由经纪人审核并确认。我们会跟进后续步骤。
```

---

## 7. Broker UX Requirements

In existing `BrokerWorkbenchTab.tsx` (no new tab/page):

1. Case list: show a **"Draft"** badge when `broker_confirmed_at` is null; no badge (or "Active") once set. Reuses existing badge rendering pattern (`quote_ready_status` already renders similarly).
2. Case detail: show a **"⚠ Claim mentioned"** banner when `claim_mentioned_at` is set — broker-only, not sent to customer, not a separate case.
3. Case detail: one new **"Confirm"** button.
   - Disabled/tooltip if phone is missing (§4.1 guardrail).
   - On click → `PATCH` sets `broker_confirmed_at` + triggers Done Card send.
   - Irreversible in v1 (no "unconfirm") — matches `formal_submitted_at` immutability precedent.

---

## 8. Persistence Rules

- Same store as all existing cases: JSON file (dev/demo) and/or Postgres `service_records.extra` (pilot), per existing `UNIFIED_INTAKE_*` flags. **No new table, no new migration.**
- `broker_confirmed_at` and `claim_mentioned_at` follow the same dual-write/read rules as `workbench_test`/`workbench_archived`.
- Evidence events (`evidence_events[]`) already append-only; no change.

---

## 9. Trigger Rules

| Trigger | Condition | Action |
|---|---|---|
| Send Start Card | `intent=add_car`, confidence=high, **no open Draft/Active case exists for this `external_userid`** | `send_menu_reply()`, no case created |
| Create Draft Case | click id `start_add_car` received | Bind to `external_userid`; `case_status=new`; `broker_confirmed_at=null` |
| Attach evidence | message from `external_userid`/phone with an open, unconfirmed case | Extract phone/VIN/ZIP/date/driver → merge into `collected_fields`/`still_needed_fields` |
| Set claim flag | `intent=claim_intake` **and** an open add-car case already exists for this identity | `update_case_workspace_flags(claim_mentioned=True)`; send existing safe claim reply; do **not** create a case |
| Broker Confirm | broker clicks Confirm **and** case has a valid phone | `update_case_workspace_flags(broker_confirmed_at=<now>)` → `send_text_reply()` Done Card |
| Block | any attempt to set `broker_confirmed_at` without a phone on the case | Reject with 400, workbench shows why |

---

## 10. Acceptance Tests

Add to `tests/test_wecom_active_case.py` (extend, do not fork a new test module):

1. `test_hello_message_creates_no_case` — small talk → no Start Card, no case.
2. `test_add_car_intent_sends_start_card_no_case` — high-confidence add_car → menu sent, `count_stored_cases() == 0`.
3. `test_start_click_creates_draft_case_without_phone` — `start_add_car` click, no phone yet → case created, `broker_confirmed_at is None`, bound to `external_userid`.
4. `test_followup_messages_merge_into_same_draft` — VIN, then ZIP, then phone, then driver name across 4 turns → one case, `collected_fields` accumulates, no duplicate case.
5. `test_claim_mention_flags_without_new_case` — claim message inside open draft → `claim_mentioned_at` set, `count_stored_cases()` unchanged, no claim-lane case fields added.
6. `test_broker_confirm_blocked_without_phone` — confirm attempt on phone-less case → rejected.
7. `test_broker_confirm_sets_flag_and_sends_done_card` — confirm with phone present → `broker_confirmed_at` set, `send_text_reply` called once with Done Card copy.
8. `test_no_active_case_before_confirm` — assert `broker_confirmed_at is None` at every step 1–9 of the scripted scenario; only true after step 10.
9. `test_decline_start_creates_nothing` — "Not now" click → no case, no crash, no stored "later" state.

All must pass under `bash scripts/guardrail_inbox_triage.sh` equivalent for WeCom (extend `scripts/track_a_e2e_acceptance.py` or add a `track_b0_e2e_acceptance.py` sibling — reuse the Track A script's structure).

---

## 11. Rollback Strategy

- New behavior gated behind `WECOM_B0_ACTIVE_WORKSPACE=1` (default off). When off, current Track A behavior (immediate case creation on phone+intent, no Start Card, no Confirm gate) is unchanged.
- Rollback = unset the flag. No data migration needed since new fields are additive and nullable.
- If Start Card causes customer confusion mid-pilot, disabling the flag reverts to today's proven auto-create path without touching `active_case_resolver.py` or `case_store.py` schemas.

---

## 12. Implementation Milestones

See Part 5 below (kept in this doc for implementers; summarized in the review chat).

| Milestone | Purpose |
|---|---|
| B0.1 | Start Card send + click handling (no case yet) |
| B0.2 | Draft Case creation on Start, bound to `external_userid`; extend `identity.py` with ZIP/date/driver extractors |
| B0.3 | Broker Confirm button + Done Card send |
| B0.4 | Claim mention flag (broker-only) |
| B0.5 | Demo polish + acceptance tests (§10) |

B0.4 is not a scoped-down placeholder for a future "real" concurrent claim flow — flag-only is the permanent shape of a second topic under Rule 8. If a claim flow is built in a later track, it becomes its own flow that a customer can only enter once the add-car flow reaches a terminal state (or the broker splits/closes it), not a parallel track running today.

---

## 13. Guardrails (hard rules for this track)

- No new database table.
- No Timeline UI.
- No full claim intake / FNOL flow.
- No media/OCR extraction.
- No autonomous policy update of any kind.
- No customer login or verification.
- No broker bypass of the resolver (`active_case_resolver.py` remains the only path to create/attach a case).
- No Active Case (`broker_confirmed_at` set) before explicit broker confirmation — tested explicitly (§10.8).
- No case created from small talk or ambiguous/low-confidence intent.
- No claim case, and no parallel claim flow, created from a claim mention — flag only, permanently (Constitution Rule 8), not a v1-only cut.
- No changes to Track A networking (static IP, NAT, VPC egress) — this track is application logic only, deployed on top of the accepted Track A transport.
- No refactor of `case_store.py` or `active_case_resolver.py` internals — only additive functions following existing patterns (`update_case_workbench_flags` → `update_case_workspace_flags`).

---

*Related: `docs/trial/TRACK_A_ACCEPTANCE_REPORT.md` · `docs/p16/adr/ADR_004_ENTERPRISE_WECOM_CHANNEL_INTEGRATION.md` · `docs/p16/adr/ADR_005_ACTIVE_CASE_CONSOLIDATION.md` · `docs/p16/adr/ADR_002_NO_TIMELINE_V1.md` · `services/fiqa_api/wecom/active_case_bridge.py` · `tests/test_wecom_active_case.py`*
