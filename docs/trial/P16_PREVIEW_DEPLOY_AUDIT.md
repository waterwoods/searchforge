# P16 Preview Deploy Audit — Office Visibility

**Sprint:** P16-VERIFY-AND-DEPLOY-OFFICE-VISIBILITY-SPRINT  
**Date:** 2026-06-06  
**Phase:** 1 — Verify Vercel Preview Build  
**Alias audited:** `ui-waterwoods-andys-projects-1f411b73.vercel.app`

---

## Before this sprint (stale Preview)

| Field | Value |
|-------|-------|
| **Deployment ID** | `dpl_JCuPNUHy6a3nDq64ea6SnYQQFLw6` |
| **Deployment URL** | `https://ui-rfkvvg0sz-andys-projects-1f411b73.vercel.app` |
| **Build timestamp (bundle)** | `2026-06-05T04:14:46.132Z` |
| **Bundle hash** | `index-CJ0tCunS.js` |
| **Vercel created** | Thu Jun 04 2026 21:14:40 PDT |
| **Git SHA (linked)** | **Not available** — CLI upload; inferred baseline `517f728` from deploy timing |
| **Local HEAD at audit start** | `b3c8ec369fa9f9232e3f663be23cd4f093c985d3` |

### Bundle marker scan (stale)

| Marker | Present? |
|--------|----------|
| `FOUNDER_DEMO_SEED_WORKBENCH_PENALTY` | ❌ |
| `getRecentFormalSubmissionVisibilityBoost` | ❌ |
| `buildOfficeCaseHeadline` (card headline path) | ❌ |
| `正式送达` (submitted tag copy) | ✅ (4) — generic copy only |
| `formal_submitted_at` field reference | ✅ (4) — not scoring |

### Product-only card behavior (stale HEAD)

`BrokerWorkbenchTab.tsx` @ HEAD product-only branch showed **urgency tag + 90-char `source_text` preview only** — no vehicle, case ID, missing fields, or office next step on card.

---

## Comparison vs local HEAD

| Dimension | Stale Preview | Local HEAD (`b3c8ec3`) | Office Visibility WIP |
|-----------|---------------|------------------------|------------------------|
| Git SHA | Inferred `517f728` era | `b3c8ec3` | Same + uncommitted UI delta |
| Score boost / demo penalty | ❌ | ❌ | ✅ |
| Product-only rich cards | ❌ | ❌ | ✅ |
| Bundle | `index-CJ0tCunS.js` | Not built/deployed | — |

---

## Answer: Did Preview contain Office Visibility changes?

**NO.**

Preview alias `ui-waterwoods` pointed to a **Jun 4 / Jun 5 bundle** without visibility scoring or enhanced product-only queue cards. Local HEAD also lacks the committed fix.

---

## After deploy (Phase 3 — for cross-reference)

| Field | Value |
|-------|-------|
| **Deployment ID** | `dpl_2S7zGtHDyHX2WW4fZdKtuQ9CwJHL` |
| **Deployment URL** | `https://ui-erdln9896-andys-projects-1f411b73.vercel.app` |
| **Alias** | `https://ui-waterwoods-andys-projects-1f411b73.vercel.app` |
| **Build timestamp (bundle)** | `2026-06-06T13:10:04.774Z` |
| **Bundle hash** | `index-DMOKMAa_.js` |
| **Vercel created** | Sat Jun 06 2026 06:09:59 PDT |
| **Git SHA (linked)** | **Not available** — CLI upload of WIP tree |
| **Intake API key in bundle** | ✅ (required for queue load) |

### Bundle marker scan (post-deploy)

| Marker | Present? |
|--------|----------|
| `正式送达` | ✅ (4) |
| `待补` | ✅ (5) |
| `primary_vehicle_summary` | ✅ (3) |
| `formal_submitted_at` | ✅ (4) |
| Penalty/boost constants (`300`, `165`) | ✅ |
| `founder_demo` penalty path | ✅ (1) |
