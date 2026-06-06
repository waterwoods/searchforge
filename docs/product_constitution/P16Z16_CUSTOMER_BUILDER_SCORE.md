# P16-Z16 Phase 5 — Customer Builder Score

**Date:** 2026-06-03  
**Sprint:** P16-Z16 Customer Builder Reality Validation  
**Method:** Evidence from Phases 1–4 against north star: Customer First → Case Builder → Broker Review

---

## Scoring rubric

Each dimension scored 0–100 based on **what works today without new architecture**, not polish or future platform features.

---

## Dimension scores

| Dimension | Score | Evidence |
|-----------|-------|----------|
| **A. Create Case** | **88** | Add-Car formal submit → `save_case()` → real `case_id`. Multi-turn pre-submit collection works. Generic lanes persist on `handoff_ready`. |
| **B. Return Later** | **52** | Pre-submit: session restore (localStorage + Postgres). Post-submit: My Requests lists case but no conversation resume. Refresh loses `lastCaseId`. No customer auth. |
| **C. Append Information** | **78** | `appendFollowUpMessage` + `triage_for_append` + boundary enforcement fully implemented. UX: collapsed, post-handoff-only, in-memory `case_id`. |
| **D. Timeline** | **82** | `case_messages[]` sequenced thread + `case_activity[]` audit + stable `formal_submitted_at`. Customer UI shows chat bubbles pre-handoff only; no customer-facing activity timeline. |
| **E. Broker Visibility** | **90** | Workbench lists cases, shows thread, drafts, append updates, copy draft. Same case_id end-to-end. |
| **F. Persistence** | **85** | JSON case store always works; Postgres optional dual-write. Session store requires DB. 200-case cap in JSON. |
| **G. Cross-device readiness** | **18** | No login. `client_id` scopes broker pack, not customer. Shared case list. Session in localStorage. WeChat binding stub only. |

---

## Weighted overall

| Weight | Dimension | Score | Weighted |
|--------|-----------|-------|----------|
| 20% | A. Create Case | 88 | 17.6 |
| 20% | B. Return Later | 52 | 10.4 |
| 15% | C. Append | 78 | 11.7 |
| 10% | D. Timeline | 82 | 8.2 |
| 15% | E. Broker Visibility | 90 | 13.5 |
| 10% | F. Persistence | 85 | 8.5 |
| 10% | G. Cross-device | 18 | 1.8 |

**Overall: 72 / 100**

---

## Completion tier

| Tier | Threshold | Match? |
|------|-----------|--------|
| 50% — prototype | Basic intake | ✅ Exceeded |
| **70% — usable pilot** | **Create + broker review + partial return** | **✅ Current (~72%)** |
| 90% — production Customer First | Return + append + identity + cross-device | ❌ Not yet |
| 95% — mature SaaS | Auth, multi-tenant, full customer UX | ❌ Out of scope |

---

## Answer: How complete is Customer Builder?

**~70% complete** — firmly in the **「usable pilot」** band.

- Backend and broker path are **~85–90%**.
- Customer return-later and cross-device are **~35% blended**.
- The product is **not** 50% (too much exists).
- It is **not** 90% (return/resume/identity blockers remain).

---

## What the score means for reuse

Do **not** build a parallel Customer Builder. The 72% is **real infrastructure** with **UX wiring gaps**, not missing foundations. Closing to 90% is estimated **3–5 engineer-days** of wiring/repackaging (see Founder Summary), not a new architecture sprint.
