# P5 Sprint 1 — C01 Customer Lookup Reference Implementation

**Status:** Implementation + architecture/UX review — awaiting Founder acknowledgment  
**Date:** 2026-07-25  
**Capability:** C01 Customer Lookup  
**Governing law:** `docs/product/p5_capability_constitution_v1.md` · `docs/product/p5_capability_review.md` · `docs/FOUNDER_PRODUCT_CODEX_V1.md` · Workflow V2 blueprint  
**Prior harness:** `docs/product/p4_capability_01_customer_lookup.md` (contract + mock scenarios preserved)

---

## One objective / Out of scope

**ONE OBJECTIVE**

Prove in real code that **Workflow → Capability C01 → Mock Adapter → LookupResult** works as the template for every future Capability — with graceful degrade so nothing blocks reporting an accident.

**OUT OF SCOPE**

- C02 Prefill implementation changes  
- C03 Smart Claim Start redesign  
- Notification / Timeline / CRM / AMS live integration  
- Mini Program visual redesign as the product goal  
- Identity redesign (P29B unchanged)

---

# 1. Working C01 implementation

## Call chain (locked)

```text
Workflow V2 (c01_lookup_entry)
        ↓  lookup_customer(person_link_key)
Capability C01 (facade)
        ↓  CustomerDirectoryAdapter.lookup_by_person_link
Mock Adapter (mock_adapter + mock_directory fixtures)
        ↓
LookupResult  (always complete)
        ↓
Workflow branches on next_action / match_status only
```

## Code map (copy this for C02+)

| Layer | Path | Owns |
|-------|------|------|
| **Workflow** | `services/fiqa_api/inbox_triage/workflow_v2/c01_lookup_entry.py` | Journey mode, next screen, CTA, degrade branches |
| **Capability** | `services/fiqa_api/inbox_triage/customer_lookup/facade.py` | Flag, identity-shape gate, sanitize, adapter call |
| **Contract** | `…/customer_lookup/contract.py` | Stable `LookupResult` |
| **Adapter protocol** | `…/customer_lookup/adapters/protocol.py` | Swappable directory interface |
| **Mock Adapter** | `…/customer_lookup/adapters/mock_adapter.py` | Datasource simulation |
| **Fixtures** | `…/customer_lookup/mock_directory.py` | Adapter-owned mock rows (Workflow must not import) |
| **QA helpers** | `…/customer_lookup/qa_scenarios.py` | Scenario keys without leaking adapter into Cap 03 |
| **HTTP edge** | `POST /api/h5/customer/lookup` | Thin → Capability |
| **Tests** | `tests/test_p5_sprint1_c01_reference.py` | Boundary + degrade |
| **Sim** | `scripts/simulate_p5_sprint1_c01_reference.py` | Founder-readable PASS report |

## Mock Adapter outcomes (required)

| Outcome | Mock key | Workflow `journey_mode` |
|---------|----------|-------------------------|
| Customer found + active case | `wx_mock_cap01_s1_existing_active` | `continue_active` |
| Multiple vehicles | `wx_mock_cap01_s2_multi_vehicle` | `confirm_vehicle` (customer selects) |
| Policy expired | `wx_mock_cap01_s4_stale_policy` | `confirm_stale_policy` |
| Customer not found | `wx_mock_cap01_s5_identity_no_mapping` | `blank_claim` (manual claim) |
| Lookup unavailable | `wx_mock_cap01_s6_lookup_unavailable` / flag off | `blank_claim` (Pilot blank) |

## Commands (PASS on 2026-07-25)

```bash
P4_CUSTOMER_LOOKUP_MOCK=1 PYTHONPATH=. python3 -m pytest \
  tests/test_p5_sprint1_c01_reference.py \
  tests/test_p4_capability_01_customer_lookup_mock.py -q

P4_CUSTOMER_LOOKUP_MOCK=1 PYTHONPATH=. python3 \
  scripts/simulate_p5_sprint1_c01_reference.py
```

**Result:** pytest green · simulation `RESULT: PASS` · `BOUNDARY_WORKFLOW_NO_ADAPTER_IMPORT: PASS`

Flag remains **default OFF** in pilot (`P4_CUSTOMER_LOOKUP_MOCK`).

---

# 2. Architecture validation report

## Engineer Review

| Check | Result | Evidence |
|-------|--------|----------|
| Workflow owns journey | **PASS** | `enter_claim_with_lookup` / `decide_lookup_entry` live under `workflow_v2/` |
| Capability owns lookup | **PASS** | Facade answers “who?”; no case create/write CRM |
| Adapter owns datasource | **PASS** | `MockCustomerDirectoryAdapter`; fixtures not read by facade |
| Workflow never calls CRM | **PASS** | AST import ban in `test_workflow_never_imports_adapter_or_mock_directory` |
| Workflow never imports datasource logic | **PASS** | Same test + sim boundary check |
| Adapter swap without journey rewrite | **PASS** | `set_directory_adapter_for_tests(FakeAmsAdapter)` — Workflow still branches on contract |
| Lookup READ ONLY (L-05) | **PASS** | No write APIs; close step asserts `lookup_mutated_crm=False` |
| Graceful degrade (L-11) | **PASS** | Unavailable / not found → `blank_claim`; `blocks_accident_report=False` |
| Cap 02/03 not entangled | **PASS** | Workflow module does not import Prefill / Smart Claim Start |

### Architecture scorecard

| Dimension | Result |
|-----------|--------|
| Reliability | **PASS** — complete LookupResult every path |
| Simplicity | **PASS** — one question, one facade, one adapter protocol |
| Smoothness | **PASS** — HTTP 200 degrade; no thrown UI break |
| Business Value | **PASS** — journey can trust “who” without CRM SoR |
| Scope Control | **PASS** — C01 only; no AMS / Notification / Timeline |

### Reference pattern for C02 / C03 / C06

```text
1. contract.py     — stable result type
2. adapters/       — Protocol + Mock (+ future vendor)
3. facade.py       — Capability entry; flag + sanitize + degrade
4. workflow_v2/    — journey consumer; import Capability only
5. tests           — AST boundary + adapter swap + degrade matrix
6. simulate_*.py   — Founder-readable PASS/FAIL
```

A new engineer copies this layout; they do **not** invent Workflow→CRM shortcuts.

---

# 3. UX review

## 3.1 Workflow Review

| Question | Finding |
|----------|---------|
| Too many steps? | **No** for C01 itself — Lookup is silent. Main-chain narrative still 8 steps (unchanged harness). Customer-visible beats remain: Know you → What happened → Optional evidence → Submit. |
| Repeated input? | **Avoided** when match succeeds — name/vehicle come as chips/confirm, not retype. Blank path still asks only accident Must Haves (Pilot). |
| Unnecessary transitions? | **Watch item:** S3 (single vehicle, HIGH) still surfaces `confirm_vehicle`. Workflow V2 wanted “chips, not a quiz” for unambiguous match. Presentation belongs to C03 — do not invent a second confirm page in C01. |

**Verdict:** Workflow layer is thin and correct. Do not add C01-owned screens.

## 3.2 First-time Customer Walk

**Persona:** “I've just had an accident.” Open Mini Program → Start Claim entry that calls C01.

| Beat | Feeling | Notes |
|------|---------|-------|
| Open / login | Trust | Identity restore invisible (P29B) — good |
| Silent Lookup | Waiting | Must stay &lt;1s feel; no spinner essay; shell before network (Nav Gate) |
| Found + chips (S3) | Trust ↑ | “They know me” before story — North Star |
| Multi-vehicle (S2) | Slight friction | One chooser “哪辆车出险？” — acceptable; better than wrong car |
| Stale policy (S4) | Confusion risk | Copy must say “先确认保单，仍可继续报案” — not “不能报案” |
| Not found / unavailable (S5/S6) | Relief if blank | Same Pilot form — **do not show error wall** |
| Ambiguous | Anxiety | “联系顾问” alone can feel stuck — see Founder Challenge |
| Story / time / location / injury | Product core | Typing that remains is the right typing |
| Submit → Waiting | Trust | Named human (陈总) — unchanged |

**Confusion recorded:** Stale-policy and Ambiguous can read as blockers if copy is wrong.  
**Trust recorded:** Matched chips before story.  
**Typing recorded:** Identity typing → 0 when matched; accident facts remain.  
**Waiting recorded:** Lookup must never own a dedicated “正在匹配客户…” dead screen.

## 3.3 Graceful degrade matrix (product law)

| Lookup outcome | Continue? |
|----------------|-----------|
| Success | Continue (confirm only if ambiguous vehicle/policy) |
| Unavailable | Pilot blank workflow |
| Not found | Manual / blank claim |
| Multiple vehicles | Customer selects |
| Accident report blocked? | **Never** (except soft relogin for invalid identity handle) |

---

# 4. Founder Challenge report

Attempted redesign of our own solution:

### Can this workflow become even simpler?

**Yes, slightly — without changing C01 Owns.**

1. **Unambiguous match should not feel like a confirm quiz**  
   When `HIGH` + one vehicle + fresh policy + no active case → Workflow/C03 should show review chips and land on “今天发生了什么？” in one breath. C01 can keep `confirm_vehicle` as a soft next_action; **C03 must not invent an extra full-screen gate.**

2. **Ambiguous path needs a secondary escape**  
   Primary: 联系顾问. Secondary: 仍要先报案（空白） so a stressed customer is never trapped proving identity. Workflow now sets `allows_manual_claim=True` for `contact_broker` — **C03/UI must render the secondary CTA before customer-facing flag ON.**

3. **Can one screen disappear?**  
   Yes: any dedicated “Lookup loading / match status” page. Lookup stays behind Start Claim plan.  
   No: vehicle chooser for S2 — that screen earns its keep.

4. **Can typing decrease further?**  
   Not inside C01. Further typing removal is **C02 Prefill** classifying AUTO vs ASK. Do not overload Lookup with field taxonomy.

### Redesign verdict

Keep the three-layer reference. Simplify **presentation**, not the Capability boundary. Do not merge C01+C02 into one God Capability.

---

# 5. Recommended improvements before C02 begins

| # | Recommendation | Layer | Priority |
|---|----------------|-------|----------|
| 1 | C03 (or Workflow render): HIGH + single vehicle → chip strip, not full chooser | Workflow / C03 | **P0 before customer flag ON** |
| 2 | Ambiguous: render secondary “空白报案” CTA in Start Claim UI (Workflow already allows) | C03 / Mini Program | **P0 before customer flag ON** |
| 3 | Keep `P4_CUSTOMER_LOOKUP_MOCK` default OFF in pilot until Founder Preview GO | Ops | P0 |
| 4 | C02 consumes `LookupResult` only — copy C01 package layout (`contract` / `facade` / no Workflow→CRM) | C02 | Template |
| 5 | Do not add Timeline/Notification into C01 “while wiring Prefill” | Scope | Hard ban |
| 6 | Record only: real AMS adapter behind `CustomerDirectoryAdapter` after Pilot evidence | Adapter | P2 |
| 7 | Founder Reality Walk on physical Preview with S2 + S5 + S6 before Cap Done claim | QA | Required for User Done |

### Explicitly not recommended now

- Customer Account / profile center  
- Multi-case picker  
- CRM write-back  
- Expanding Start Claim Must Haves  
- Rewriting Mini Program purely for Lookup theater  

---

# 6. Success criteria check

| Criterion | Met? |
|-----------|------|
| Working C01 implementation | **Yes** |
| Workflow / Capability / Adapter validated in real code | **Yes** |
| Mock: found / multi-vehicle / expired / not found / unavailable | **Yes** |
| Workflow does not know datasource | **Yes** |
| Template for future Capabilities | **Yes** — documented code map + tests |
| Customer feel: “almost no time proving who I am” | **Conditional** — architecture ready; customer-facing GO still needs C03 presentation polish + Founder Preview |

**Customer north-star line (target feel):**

> I spent almost no time proving who I am. I could immediately start telling my story.  
> Type Less. Think Less. Trust More.

---

# 7. Rollback

1. Unset / `P4_CUSTOMER_LOOKUP_MOCK=0` → Capability returns `LOOKUP_UNAVAILABLE` → Workflow `blank_claim` (Pilot).  
2. No schema migration in this sprint.  
3. Do not roll back P29B identity with C01.

---

# 8. Founder checkbox

- [ ] Acknowledge three-layer reference (Workflow / Capability / Adapter)  
- [ ] Acknowledge READ ONLY + degrade matrix  
- [ ] Acknowledge recommendations #1–#2 before customer-facing flag ON  
- [ ] Authorize C02 loop separately (do not start from momentum)  
- [ ] Defer live AMS  

---

## Document control

| Version | Date | Change |
|---------|------|--------|
| v1 | 2026-07-25 | P5 Sprint 1 C01 reference implementation + four reviews |
