# P16-Z18 Top 20 Things Never To Build

**Date:** 2026-06-03  
**Sprint:** P16-Z18 Product Constitution Refresh  
**Sources:** P16-Z3/Z9 90-day filter · P16-Z16/Z17 · P16-Z5/Z8 · constitution · user mandate

**Rule:** If it exists in `inbox_triage/` or current UI tabs, **wire — never rebuild.**

---

## Ranked never-build list

| Rank | Never build | Why | Use instead |
|------|-------------|-----|-------------|
| **1** | **New Customer Builder** | `CustomerEntryTab` is ~76% real (`P16Z17`) | Wire return-later UX |
| **2** | **New Case Service** | `case_store.py` + `SavedCase` complete | `save_case()` |
| **3** | **New Timeline Service** | `case_messages` + `case_activity` in case store | Render existing arrays |
| **4** | **New Memory Service** | `triage_for_append` production-grade | Tune `triage.py` merge |
| **5** | **Case Intelligence microservice** | 48 modules = L4.5 engine (`P16Z3`) | `triage.py` + `case_draft_engine.py` |
| **6** | **Conversation / append microservice** | Append route + tests exist (`P16Z4`) | `POST .../append-message` |
| **7** | **Platform rewrite / P17** | Constitution blocked | `product_only` pilot |
| **8** | **CRM / AMS replacement** | Offices keep existing AMS (`P16Z2`) | Case export if needed |
| **9** | **Stripe / in-app billing** | Manual invoice until 3+ offices (`P16Z3`) | Founder invoice |
| **10** | **Customer portal from scratch** | Tabs exist, hidden not missing (`P16Z0`) | `UnifiedIntakePage` tabs |
| **11** | **GraphRAG / knowledge graph layer** | Platform fantasy | Rules + case store |
| **12** | **Voice agent / IVR intake** | Out of pilot scope (`P16Z3`) | Text message wedge |
| **13** | **WaitingOnEngine service** | PATCH + Z10B heuristic done | `_suggest_waiting_on()` |
| **14** | **PaymentMemoryService** | Payment logic in triage (`P16Z8`) | Lane guards + merge |
| **15** | **ClaimsIntakeService / greenfield FNOL** | Turn 1 ready; tune Turn 2+ (`P16Z6`) | `_extract_claim_fields` |
| **16** | **CollectedFieldsMergeService** | Z10A generic merge shipped | `_merge_persisted_collected` |
| **17** | **OCR-first primary product** | Pipeline built; no product caller (`P16Z3`) | Text paste wedge |
| **18** | **SimulationAssistant v2** | Orphaned — zero imports (`P16Z0`) | `ScenarioReplayTab` + Role D |
| **19** | **WeChat bot / official integration** | Broker stays channel (`P16Z4`) | Copy-to-WeChat |
| **20** | **Multi-tenant auth platform** | Single broker supervised pilot | Shared `client_id` pack |

---

## Additional never-build (21–35)

| Item | Source |
|------|--------|
| LLM generation rewrite | Rules 88.6 sufficient; path unverified (Z3) |
| Risk scoring engine v6+ | v4/v5 exists, wire badge only (Z3) |
| Outcome / resolution product UI | Observation log first (Z9) |
| Push notifications / email automation | WeChat is channel (Z2) |
| HubSpot-style sequences | Not wedge (Z9) |
| Document intelligence L6 product | Memory L5 incomplete (Z9) |
| Second office GTM tooling | Chen Kui not paid (Z3) |
| New add-car battery runners | p16y + role_d sufficient (Z0) |
| P16-M full TOP50 UI sprint | Copy fixes only (Z9) |
| Audit export product | Scaffold only — ignore (Z9) |
| ML distillation experiment | Rules-first (Z3) |
| Deadline countdown widget (now) | Tier 2 nice-to-have (Z8) |
| Full activity timeline merge (now) | Z6 thread sufficient first (Z9) |
| Customer message-first **replatform** | Repackage tabs, don't rebuild (Z16) |
| Greenfield case persistence | Contradicted by live proof (Z17) |

---

## Never-build decision tree

```
New feature idea?
    │
    ├─ Exists in case_store / triage / current tab?
    │       YES → Wire / tune / deploy. STOP.
    │
    ├─ In P16Z18_MVP_SCOPE OUT list?
    │       YES → Reject. STOP.
    │
    ├─ Moves Customer Builder 76 → 90+?
    │       NO → Defer. STOP.
    │
    └─ Founder explicitly updates constitution?
            NO → Reject. STOP.
```

---

## Historical waste patterns (do not repeat)

From P16-Z3 §4 — estimated waste if rebuilt:

| Pattern | Already exists | Waste if rebuilt |
|---------|----------------|------------------|
| Case Intelligence microservice | `triage.py` | Weeks |
| Conversation service | `triage_conversation()` | Weeks |
| OCR pipeline | `image_input_pipeline.py` | Days |
| Customer portal | `CustomerEntryTab` + `MyRequestsTab` | Weeks |
| ~197 lab script batteries | guardrail + p16y + role_d | Ongoing cognitive load |
| P17 platform | Blocked | Months |

---

## Docs to demote (not code — never-build narratives)

| Archive narrative | Why |
|-------------------|-----|
| "Build Customer Builder from scratch" | Contradicted Z16/Z17 |
| "Build case persistence layer" | `case_store.py` exists |
| "Customer tab week 3 greenfield" | Tab exists today |
| Simulation Role C/D as primary product | Test harness, not Customer First |
| Platform sprint roadmaps in `docs/archive/platform/` | Fantasy |

---

## One-line never-build rule

> **If you're building a new service, portal, or platform — stop. Wire what Z17 proved already works.**

---

*End of P16-Z18 Phase 8 — Top 20 Things Never To Build*
