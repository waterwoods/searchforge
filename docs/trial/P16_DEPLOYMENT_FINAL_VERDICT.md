# P16 Deployment Final Verdict — Office Visibility

**Sprint:** P16-VERIFY-AND-DEPLOY-OFFICE-VISIBILITY-SPRINT  
**Date:** 2026-06-06  
**Classification:** **GO** (Chen Kui pilot on Preview)

---

## Founder answers

### 1. Was the fix actually deployed before this sprint?

**No.**

Preview served `index-CJ0tCunS.js` (build `2026-06-05T04:14:46Z`) without visibility scoring or enhanced product-only cards. The fix existed only as **uncommitted local WIP** and simulation docs — never committed, never on Vercel.

### 2. Is it deployed now?

**Yes.**

Preview alias updated 2026-06-06 with bundle `index-DMOKMAa_.js` (build `2026-06-06T13:10:04.774Z`). Browser certification confirms vehicle, case ID, submitted tag, missing fields, office next step, and Tesla case at queue top.

### 3. Which URL should Andy use?

**https://ui-waterwoods-andys-projects-1f411b73.vercel.app/workbench/unified-intake**

Use the **alias only** — not per-deploy hash URLs.

### 4. Which commit SHA is live?

| Layer | SHA / artifact |
|-------|----------------|
| **Git (repo HEAD)** | `b3c8ec369fa9f9232e3f663be23cd4f093c985d3` |
| **Office Visibility fix** | **Uncommitted WIP** on branch `sprint-a/broker-front-door` (not a git object) |
| **Vercel deployment** | `dpl_2S7zGtHDyHX2WW4fZdKtuQ9CwJHL` — CLI upload, no git metadata |
| **Live bundle identity** | `index-DMOKMAa_.js` · `2026-06-06T13:10:04.774Z` |
| **Cloud Run backend** | `29a00f8c7` (unchanged this sprint) |

**Action recommended:** Commit visibility WIP + API-key request wiring before next promotion.

### 5. GO / NO GO for Chen Kui pilot

**GO** — on Preview alias, supervised Day 0.

---

## Success criteria scorecard

| Criterion | Status |
|-----------|--------|
| Preview bundle contains Office Visibility fix | ✅ PASS |
| Tesla case visible in workbench | ✅ PASS |
| Vehicle + case ID shown on card | ✅ PASS |
| Ranking improved (#50 → #1 visible) | ✅ PASS |
| Deployment SHA / bundle identified | ✅ PASS (`dpl_2S7zGtHDyHX2WW4fZdKtuQ9CwJHL`, `index-DMOKMAa_.js`) |

**Overall: PASS**

---

## Residual risks (non-blocking for Preview pilot)

| Risk | Mitigation |
|------|------------|
| Fix not committed to git | Commit + tag before mainline promotion |
| `CustomerEntryTab` prototype imports missing on HEAD | Resolved for deploy only; needs proper stub or revert before next local build on HEAD |
| Production Vercel untouched | Intentional — prod remains pre-P16 UX |
| Backend one commit behind baseline | Acceptable for pilot; API path healthy for Tesla case |

---

## Sprint verdict

**FAIL → PASS (recovered in sprint).**

Blocker was **stale Preview deploy**, not DB/API. Deploy + API-key bundle + alias update cleared the gap. Chen Kui pilot may proceed on `ui-waterwoods` Preview.
