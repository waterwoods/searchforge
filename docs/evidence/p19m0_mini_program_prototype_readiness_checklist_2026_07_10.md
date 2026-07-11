# P19M-0 — Mini Program Prototype Readiness Checklist

**Date:** 2026-07-10  
**Parent SSOT:** `p19m0_unified_claim_mini_program_architecture_v1_2026_07_10.md`  
**Branch:** `sprint/p16-trust-layer` @ `d413434`  
**Status:** Pre-Prototype gate checklist

---

## 1. SSOT Complete?

| Check | Status | Notes |
|-------|--------|-------|
| Main architecture SSOT created | ✅ | `p19m0_unified_claim_mini_program_architecture_v1_2026_07_10.md` |
| H5 mapping doc created | ✅ | `p19m0_h5_to_mini_program_mapping_2026_07_10.md` |
| Founder Decisions 1–10 preserved | ✅ | See SSOT §1, §25 |
| Prototype scope bounded | ✅ | SSOT §21 |
| Implementation gates defined | ✅ | SSOT §26 — Gate 0 blocked |
| **Founder approval** | ❌ | **Required before P19M-1** |

---

## 2. Official Feasibility Unknowns

| Item | Known | Unknown | Blocker? |
|------|-------|---------|----------|
| Mini program 主体 registration | No MP project exists | Entity type, region | **Potential** |
| 类目 for insurance intake | — | Required category list | **Potential** |
| Enterprise WeChat → MP card | WeCom cards use H5 view URLs today (`reply.py`) | MP card API for KF | **Potential** |
| US users / US entity | Chen pilot is WeChat-native | Official policy | **Potential** |
| openid ↔ external_userid | Separate ID systems in code | Official linking API | **High for seamless auth** |
| Voice / ASR | No backend endpoint | WeChat plugin availability | No — text fallback |

**Verdict:** WeChat official feasibility = **HOLD** until Gate 1 spike.

---

## 3. Existing APIs Ready?

| API | Ready? | Evidence |
|-----|--------|----------|
| `GET .../intake` | ✅ | `routes/h5_task_intake.py`, deployed per `p19h3i` evidence |
| `PATCH .../fields` | ✅ | `patch_intake_fields()` with dedup |
| `POST .../submit` | ✅ | Idempotent `submit_intent_id` |
| `POST .../upload` | ✅ | `routes/h5_task_upload.py`, GCS pipeline |
| Dashboard payload | ✅ | `_build_dashboard_summary()` — commit `7ac5362` |
| Phase / missing | ✅ | `derive_claim_phase`, `get_claim_missing_items` |
| Broker readback | ✅ | `build_claim_case_brief`, Workbench UI exists |
| Customer facade `/api/customer/*` | ❌ | Not built — Prototype can use H5 paths |
| MP session auth | ❌ | Not built — token-in-query for Prototype |
| Voice upload | ❌ | Not built |

**Verdict:** Backend **ready for Prototype** via existing H5 task APIs.

---

## 4. Identity Plan

| Layer | Prototype plan | Production plan |
|-------|----------------|-----------------|
| Task credential | `h5t1` token in MP launch query | Token + wx session |
| WeCom binding | `external_userid` on case record | Same |
| MP user | Defer openid — token is sufficient for P0 | `wx.login` → `code2session` |
| Display name | From case / customer profile | nickname display-only |
| Recovery | WeCom「进度」→ new card with token | Same |

**Verdict:** Identity **adequate for Prototype** with token-first; **not adequate for production** without Gate 3.

---

## 5. Media Plan

| Type | Pipeline | Ready? |
|------|----------|--------|
| Photo | `ingest_h5_slot_upload` → GCS (`media_storage.py`) | ✅ |
| Slots | `claim_evidence_pack` 3 slots | ✅ |
| Dedup | content SHA256 | ✅ per smooth UX design |
| Voice | No endpoint | ❌ mock or defer |
| Video | Out of scope | — |

**Verdict:** Photo **ready**; voice **not ready**.

---

## 6. State Mapping

| Check | Status |
|-------|--------|
| `derive_claim_phase()` documented | ✅ SSOT §10 |
| Customer labels simplified | ✅ |
| MP must not invent phases | ✅ enforced in SSOT |
| `broker_done` broker-only | ✅ `mark_claim_broker_done()` |
| Submit → `intake_ready_for_broker` | ✅ `submit_intake_form()` |

**Verdict:** State mapping **complete** for architecture.

---

## 7. Prototype Must-Have Checklist

| # | Item | Backend | Frontend | Ready? |
|---|------|---------|----------|--------|
| 1 | One current task | ✅ single active claim | ❌ MP not built | Partial |
| 2 | Single tenant config | ✅ hardcoded 陈总 | ❌ | Partial |
| 3 | Task Home | ✅ dashboard_summary | ❌ | Partial |
| 4 | Progress display | ✅ completed_count | ❌ | Partial |
| 5 | Story input | ✅ PATCH story | ❌ | Partial |
| 6 | Photo upload (2+) | ✅ upload API | ❌ | Partial |
| 7 | Review | ✅ intake GET | ❌ | Partial |
| 8 | Submit idempotent | ✅ | ❌ | Partial |
| 9 | Resume | ✅ 72h token | ❌ | Partial |
| 10 | Error states | ✅ 403 codes | ❌ | Partial |
| 11 | Workbench readback | ✅ | ✅ UI exists | **Ready** |
| 12 | WeCom MP card | ❌ H5 URL today | ❌ | **Not ready** |

---

## 8. STOP Conditions

Do **not** start P19M-1 if:

| # | Condition |
|---|-----------|
| S1 | Founder has not approved SSOT (Gate 0) |
| S2 | Tracked uncommitted business code on branch |
| S3 | Gate 1 confirms WeChat registration impossible for founder entity |
| S4 | Backend Claim APIs regressed (pytest red on `test_h5_claim_intake_form.py`) |
| S5 | Scope creep: Add Car, multi-tenant admin, or Workbench redesign included |

---

## 9. GO / HOLD

| Decision | Verdict | Rationale |
|----------|---------|-----------|
| **SSOT review** | **GO** | Documents complete; await Founder |
| **Prototype implementation (P19M-1)** | **HOLD** | Gate 0 not approved |
| **WeChat official feasibility** | **HOLD** | Unverified; Gate 1 required |
| **H5 further development as primary** | **STOP** | Founder Decision 1 — H5 is fallback only |
| **H5 bugfix / fallback maintenance** | **GO** | Keep fallback operational |
| **WeCom structured intake expansion** | **STOP** | Founder Decision 2 |
| **Backend rewrite for MP** | **STOP** | Reuse facade only |

---

## 10. Pre-P19M-1 Actions (after Gate 0)

1. Founder approves SSOT
2. Gate 1: Register dev mini program / confirm 类目
3. Confirm WeCom MP card vs URL scheme for Chen pilot
4. Run baseline pytest: `tests/test_h5_claim_intake_form.py`
5. Launch P19M-1 prompt

---

*Checklist complete — P19M-0 architecture freeze. No code authorized.*
