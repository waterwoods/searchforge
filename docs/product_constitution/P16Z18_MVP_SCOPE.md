# P16-Z18 MVP Scope Lock

**Date:** 2026-06-03  
**Sprint:** P16-Z18 Product Constitution Refresh  
**Rule:** No scope creep. Optimize for first paying broker.

---

## MVP definition

**Minimum viable product** = supervised pilot where a customer can start a request, the office confirms a draft case, both sides see continuity across days, and Chen Kui will pay for time saved.

**North star loop (only scope that matters):**

```
Customer Message → Draft Case → Broker Review → Return Later → Timeline → Close
```

**Current completion:** Customer Builder **~76/100** (`P16Z17`). MVP = **≥90** on Cap 1, 4, 5, 7.

---

## IN MVP

### Core flow (must work end-to-end)

| Step | What | Existing asset | Status |
|------|------|----------------|--------|
| 1 | **Customer Message** | `CustomerEntryTab` + `triageMessage()` | ✅ Works (Add-Car) |
| 2 | **Draft Case** | `triage.py` → collected/still/next step | ✅ P16-Y 88.6 |
| 3 | **Broker Review** | `BrokerWorkbenchTab` + same `case_id` | ✅ 88/100 |
| 4 | **Return Later** | Session pre-submit ✅ · post-submit wiring ❌ | ⚠️ **Blocker** |
| 5 | **Timeline** | `case_messages` + `case_activity` | ✅ Data · ⚠️ Customer UI |

### IN — feature list

| Feature | Notes |
|---------|-------|
| Customer Entry / Case Builder tab | Rename copy optional; code stays `CustomerEntryTab` |
| Multi-turn triage (Add-Car flagship) | Formal submit gate with structural truth (VIN) |
| Formal submit → `save_case` → `case_id` | Proven live |
| My Requests / progress list | Lists cases; must wire `case_id` back |
| Post-handoff append (same case) | API ✅ · customer UX after refresh ❌ |
| Broker workbench glance + thread | Z6 UI in repo |
| Append from broker side | `appendFollowUpMessage` / paste append |
| Chinese office next step + missing fields | Z11 office value surface |
| `waiting_on` suggest (broker confirms) | Z10B heuristic |
| Session restore (pre-submit) | localStorage + Postgres session |
| Validation batteries | guardrail · p16y · role_d · trial_launch_check |
| Single broker pack (Chen Kui) | `client_id=chen_kui` |
| Manual invoice ($49–99 pilot) | Founder process, not product |
| Observation log | Commercial SSOT for proof |
| Deploy to cold URL | Blocked but **in MVP** — must fix |

### IN — wiring tasks (not new features)

1. Hydrate `case_id` into Customer Entry after return  
2. My Requests → pass `case_id` on continue  
3. Resume hint for submitted cases  
4. Demo env session DB verification  
5. 3-day Tesla browser walkthrough  
6. Founder + Chen Kui supervised testing  

**Estimate:** 3.0–3.5 engineer-days (`P16Z17_TRUE_MVP_GAPS`)

---

## OUT MVP

### Explicitly OUT (do not build, do not sprint)

| Item | Why OUT | Use instead |
|------|---------|-------------|
| **CRM** | Offices have AMS | Export case summary if needed |
| **Stripe** | Manual invoice until 3+ offices | Founder sends invoice |
| **P17** | Constitution blocked | `product_only` pilot |
| **Voice Agent** | Out of pilot scope | Text/message wedge |
| **GraphRAG** | Platform fantasy | `triage.py` rules |
| **Platform Rebuild** | Engine L4.5 exists | Wire existing modules |
| **New Customer Builder** | Already exists | `CustomerEntryTab` |
| **New Case Service** | `case_store.py` complete | Reuse |
| **New Timeline Service** | `case_messages` in case store | Render existing |
| **New Memory Service** | `triage_for_append` exists | Tune merge in `triage.py` |
| **Case Intelligence microservice** | 48 modules in repo | `inbox_triage/` |
| **WaitingOnEngine service** | PATCH + heuristic done | Z10B suggest |
| **ClaimsIntakeService / greenfield FNOL** | Turn 1 ready | Tune extractors |
| **OCR-first primary intake** | Text wedge first | Wire attachment later |
| **WeChat bot / integration** | Broker is channel | Copy-to-WeChat |
| **Multi-tenant auth** | Single broker pilot | Shared case list OK for supervised |
| **Cross-device customer identity** | Post-MVP | Same-browser sufficient for pilot |
| **Customer message timeline UI (full)** | Nice-to-have | Progress fields in My Requests OK for v1 |
| **Outcome / closure product UI** | Process first | Observation log |
| **Push notifications / email** | WeChat is channel | — |
| **SimulationAssistant v2** | Orphaned | ScenarioReplayTab + Role D |
| **Second office onboarding** | Chen Kui not paid | After first payment |
| **LLM generation rewrite** | Rules at 88.6 | Rules-first |
| **P16-M TOP50 UI sprint** | Copy fixes only if blocking | TOP5 max |
| **Deadline countdown widget** | Tier 2 | Prose hint sufficient |
| **Risk dashboard** | v4 score exists | Single badge max |
| **Lab tabs on trial URL** | Cognitive load | `productOnlyUi` |

---

## Scope creep guardrails

Before any PR or sprint, ask:

1. Does it move **Customer Builder 76 → 90+**?  
2. Does it close **Return Later → Append** without new architecture?  
3. Does it help **Chen Kui pay** in the next 30 days?

If **no to all three** → **OUT**.

### Allowed sprint types (from Z9, unchanged)

| Type | Example |
|------|---------|
| **Ship** | Wire `case_id` hydrate · deploy Z11 backend |
| **Validate** | Role D run · 3-day browser walkthrough · observation log |
| **Archive** | SSOT refresh (this sprint) |

**Forbidden:** Platform sprint · archaeology without code delta · greenfield customer portal · new microservice.

---

## MVP exit criteria (GO for supervised Chen Kui pilot)

- [ ] Customer: message → draft → submit → **return next day** → append on **same case_id** (browser, no founder narration)
- [ ] Broker: sees append + timeline without reopening customer chat
- [ ] `bash scripts/trial_launch_check.sh` PASS on deployed URL
- [ ] P16-Y ≥88 · Role D reread ≥80
- [ ] Andy: 3 real multi-turn cases in observation log
- [ ] Chen Kui: supervised 15-min demo on cold URL
- [ ] Invoice sent

**NOT required for MVP GO:** Stripe · cross-device · full customer timeline UI · second office · claims 100% retention · voice · GraphRAG.

---

## One-line scope lock

> **IN: Customer message → draft case → broker confirm → return later → timeline. OUT: everything else until Chen Kui pays.**

---

*End of P16-Z18 Phase 4 — MVP Scope Lock*
