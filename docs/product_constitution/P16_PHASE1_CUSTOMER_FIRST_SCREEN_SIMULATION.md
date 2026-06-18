# P16 Phase 1 — Customer First Screen Simulation

**Sprint:** P16-PHASE1-CUSTOMER-FIRST-SCREEN  
**Date:** 2026-06-07  
**Runner:** `PYTHONPATH=. python3 scripts/run_p16_customer_first_screen_simulations.py`

---

## Environment

- API: `http://127.0.0.1:8001`
- Auth: `X-Unified-Intake-Api-Key` (same perimeter as Unified Intake UI)
- Unit tests: `pytest tests/test_active_case_by_phone.py` — 3/3 pass

**Result: 4/4 simulations PASS**

---

## Simulation 1 — Li Hua, New Customer

**Setup:** Phone `6265550101`, no prior case.

**Steps:**

1. Open Customer Entry (cold URL mental model).  
2. Enter phone → Continue.  
3. API: `GET /customer/active-case`.

**Expected:** Scenario A — no active case → “Start New Add-Car Request”.

**Actual:**

```json
{"has_active_case": false, "phone_normalized": "6265550101", "active_case": null}
```

**Pass:** ✅

---

## Simulation 2 — Li Hua Returns (Tesla, Missing VIN)

**Setup:** Seed draft via `POST /customer/start-add-car` with phone `6265550102`, name 李华.

**Steps:**

1. Same customer returns with same phone.  
2. Continue → active case check.

**Expected:** Scenario B — active request, missing fields, not submitted.

**Actual:**

- `has_active_case: true`
- `submit_state: not_yet`
- `missing_fields` includes `vin` (plus other collecting defaults until vehicle filled)

**Note:** Full “2024 Tesla Model Y” line appears after customer fills vehicle in intake; draft stub shows 加车申请（车辆信息待补充） until then. Broker/workbench sees same case once vehicle fields are captured.

**Pass:** ✅

---

## Simulation 3 — Wrong Phone Digit

**Setup:** Li Hua’s real case on `6265550102`; customer types `6265550198` (wrong last digit).

**Expected:** No match → Scenario A → customer may unknowingly start a second path.

**Actual:**

- `has_active_case: false` for wrong phone

**Customer experience:** Feels like a brand-new customer. No error — system cannot know the typo.

**Risk (documented):**

| Risk | Severity | Mitigation |
|------|----------|------------|
| Wrong digit → empty lookup | P1 | Broker workbench phone edit; future: “No request found — double-check phone?” copy |
| Duplicate matter if broker hasn’t closed first | P1 | Rule 7 server 409 only same phone; wrong phone bypasses |
| Family shared phone | P2 | Broker confirms identity (Rule 6) |

**Pass:** ✅ (behavior verified; risk documented)

---

## Simulation 4 — Second Vehicle While Active

**Setup:** Active case on `6265550104`; customer attempts second `POST /customer/start-add-car`.

**Expected:** One Active Case enforced → Contact Broker.

**Actual:**

- HTTP **409**
- `detail.error: active_case_exists`
- Active case summary returned for UI “Continue Existing / Contact Broker”

**Pass:** ✅

---

## UI Walkthrough (Manual)

With demo running (`bash scripts/run_demo_local.sh`):

1. Tab **客户报送** → Customer First screen (not message-first textarea).  
2. 5-second test: banner shows 无需注册 / 无需密码 / 手机号继续.  
3. Scenario A/B cards match spec layout.  
4. Continue existing hydrates intake via `customerEntryTurnsFromSavedCase`.

---

*End of simulation record*
