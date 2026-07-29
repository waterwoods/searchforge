# P5 Sprint 2 — C02 Claim Prefill Reference Implementation

**Status:** Implementation complete — **awaiting Founder Preview review**  
**Date:** 2026-07-25  
**Capability:** C02 Customer Prefill (Claim Prefill)  
**Governing law:** `docs/product/p5_master_execution_plan.md` · `docs/product/p5_capability_constitution_v1.md` · `docs/product/p5_capability_review.md` · C01 template  
**Prior harness:** `docs/product/p4_capability_02_claim_prefill.md` (classification table preserved)

---

## One objective / Out of scope

**ONE OBJECTIVE**

Prove in real code that **Workflow → Capability C02 → Classifier Adapter → PrefillResult** mirrors the C01 template — classify what we already know vs still need from `LookupResult` only, with zero AUTO on weak/ambiguous/unavailable paths, and no CRM write-back.

**OUT OF SCOPE (hard stop)**

- C03 Smart Claim Start implementation / Mini Program presentation  
- AMS / CRM live integration  
- Customer-facing feature flag ON  
- Timeline / Notification / Brief  
- Expanding Start Claim Must Haves  
- Identity redesign  

---

# 1. Working C02 implementation

## Call chain (locked)

```text
Workflow V2 (c02_prefill_entry)
        ↓  lookup_customer (C01 Capability)
LookupResult
        ↓  prefill_from_lookup (C02 Capability)
Capability C02 (facade)
        ↓  PrefillClassifierAdapter.classify
Mock Adapter (rules via engine)
        ↓
PrefillResult  (always complete)
        ↓
Workflow PrefillEntryDecision (ask/confirm summary only — no screens)
        ↓
C03 presentation (Sprint 3 — see p5_sprint3_c03_smart_claim_start_customer_trust.md)
```

## Code map (copy of C01 layout)

| Layer | Path | Owns |
|-------|------|------|
| **Workflow** | `services/fiqa_api/inbox_triage/workflow_v2/c02_prefill_entry.py` | When to call Prefill; ask/confirm summary; never screens |
| **Capability** | `…/claim_prefill/facade.py` | Entry, sanitize, degrade, adapter call |
| **Contract** | `…/claim_prefill/contract.py` | Stable `PrefillResult` |
| **Adapter protocol** | `…/claim_prefill/adapters/protocol.py` | Swappable classifier interface |
| **Mock Adapter** | `…/claim_prefill/adapters/mock_adapter.py` | Rule classification |
| **Engine** | `…/claim_prefill/engine.py` | Pure field taxonomy (adapter-owned logic) |
| **Tests** | `tests/test_p5_sprint2_c02_prefill.py` | Boundary + S1–S6 + degrade |
| **Sim** | `scripts/simulate_p5_sprint2_c02_prefill.py` | Founder-readable PASS report |

## Commands (PASS on 2026-07-25)

```bash
P4_CUSTOMER_LOOKUP_MOCK=1 PYTHONPATH=. python3 -m pytest \
  tests/test_p5_sprint2_c02_prefill.py \
  tests/test_p4_capability_02_claim_prefill.py -q

P4_CUSTOMER_LOOKUP_MOCK=1 PYTHONPATH=. python3 \
  scripts/simulate_p5_sprint2_c02_prefill.py
```

**Result:** pytest green · simulation `RESULT: PASS` · `BOUNDARY_WORKFLOW_NO_ADAPTER_OR_C03: PASS`

No new customer-facing flag. C01 Lookup mock remains default OFF in pilot. C02 is suggestion-only until C03 renders.

---

# 2. Architecture validation report

| Check | Result | Evidence |
|-------|--------|----------|
| Workflow owns journey summary | **PASS** | `enter_claim_with_prefill` / `decide_prefill_entry` under `workflow_v2/` |
| Capability owns classification | **PASS** | Facade answers “what do we know?”; no case/CRM writes |
| Adapter owns rules | **PASS** | `MockPrefillClassifierAdapter`; Workflow does not import engine |
| Workflow never calls CRM | **PASS** | AST ban + sim boundary |
| Workflow never imports C03 | **PASS** | AST ban on `smart_claim_start` |
| Adapter swap without journey rewrite | **PASS** | Fake richer adapter promotes email → AUTO; Workflow still uses contract |
| Prefill is suggestion (L-06) | **PASS** | `prefill_wrote_crm=False`; no write APIs |
| Graceful degrade (L-11) | **PASS** | Exception / missing lookup → complete zero-AUTO result |
| Cap 03 not entangled | **PASS** | Presentation step explicitly `deferred_to: C03` |

### Architecture scorecard

| Dimension | Result |
|-----------|--------|
| Reliability | **PASS** — complete PrefillResult every path |
| Simplicity | **PASS** — one question, one facade, one adapter protocol |
| Smoothness | **PASS** — never blocks accident reporting |
| Business Value | **PASS** — typing reduction measured (S1 removes ≥10 ask fields) |
| Scope Control | **PASS** — C02 only; no C03 / AMS / MP redesign |

---

# 3. Classification matrix (S1–S6)

| Scenario | AUTO | Customer ASK | Vehicle confirm | Stale confirm | Zero AUTO |
|----------|------|--------------|-----------------|---------------|-----------|
| S1 Existing + active | ≥8 | 5 accident | No | No | No |
| S2 Multi-vehicle | name/policy… | accident + vehicle/vin/plate | **Yes** | No | No |
| S3 No active | ≥8 | 5 accident | No | No | No |
| S4 Stale policy | name/vehicle… | accident + policy/carrier | No | **Yes** | No |
| S5 Not found | 0 | 5 accident | No | No | **Yes** |
| S6 Unavailable | 0 | 5 accident | No | No | **Yes** |
| Ambiguous | 0 | 5 accident | No | No | **Yes** |

Email stays **UNKNOWN** (never invented). Photos/docs stay **BROKER_REQUIRED** (not Start Claim Must Haves).

**Weak confidence:** `lookup_confidence == LOW` forces zero AUTO even if status looks matched.

---

# 4. Founder Preview (STOP HERE)

**This sprint stops for Founder review. Do not authorize C03 from momentum.**

### Preview checklist (Master Plan)

- [ ] Matched path: name/vehicle appear as known values in PrefillResult — not retyped taxonomy  
- [ ] Multi-vehicle: vehicle is ASK (choose), not silent AUTO  
- [ ] Stale policy: policy/carrier confirm (`needs_confirm`), not silent AUTO  
- [ ] Not found / unavailable / ambiguous: zero dangerous AUTO  
- [ ] No enum names (`AUTO_PREFILL`) required on any customer surface (C02 does not render UI)  
- [ ] Engineer can explain “suggestion, case is SoR” in one sentence  

### How to walk the Preview (≤10 minutes)

```bash
P4_CUSTOMER_LOOKUP_MOCK=1 PYTHONPATH=. python3 \
  scripts/simulate_p5_sprint2_c02_prefill.py
```

Read the JSON report:

1. **S3** — `auto_chip_values` includes 陈明 / Camry; `customer_ask_fields` = accident facts only.  
2. **S2** — `needs_vehicle_confirm: true`; vehicle not in AUTO chips.  
3. **S4** — `needs_stale_policy_confirm: true`.  
4. **S5 / S6 / AMBIGUOUS** — `zero_auto: true`.  
5. Every row — `deferred_presentation: C03`, `prefill_wrote_crm: false`, `blocks_accident_report: false`.

### Founder Challenge (self-review)

| Question | Answer |
|----------|--------|
| Can we merge C01+C02? | **No** — different business questions; Constitution seam. |
| Can we ship customer flag ON now? | **No** — presentation is C03; Master Plan Gate 2. |
| Did we invent truth for email/VIN? | **No** — UNKNOWN / last4 only. |
| Did Workflow grow Start Claim screens? | **No** — `owns_start_claim_screens=False`. |
| Could typing decrease further inside C02? | **No** — next win is C03 chip presentation, not more taxonomy. |

### Customer feel (conditional)

> Architecture ready for “Type Less.” Customer-visible “almost no time proving who I am” still requires **C03 presentation** (Gate 2).

---

# 5. GO / NO GO (C02 only)

| GO (authorize C03 next) | NO GO |
|-------------------------|-------|
| Classification matches matrix; degrade complete; Workflow thin; CRM untouched | Any CRM write; Must Have expansion; Workflow imports adapters/C03; customer flag ON |

### Founder checkbox

- [ ] Acknowledge C02 three-layer reference (Workflow / Capability / Adapter)  
- [ ] Acknowledge Prefill is suggestion only; claim case remains SoR  
- [ ] Acknowledge S1–S6 / ambiguous zero-AUTO matrix  
- [ ] Acknowledge Sprint stops here — **authorize C03 separately**  
- [ ] Defer AMS / Mini Program wire / customer flag ON  

---

# 6. Recommended next (after Founder GO)

| # | Only after Founder authorize | Layer |
|---|------------------------------|-------|
| 1 | Sprint 3 — C03 Smart Claim Start + chips / blank escape | Workflow / C03 / Mini Program |
| 2 | Keep C01 Lookup mock OFF in pilot until Gate 2 | Ops |
| 3 | Do not add Timeline/Notification “while wiring Start” | Scope ban |

### Explicitly not recommended now

- Customer Account / profile center  
- AMS adapter  
- Merging C02 into C01  
- Expanding Start Claim Must Haves  

---

# 7. Rollback

1. Stop calling `enter_claim_with_prefill` from any future wire — Pilot blank path unaffected.  
2. C01 flag OFF still yields Lookup unavailable → Prefill zero AUTO.  
3. No schema migration in this sprint.  
4. C03 / smart_claim_start package untouched as product goal (still may import `build_prefill_result` for its own harness).  

---

## Document control

| Version | Date | Change |
|---------|------|--------|
| v1 | 2026-07-25 | P5 Sprint 2 C02 reference — stop at Founder Preview |
