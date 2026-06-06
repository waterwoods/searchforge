# P16-Z21 Phase 3 — Lightweight Prototypes

**Date:** 2026-06-03  
**Branch:** main (no isolated branch — changes gated by URL param)  
**Time budget:** ≤30 min per path

---

## Activation

Open Customer Entry with query param:

| Path | URL |
|------|-----|
| **A — Minimal** | `?tab=customer&builderEvolution=minimal` |
| **B — Guided** | `?tab=customer&builderEvolution=guided` |
| **C — Timeline First** | `?tab=customer&builderEvolution=timeline` |
| Default (unchanged) | no param |

---

## Path A — Customer Builder Minimal

**Files:**
- `ui/src/features/intake/components/CustomerEntryTab.tsx` — hides secondary empty-state links when `minimal`
- `ui/src/features/intake/prototypes/p16z21/evolutionPaths.ts`

**Changes:**
- Empty state: textarea + send + trust line only
- Hides: structured Add-Car form link, more-intents dropdown, human-help link
- No backend changes

**Intent:** Fastest paste-and-go for WeChat-forward customers; lowest cognitive load.

---

## Path B — Customer Builder Guided

**Files:**
- `ui/src/features/intake/prototypes/p16z21/PathGuidedRail.tsx`
- `CustomerEntryTab.tsx` — renders rail when Add-Car active and `guided`

**Changes:**
- Horizontal step checklist: 年份 → 车型 → VIN → 邮编 → 主驾 → 提车日 → 姓名/电话
- Steps derive from `collected_fields` / `still_needed_fields` on latest triage turn
- No backend changes

**Intent:** Reduce incomplete submissions (AC11/AC12 class) by showing missing slots visually.

---

## Path C — Customer Builder Timeline First

**Files:**
- `ui/src/features/intake/prototypes/p16z21/PathTimelineFirstBanner.tsx`
- `CustomerEntryTab.tsx` — banner at top; hides default flow-step track when `timeline`

**Changes:**
- Progress banner above conversation: case_id, lifecycle tag, turn count
- Replaces IntakeFlowStepTrack with timeline-first chrome
- No backend changes; does not fix post-submit rehydrate (still needs Cap 1 wiring)

**Intent:** Trust through visible progress; preview of return-later UX without new architecture.

---

## What was NOT built

- No new API endpoints
- No CRM / WeChat integration
- No microservices
- No P17 features
- No return-later `case_id` hydrate (still Cap 1 sprint work)

---

*End of P16-Z21 Phase 3*
