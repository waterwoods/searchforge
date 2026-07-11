# P19M-0 — Mini Program Prototype Readiness Checklist

**Date:** 2026-07-10  
**Parent SSOT:** `p19m0_unified_claim_mini_program_architecture_v1_2026_07_10.md`  
**Branch:** `sprint/p16-trust-layer` @ `3970bd8` (Gate 0A lock)
**Status:** Gate 0 **APPROVED** — P19M-1 local prototype authorized

---

## 1. SSOT Complete?

| Check | Status | Notes |
|-------|--------|-------|
| Main architecture SSOT created | ✅ | `p19m0_unified_claim_mini_program_architecture_v1_2026_07_10.md` |
| H5 mapping doc created | ✅ | `p19m0_h5_to_mini_program_mapping_2026_07_10.md` |
| Founder Decisions 1–10 preserved | ✅ | See SSOT §1, §25 |
| Prototype Non-Negotiable Locks (3) | ✅ | SSOT §Prototype Non-Negotiable Locks |
| Prototype scope bounded | ✅ | Lock 3 — immutable |
| Implementation gates defined | ✅ | SSOT §26 — Gate 0 approved |
| **Founder approval (Gate 0)** | ✅ | P19M-0A — local prototype only |

---

## 2. Gate 0 — Three Lock Checks

### UI Independence Check

- [ ] Mini Program design is not a visual copy of H5
- [ ] Each screen has one primary action
- [ ] Task Home opens directly to current task
- [ ] No traditional insurance portal homepage
- [ ] No parallel chat-form workflow

*Verify during P19M-1 implementation and prototype review.*

### Official Capability Isolation Check

- [ ] Unverified WeChat APIs are behind adapters/mocks
- [ ] No production identity assumption
- [ ] Token launch works without openid binding
- [ ] Official validation requirements are documented

*Prototype may use `h5t1` dev query + mock session. WeCom MP card = adapter mock until Gate 1.*

### Scope Containment Check

- [ ] No voice implementation
- [ ] No video implementation
- [ ] No Add Car
- [ ] No full tenant system
- [ ] No Workbench redesign
- [ ] No production deploy
- [ ] No schema migration

*Enforced by Lock 3 — immutable without Founder approval.*

---

## 3. Official Feasibility Unknowns

| Item | Classification | Blocker? |
|------|----------------|----------|
| Mini program 主体 registration | OFFICIAL VALIDATION REQUIRED | Potential |
| 类目 for insurance intake | OFFICIAL VALIDATION REQUIRED | Potential |
| Enterprise WeChat → MP card | OFFICIAL VALIDATION REQUIRED | Potential |
| US users / US entity | OFFICIAL VALIDATION REQUIRED | Potential |
| openid ↔ external_userid | OFFICIAL VALIDATION REQUIRED | High for production |
| Voice / ASR | OFFICIAL VALIDATION REQUIRED | No — text-only P19M-1 |
| `h5t1` token + H5 task APIs | **CONFIRMED** | No |
| Claim state machine + Workbench | **CONFIRMED** | No |

**Verdict:** WeChat official feasibility = **HOLD (Gate 1)** — may proceed in parallel; does **not** block local dev prototype (D15).

---

## 4. Existing APIs Ready?

| API | Ready? | Evidence |
|-----|--------|----------|
| `GET .../intake` | ✅ CONFIRMED | `routes/h5_task_intake.py` |
| `PATCH .../fields` | ✅ CONFIRMED | `patch_intake_fields()` with dedup |
| `POST .../submit` | ✅ CONFIRMED | Idempotent `submit_intent_id` |
| `POST .../upload` | ✅ CONFIRMED | `routes/h5_task_upload.py`, GCS pipeline |
| Dashboard payload | ✅ CONFIRMED | `_build_dashboard_summary()` |
| Phase / missing | ✅ CONFIRMED | `derive_claim_phase`, `get_claim_missing_items` |
| Broker readback | ✅ CONFIRMED | `build_claim_case_brief`, Workbench UI |
| Customer facade `/api/customer/*` | ❌ | Not built — Prototype uses H5 paths |
| MP session auth | ASSUMED FOR PROTOTYPE | Token-in-query + mock adapter |
| Voice upload | OUT OF SCOPE | Lock 3 |

**Verdict:** Backend **ready for P19M-1** via existing H5 task APIs.

---

## 5. Identity Plan

| Layer | Prototype (ASSUMED FOR PROTOTYPE) | Production (OFFICIAL VALIDATION REQUIRED) |
|-------|-----------------------------------|-------------------------------------------|
| Task credential | `h5t1` token in MP launch query | Token + wx session |
| WeCom binding | `external_userid` on case record | Same |
| MP user | Mock / defer openid | `wx.login` → `code2session` |
| Display name | From case / customer profile | nickname display-only |
| Recovery | Dev re-launch or manual token | WeCom Resume card (adapter) |

**Verdict:** Token-first **adequate for P19M-1**; production identity **not ready**.

---

## 6. Media Plan

| Type | Pipeline | P19M-1 |
|------|----------|--------|
| Photo | `ingest_h5_slot_upload` → GCS | ✅ Must Have (2 photos) |
| Slots | `claim_evidence_pack` | ✅ |
| Dedup | content SHA256 | ✅ |
| Voice | — | ❌ Strictly Out (Lock 3) |
| Video | — | ❌ Strictly Out (Lock 3) |

---

## 7. Prototype Must-Have Checklist

| # | Item | Backend | Frontend | Ready? |
|---|------|---------|----------|--------|
| 1 | One current task | ✅ | ❌ MP not built | Partial |
| 2 | Single tenant config | ✅ | ❌ | Partial |
| 3 | Task Home | ✅ | ❌ | Partial |
| 4 | One text story | ✅ | ❌ | Partial |
| 5 | Two photo uploads | ✅ | ❌ | Partial |
| 6 | Missing items | ✅ | ❌ | Partial |
| 7 | Review + Submit | ✅ | ❌ | Partial |
| 8 | Receipt + Resume | ✅ | ❌ | Partial |
| 9 | Error / expired states | ✅ | ❌ | Partial |
| 10 | Workbench readback | ✅ | ✅ | **Ready** |
| 11 | Native MP shell | — | ❌ | Not started |
| 12 | WeCom MP card | adapter mock | ❌ | Gate 1 / adapter |

---

## 8. STOP Conditions

Do **not** continue P19M-1 if:

| # | Condition |
|---|-----------|
| S1 | H5 UI copied mechanically (Lock 1 violation) |
| S2 | Prototype requires unverified WeChat production API as hard dependency (Lock 2 violation) |
| S3 | Scope expands outside minimal Claim loop (Lock 3 violation) |
| S4 | Backend rewrite begins without explicit need |
| S5 | Schema migration proposed without Founder approval |
| S6 | Backend Claim APIs regressed (`test_h5_claim_intake_form.py` red) |
| S7 | Production deploy attempted without Gates 1–8 |

**On any S1–S5 during implementation:** STOP and report before continuing.

---

## 9. GO / HOLD

| Decision | Verdict | Rationale |
|----------|---------|-----------|
| **Gate 0 / SSOT** | **APPROVED** | P19M-0A lock complete |
| **P19M-1 local prototype** | **GO** | Await P19M-1 prompt |
| **Production release** | **HOLD** | Gate 0 does not approve |
| **WeChat official feasibility** | **HOLD** | Gate 1 — parallel research OK |
| **H5 primary development** | **STOP** | Fallback only |
| **H5 fallback maintenance** | **GO** | Allowed |
| **WeCom structured intake expansion** | **STOP** | Notify + supplement only |
| **Backend rewrite for MP** | **STOP** | Facade / reuse only |

---

## 10. Pre-P19M-1 Actions

1. ~~Founder approves SSOT~~ ✅ Gate 0 closed
2. Issue P19M-1 implementation prompt
3. Gate 1 (parallel): Register dev mini program / confirm 类目
4. Run baseline pytest: `tests/test_h5_claim_intake_form.py`
5. Create native MP dev shell with adapter seams

---

*Gate 0 approved — P19M-1 authorized for local prototype only. No production deploy.*
