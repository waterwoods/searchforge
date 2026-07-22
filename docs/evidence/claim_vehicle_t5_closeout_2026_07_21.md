# Claim Vehicle T5 — Closeout

**Date:** 2026-07-21  
**Task:** Workbench structured vehicle projection / readback (`vehicle_information`)  
**Verdict:** **T5 DONE** (Founder QA UX deferred to separate P0)

---

## One objective

Finish the Claim Vehicle T5 production slice: broker can send `vehicle_information`; customer completes via existing Request Item path; Workbench shows the same structured vehicle (read-after-write).

**Out of scope for T5:** T6 vehicle fixture, T7 Cloud QA PAT, Add Car, new APIs, Mini Program form redesign, Founder QA UX Simplification.

---

## What was completed

| Area | Result |
|------|--------|
| UI MVP sendable | `vehicle_information` in Workbench Request More / MVP types |
| Broker Request More | Structured preset + response labels for 车辆信息 |
| Case brief backend | `claim_vehicle` projected from `known_facts` via Claim Vehicle Identity SSOT |
| Case brief UI | `ClaimCaseBriefPanel` shows structured year/make/model (+ VIN/plate when present) |
| Automated Path B | `tests/test_claim_vehicle_workbench_projection.py` PASS |
| T2/T3 + MVP gating regression | PASS |
| DB-primary extra bag durability | `claim_case_brief` / `claim_evidence_summary` (+ Golden photo slots) round-trip |
| Founder QA playbook | `docs/FOUNDER_QA_PLAYBOOK.md` committed as permanent runbook |

**Product commit:** `4a2f4cc` — `feat(claim-vehicle): T5 workbench vehicle_information request and readback`

**Architecture:** No new framework. Reuses Slice1 Request More, Request Item / `claimVehicleForm` (T4), `ClaimVehicleIdentityService` (T2/T3), timeline events, `known_facts` as SSOT. No duplicate vehicle APIs or second vehicle slot.

---

## What was intentionally NOT completed

| Item | Why deferred |
|------|--------------|
| Physical Founder Preview end-to-end (phone → Workbench) | Founder-owned; usability friction promoted to P0 |
| Founder QA Console / identity / Preview UX simplification | Separate P0 initiative |
| T6 deterministic vehicle-slot fixture | Next Claim Vehicle task; not T5 |
| T7 Cloud QA PAT + Production non-mutation proof | After T6 |
| Amend/withdraw for `vehicle_information` | Not in T5 freeze |
| Add Car / garage / multi-vehicle | Explicit non-goals in V1 freeze |

---

## Remaining risks

1. **Founder physical path not yet recorded** — automated Path B proves read-after-write; phone Preview + Workbench evidence still founder-owned under P0.
2. **Golden case defaults to insurance-card request** — vehicle Request More must be sent (or seed adjusted in T6/P0); not a T5 product defect.
3. **Founder QA Console friction** (identity selection, Preview/token pipeline) — blocks smooth manual verification; tracked as P0, not T5 blocker.
4. **Checklist + Structured Request More both send `vehicle_information`** — intentional reuse; no amend/withdraw changes in this slice.

---

## Why T5 is DONE

T5 exit criteria from `docs/product/CLAIM_VEHICLE_IDENTITY_V1.md`:

> Broker detail shows same structured vehicle as customer submit (read-after-write)

Met by:

1. Broker can send `vehicle_information` (UI + backend MVP sendable aligned).
2. Customer submit path already persists via Claim Vehicle Identity (T2–T4).
3. Workbench brief projects structured `claim_vehicle` from server `known_facts`.
4. Focused automated tests prove request → satisfy → brief projection without architecture drift.

Founder QA **usability** issues do not block this production slice; they are the next initiative.

---

## Handoff — P0 Founder QA UX Simplification

**Do not implement in this closeout.** Start only after explicit kickoff.

### Problem statement

Founders cannot smoothly verify production slices (including Claim Vehicle) because Golden QA / Console / Preview identity steps are multi-step and easy to mis-order. Product path is fine; the QA shortcut is the friction.

### Objective (for P0)

One founder action path: launch Golden QA → scan once → land on the correct active task → complete → see Workbench read-after-write — without Cursor-guided recovery.

### In scope (candidate)

- Reduce Founder QA Console / identity / Preview setup steps
- Clear first-failure staging (already sketched in playbook §3–4)
- Align Golden seed active request with the slice under test when needed
- Record evidence using `docs/FOUNDER_QA_PLAYBOOK.md` as SSOT

### Out of scope for P0

- Claim Vehicle T6/T7 product work (unless a tiny seed hook is required for verification)
- Production deploy / Mini Program Production upload
- New QA scenario picker or second product surface

### Start here

1. `docs/FOUNDER_QA_PLAYBOOK.md`
2. `docs/product/p20_founder_qa_checklist.md`
3. `bash scripts/launch_golden_qa.sh --qa`
4. Latest handoff under `docs/evidence/golden_qa/last_reset/` (session-only; do not commit tokens)

### Success signal

Founder completes one Camry Golden verification session in ≤15 minutes without engineering coaching, with secret-free evidence recorded.
