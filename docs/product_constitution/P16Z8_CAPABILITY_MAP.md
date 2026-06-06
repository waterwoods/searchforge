# P16-Z8 Phase 6 — Capability Map

**Date:** 2026-06-02  
**Sprint:** P16-Z8 Memory Hardening Archaeology  
**Domains:** Payment · Remove Vehicle · Collected Fields Merge · Waiting On · Claims Retention  
**Classification:** A=Already Built · B=Partially Built · C=Hidden · D=Broken · E=Truly Missing

---

## Master classification

| Domain | Already Built | Partially Built | Hidden | Broken | Missing |
|--------|---------------|-----------------|--------|--------|---------|
| **Payment Memory** | 45% | 25% | 15% | 10% | 5% |
| **Remove Vehicle** | 40% | 20% | 15% | 20% | 5% |
| **Collected Fields Merge** | 30% | 35% | 20% | 10% | 5% |
| **Waiting On Engine** | 55% | 25% | 15% | 0% | 5% |
| **Claims Retention** | 35% | 30% | 10% | 20% | 5% |

**Overall:** ~**65–70% of remaining memory system already exists** in `triage.py` + `case_store.py` + UI helpers. Gaps are **wiring, lane guards, and merge** — not new services.

---

## 1. Payment Memory

| Item | Class |
|------|-------|
| `payment_lapse_expiration` / `cancellation_warning` categories | **A** |
| Cancellation structured fields | **A** |
| Renewal / premium extractors + Z6 lane guard | **A** |
| `bill_sent_claimed` (post-Z6) | **A** |
| Prior-turn premium prepend | **A** |
| Case persistence of payment fields | **A** |
| `policy_bill_sent` precision | **B** |
| Chinese cancel wedge classification | **D** |
| Installment / 分期 classification | **D** |
| Payment amount in collected | **E** |
| Non–add-car collected merge on append | **D** |
| P16L payment evidence model | **E** (docs) |
| v4/v5 payment risk in UI | **C** |
| Confirmation # vs policy # | **B** |

---

## 2. Remove Vehicle Lane

| Item | Class |
|------|-------|
| `_is_remove_vehicle_request()` | **A** |
| Remove markers + templates | **A** |
| `_extract_remove_car_fields()` | **A** |
| Handoff copy + broker_next_step | **A** |
| Prior domain inference `remove_car` | **A** |
| `_remove_car_structured_fields()` | **E** |
| `_thread_is_remove_car_lane()` | **E** |
| Add-car guard on remove thread | **D** (D07) |
| Refund follow-up lane stability | **D** |
| Remove badge in UI | **C** |
| Multi-turn remove battery | **C** (Role D only) |

---

## 3. Collected Fields Merge

| Item | Class |
|------|-------|
| add_car full persisted merge | **A** |
| Lane-specific Turn 1 extractors (5 lanes) | **A** |
| `case_store` field persistence | **A** |
| Premium/claim/missing_doc re-extract | **B** |
| Generic `_merge_persisted_collected()` | **E** |
| else-branch field wipe | **D** |
| Deadline/policy hint append | **B** |
| Postgres field mirror | **C** |
| Turn-delta UI for fields | **C** |
| `human_confirmation_fields` | **A** |

---

## 4. Waiting On Engine

| Item | Class |
|------|-------|
| 4-value state model + validation | **A** |
| PATCH API + activity audit | **A** |
| Preserve on append | **A** |
| Queue filter + tracking summary | **A** |
| `still_needed` → client wait (implicit) | **B** |
| Triage → waiting_on inference | **E** |
| Deadline → next_contact_by | **E** |
| Follow-up editor UX | **C** |
| Archived workflow specs | **C** |
| Day 3 status ping handling | **B** (follow_up_type only) |

---

## 5. Claims Retention

| Item | Class |
|------|-------|
| FNOL routing Turn 1 | **A** |
| Claim templates (incl. hit-and-run) | **A** |
| `_extract_claim_fields()` booleans | **A** |
| Multi-turn message count | **A** |
| Correction prepend (partial) | **B** |
| Turn 2+ keyword retention | **D** |
| Plate / $ / total_loss fields | **E** |
| Claim vs missing_doc routing | **D** |
| Injury thread stability | **D** |
| waiting_on on adjuster delay | **E** |

---

## Duplication audit (SimulationAssistant guardrail)

| Risk | Verdict |
|------|---------|
| New PaymentMemoryService | **DO NOT BUILD** — extend triage |
| New WaitingOnEngine | **DO NOT BUILD** — heuristic in triage + existing PATCH |
| New ClaimsIntakeService | **DO NOT BUILD** — extend extractors |
| CollectedFieldsMergeService | **DO NOT BUILD** — generalize add-car pattern |
| Separate remove-car microservice | **DO NOT BUILD** — lane guard only |

---

## Phase 6 verdict

**Reuse first.** Five domains share one fix pattern: **lane guard + persisted collected merge + triage heuristic**. Estimated **3 engineer-days** total — not 3 weeks.
