# Add-Car Quote 80% Completion Deploy Sprint — Acceptance / Operational Criteria

**Sprint:** Add-Car Quote 80% Completion Deploy Sprint  
**Date:** 2025-03-16

---

## 1. Successful Backend Deploy

- `bash scripts/deploy_rag_demo.sh` exits 0
- Cloud Run service URL returned
- `curl <URL>/healthz` returns 200
- `curl <URL>/readyz` returns 200 (or acceptable if Qdrant warming)

---

## 2. Successful Frontend Deploy (if needed)

- `npm run build` succeeds
- `vercel --prod` succeeds
- Production URL accessible
- Frontend env points at production backend (VITE_API_BASE_URL or equivalent)

---

## 3. Successful Production Verification

- Add-car first turn: "我想加一台X5" → reply asks for year/zip or next missing thing; handoff_ready=False
- Add-car second turn: "90210" (after vehicle+zip) → reply asks delivery/driver; handoff_ready=False
- Add-car third turn: delivery or driver added → handoff_ready=True
- Founder can open Vercel URL and run Simulation Assistant add-car scenarios

---

## 4. What Would Block Founder Inspection

- Backend deploy failed
- Backend health/readyz failing
- Frontend pointing at wrong backend (localhost or stale URL)
- Add-car flow still hands off at turn 2 with zip-only (old behavior)

---

*See: SPRINT_BLUEPRINT.md, EXECUTION_OUTLINE.md*
