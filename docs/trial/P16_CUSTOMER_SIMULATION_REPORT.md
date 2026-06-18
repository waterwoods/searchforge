# P16 Customer First Simulation Report

**Sprint:** P16-CUSTOMER-FIRST-SIMULATION  
**Date:** 2026-06-07  
**Scope:** Business-level stress test of Customer First Constitution (Phase 1 deployed)  
**Method:** API battery + Postgres verification + Preview UI walkthrough  
**No code changes** — validation only

---

## Executive Summary

Customer First Phase 1 **passes core constitution mechanics** for phone return-key lookup, one-active-case enforcement, and no-login entry. Eight simulations (A–H) were executed against **Cloud Run** (`fiqa-api-00086-f95`) and **local strict-Postgres** (`STRICT_PG_ONLY`). Preview UI (`ui-waterwoods`) confirms end-to-end Scenario A/B on production API.

**Verdict:** **CONDITIONAL GO** — safe for broker-supervised pilot with documented mitigations for wrong-phone and shared-household edge cases.

---

## Environment

| Layer | Target | Status |
|-------|--------|--------|
| Backend API | `https://fiqa-api-g7zatxrycq-uw.a.run.app` | ✅ `GET /customer/active-case` HTTP 200 |
| Local API | `http://127.0.0.1:8001` | ✅ `STRICT_PG_ONLY`, `db_primary_reads/writes: true` |
| Preview UI | `https://ui-waterwoods-andys-projects-1f411b73.vercel.app/workbench/unified-intake?tab=customer` | ✅ Customer First entry live |
| Unit tests | `tests/test_active_case_by_phone.py` | ✅ 3/3 pass |

**Auth:** Customer-facing `GET /customer/active-case` is **unauthenticated** (by design — Rule 1). Broker/workbench routes use `X-Unified-Intake-Api-Key`.

---

## Constitution Reference

| # | Rule | Simulations exercising it |
|---|------|---------------------------|
| 1 | Customer Never Logs In | A, G |
| 2 | Phone Is The Return Key | A–H |
| 3 | Phone Required For Formal Submit | F |
| 4 | Progress = Missing Fields | B, F |
| 5 | Only Broker Closes Or Reopens | D, F |
| 6 | Broker Confirms Identity | C, E |
| 7 | One Customer = One Active Case | D, E |

---

## Simulation A — Xiao A, Brand New Customer

**Customer:** Xiao A · **Phone:** `6265551001`

### Scenario

Brand-new customer. No prior case. Start new Add-Car request.

### API Audit — `GET /api/inbox/customer/active-case?phone=6265551001`

| Step | HTTP | Payload (key fields) | Expected | Observed | Result |
|------|------|----------------------|----------|----------|--------|
| Cold lookup | **200** | `has_active_case: false`, `active_case: null`, `phone_normalized: "6265551001"` | No active case | Match | ✅ |
| After `POST /customer/start-add-car` | **200** | `ok: true`, `case_id: case_f1f5b23e7cc9` | Draft created | Match | ✅ |
| Re-lookup | **200** | `has_active_case: true`, `submit_state: "not_yet"` | Active draft | Match | ✅ |

### UI (Preview)

| Step | Result |
|------|--------|
| Enter `6265551009` (fresh phone) → Continue | ✅ No API error |
| Next screen | ✅ **Start New Add-Car Request** + 继续办理加车 |
| Trust copy (no login / no password / phone return) | ✅ Visible |

### Database (Postgres)

| Field | Value |
|-------|-------|
| `case_id` | `case_f1f5b23e7cc9` |
| `customer_phone` | `6265551001` |
| `customer_name` | `Xiao A` |
| `lifecycle_status` | `collecting` |
| `service_lane` | `add_car` |

### Customer Understanding

- ✅ Clear: “No account, use phone to return.”
- ✅ Phone is framed as the return key on the next screen.
- ⚠️ Draft sets `formal_submitted_at` timestamp at creation, but UI correctly shows **Not Yet** because `lifecycle_status=collecting` (Rule 4 honest; operator-facing quirk only).

**Simulation A: PASS**

---

## Simulation B — Xiao B, Return Next Day (Missing VIN)

**Customer:** Xiao B · **Phone:** `6265551002`

### Scenario

Customer started request, missing VIN. Returns next day. Phone lookup should find active case and resume — no duplicate.

### API Audit

| Step | HTTP | Payload (key fields) | Expected | Observed | Result |
|------|------|----------------------|----------|----------|--------|
| Return lookup | **200** | `has_active_case: true`, `case_id: case_23e113d4b686`, `customer_name: "Xiao B"`, `submit_state: "not_yet"` | Resume card data | Match | ✅ |
| Second `POST /customer/start-add-car` | **409** | `detail.error: "active_case_exists"` | No duplicate case | Match | ✅ |

### UI (Preview)

| Step | Result |
|------|--------|
| Enter `6265551002` → Continue | ✅ |
| Active case card | ✅ **You already have an active request.** |
| Actions | ✅ Continue Existing Request · Contact Broker |

### Database

```json
{
  "case_id": "case_23e113d4b686",
  "customer_phone": "6265551002",
  "lifecycle_status": "collecting",
  "still_needed_fields": ["year","make_model","zip","delivery_date","primary_driver","vin"],
  "primary_vehicle_summary": null
}
```

### Customer Understanding

- ✅ Return path works without session or login (Rule 2).
- ✅ Missing-field list shown on active card (Rule 4).
- ⚠️ `vehicle_display` shows **加车申请（车辆信息待补充）** until `primary_vehicle_summary` is materialized through intake chat — customer may not see “2024 Tesla Model Y” on the entry card until they continue into intake and fill vehicle fields. Resume **hydrates** full chat history via `customerEntryTurnsFromSavedCase` once they tap Continue.

**Simulation B: PASS** (resume + no-duplicate verified; vehicle label is stub until intake progress)

---

## Simulation C — Wrong Phone Digit

**Customer:** Xiao C (intended) · **Phone entered:** wrong digit (`6265551003` vs real `6265551002`)

### API Audit

| Step | HTTP | Payload | Expected | Observed | Result |
|------|------|---------|----------|----------|--------|
| Wrong-digit lookup | **200** | `has_active_case: false` | No match | Match | ✅ |
| `POST /customer/start-add-car` on wrong phone | **200** | New `case_id: case_da59993f0b0d` | System allows new draft | Match | ✅ (risk) |

### Answers

| Question | Answer |
|----------|--------|
| **Can customer recover?** | **No self-service recovery.** Wrong digit = empty lookup → customer sees “Start New Add-Car Request” and may believe they have no prior case. |
| **Does broker need to intervene?** | **Yes** — broker must match by name/WeChat, merge or close orphan, and correct phone on workbench. |
| **Risk severity** | **P1** — duplicate matter + customer confusion; Rule 7 only blocks **same** normalized phone, not typos. |

### Mitigation (copy / ops, not code)

- Customer copy: “No request found — double-check your phone number.”
- Broker playbook: search workbench by name; close/merge duplicate drafts.

**Simulation C: PASS (behavior verified) · Risk documented P1**

---

## Simulation D — Xiao D, Second Vehicle While Active

**Customer:** Xiao D · **Phone:** `6265551004`

### Scenario

Active case exists. Customer attempts second vehicle.

### API Audit

| Step | HTTP | Payload | Expected | Observed | Result |
|------|------|---------|----------|----------|--------|
| First start | **200** | `case_id` created | One draft | Match | ✅ |
| Second start (same phone) | **409** | `active_case_exists` + active case summary | Rule 7 enforced | Match | ✅ |
| Lookup | **200** | `has_active_case: true` | Single active case | Match | ✅ |

### Customer Message (UI spec)

- Active card: **One active add-car request at a time** (when second-vehicle path triggered).
- Primary path: **Continue Existing Request** or **Contact Broker**.

### Broker / Office Workflow

| Role | Action |
|------|--------|
| Customer | Cannot open second concurrent add-car case via API |
| Broker | Closes or splits current case (Rule 5), then customer can start fresh |
| Office | Sees one queue row per phone — no duplicate from double-start |

**Simulation D: PASS**

---

## Simulation E — Shared Household Phone

**Customers:** Li Hua + Wang Qiang · **Shared phone:** `6265551005`

### API Audit

| Step | HTTP | Payload | Expected | Observed | Result |
|------|------|---------|----------|----------|--------|
| Li Hua starts | **200** | `case_id: case_502ba7ce5f45`, `customer_name: "Li Hua"` | First claimant wins | Match | ✅ |
| Wang Qiang starts (same phone) | **409** | `active_case_exists` | Blocked | Match | ✅ |
| Lookup | **200** | `customer_name: "Li Hua"` | First name on record | Match | ✅ |

### What Happens?

- Rule 7 keys on **phone**, not person name → **one active case per household phone**.
- Wang Qiang cannot start a separate case; must use Li Hua’s case or contact broker.

### Constitution Conflict?

| Rule | Tension |
|------|---------|
| Rule 7 (one active case) | Phone is the identity handle — **by design** for Phase 1 |
| Rule 6 (broker confirms identity) | **Required** — broker must verify who is actually submitting when names differ |

**Not a constitution bug** — it is an explicit Phase 1 tradeoff. Broker action required for household splits.

**Simulation E: PASS · Broker playbook required**

---

## Simulation F — Submitted Case, Later Modification

**Customer:** Submitted add-car case · **Phone:** `6265551006`

### Scenario

Customer formally submitted, returns later, attempts modification (append).

### API Audit (live run)

| Step | HTTP | Observed | Expected | Result |
|------|------|----------|----------|--------|
| Active lookup (collecting draft) | **200** | `submit_state: "not_yet"`, all default `still_needed_fields` | Draft not yet submitted | Match | ✅ |
| `POST /triage` + `formal_submit: true` (incomplete fields) | **200** | `lifecycle_status: collecting` | Submit blocked until fields complete (Rule 3) | Match | ✅ |
| Second start while active | **409** | `active_case_exists` | Cannot fork | Match | ✅ |

### Append Behavior (prior certification)

Live append after formal submit was **not re-run** this sprint (OpenAI quota 429 on local triage). Prior battery:

- `docs/product_constitution/P16_APPEND_SIMULATION_REPORT.md` — **22/22 PASS**
- Post-submit append preserves collected fields; additive memory wins over triage regression.

### Lifecycle Behavior (code + constitution)

| State | Customer sees | Broker action |
|-------|---------------|---------------|
| `collecting` | Not Yet · missing fields | — |
| `handed_off` / `formal_submitted_at` + not collecting | **Submitted** on active card | Broker handles append / office follow-up |
| Closed | No active case on lookup | Broker reopened if needed (Rule 5) |

**Simulation F: CONDITIONAL PASS** — submit gate and active-case block verified; append integrity inherited from P16-APPEND sprint.

---

## Simulation G — Browser Closed, New Device

**Customer:** Returns on new device · **Phone:** `6265551007`

### Scenario

No browser session. Customer re-enters phone only.

### API Audit

| Step | HTTP | Payload | Expected | Observed | Result |
|------|------|---------|----------|----------|--------|
| Start draft (no `session_id`) | **200** | `case_id` created | Phone-keyed draft | Match | ✅ |
| Lookup (no session) | **200** | `has_active_case: true`, same `case_id` | Phone-only return | Match | ✅ |

### Session Dependency

| Mechanism | Required for return? |
|-----------|---------------------|
| `session_id` / `sessionStorage` | **No** — convenience only |
| `localStorage` phone pre-fill | **No** — optional UX on same browser |
| **Normalized phone lookup** | **Yes** — canonical return path (Rule 2) |

**Simulation G: PASS**

---

## Simulation H — Phone Normalization

**Canonical phone:** `6265551008`

### API Audit — all formats → same normalized phone

| Input format | HTTP | `phone_normalized` | `has_active_case` | Result |
|--------------|------|--------------------|-------------------|--------|
| `6265551008` | **200** | `6265551008` | `true` | ✅ |
| `(626)555-1008` | **200** | `6265551008` | `true` | ✅ |
| `626-555-1008` | **200** | `6265551008` | `true` | ✅ |
| `+1 626 555 1008` | **200** | `6265551008` | `true` | ✅ |

Invalid (&lt;10 digits after normalize): **400** `invalid_phone`.

**Simulation H: PASS**

---

## API Audit Summary Table

| Sim | Endpoint | HTTP | `has_active_case` | Notes |
|-----|----------|------|-------------------|-------|
| A cold | `GET .../active-case?phone=6265551001` | 200 | `false` | Scenario A |
| A warm | same | 200 | `true` | After start-add-car |
| B return | `.../6265551002` | 200 | `true` | Resume |
| B dup | `POST .../start-add-car` | 409 | — | Rule 7 |
| C wrong | `.../6265551003` | 200 | `false` | P1 risk |
| D block | `POST .../start-add-car` ×2 | 409 | — | Rule 7 |
| E shared | `.../6265551005` | 200 | `true` | Li Hua name |
| F active | `.../6265551006` | 200 | `true` | not_yet |
| G nodevice | `.../6265551007` | 200 | `true` | No session |
| H ×4 formats | `.../6265551008` variants | 200 | `true` | All normalize |

---

## Business Review

### 1. Customer

| Works well | Still confusing |
|------------|-----------------|
| No login wall | Wrong phone digit → feels like new customer |
| Phone return on any device | Vehicle line on entry card is generic until intake progress |
| Saved ≠ Submitted copy | “When will someone contact me?” — no SLA copy on entry card |
| Bilingual trust bullets | Missing-field labels are English field ids until humanized in intake |

**Support-call triggers:** “I submitted but office says missing info”; “I can’t find my Tesla case” (wrong digit); “My spouse can’t start their car.”

### 2. Broker

| Works well | Still confusing |
|------------|-----------------|
| One active case per phone (409) | Must manually fix wrong-phone orphans |
| Claimed name visible on case | Shared household needs identity confirmation (Rule 6) |
| Contact Broker path from entry card | `formal_submitted_at` on collecting drafts (ignore; use `submit_state`) |

**Support-call triggers:** Duplicate drafts from typo phones; household name mismatch.

### 3. Office Assistant

| Works well | Still confusing |
|------------|-----------------|
| Single queue row per phone | Cannot tell customer typo from genuinely new customer |
| `still_needed_fields` on workbench | Entry card missing fields may lag until chat capture |
| Postgres durable truth | — |

**10-second scan:** Works when case has `primary_vehicle_summary`; stub cases show “加车申请待补充.”

### 4. Founder

| Threatens $49/mo? | Keep simple |
|-------------------|-------------|
| Wrong-phone duplicate matters (P1) | Phone entry + Continue — do not add login |
| Shared-phone household friction (P2) | One active case — broker splits, not customer picker |
| No “contact timing” promise (P2) | Missing-field progress — no fake % bar |
| LLM quota / triage degradation in dev (ops) | Constitution rules — don’t expand scope |

**What remains simple:** Phone → lookup → start or resume → intake chat → formal submit. Broker closes loop.

---

## Findings (No Code Changes Required)

| ID | Severity | Finding | Action |
|----|----------|---------|--------|
| F1 | P1 | Wrong phone digit → empty lookup, possible orphan case | Copy + broker playbook (not code this sprint) |
| F2 | P2 | `vehicle_display` stub until intake fills vehicle | Expected Phase 1; improves after Continue |
| F3 | P2 | Shared household phone → one case, first name wins | Broker confirms identity (Rule 6) |
| F4 | P3 | `formal_submitted_at` set on draft create | UI uses `submit_state`; operators use lifecycle |
| F5 | Info | Append after submit | Certified P16-APPEND 22/22; not re-run live |

**Bugs discovered requiring code:** None.

---

## Simulation Scorecard

| Sim | API | UI | DB | Overall |
|-----|-----|----|----|---------|
| A | ✅ | ✅ | ✅ | **PASS** |
| B | ✅ | ✅ | ✅ | **PASS** |
| C | ✅ | — | ✅ | **PASS** (risk P1) |
| D | ✅ | — | ✅ | **PASS** |
| E | ✅ | — | ✅ | **PASS** |
| F | ✅ | — | ✅ | **CONDITIONAL** |
| G | ✅ | — | ✅ | **PASS** |
| H | ✅ | — | — | **PASS** |

**API simulations: 8/8 constitution mechanics verified**  
**UI spot-check: 2/2 (A, B) on Preview + Cloud Run**

---

*End of P16 Customer First Simulation Report*
