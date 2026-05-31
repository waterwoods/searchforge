# P16-D Phase 4 — Git Hygiene Review

**Date:** 2026-05-31  
**Sprint:** P16-D — Local Developer Entry Stabilization  
**Branch:** `sprint-a/broker-front-door`

---

## git status (P16-D scope)

Files intentionally staged for this commit:

| File | Action | P16-D relevance |
|------|--------|-----------------|
| `scripts/run_demo_local.sh` | Modified | **Core fix** — auto-source Node 22 helper before UI |
| `docs/product_constitution/P16D_ROOT_CAUSE.md` | New | Phase 0 root cause |
| `docs/product_constitution/P16D_DEV_EXPERIENCE_AUDIT.md` | New | Phase 2 audit |
| `docs/product_constitution/P16D_VALIDATION.md` | New | Phase 3 validation |
| `docs/product_constitution/P16D_GIT_REVIEW.md` | New | This document |

**Not staged (explicit exclusion):**

- Archive / reduction work (100+ deleted docs)
- Unrelated UI product changes
- `AGENTS.md`, `Makefile`, `docker-compose.yml`, etc.
- Prior uncommitted `run_demo_local.sh` improvements (Unified Intake messaging, RUN_DEMO_LAB mode) — remain in working tree after commit

---

## Staged diff summary (`run_demo_local.sh`)

**Insertions:** Node 22 helper block (~18 lines) + comment update  
**Deletions:** Direct `cd ui && npm run dev` without Node prep  
**Backend path:** Unchanged  
**Behavior:** Sources `with_node22_path.sh` when present; warns if missing; respects `SKIP_NVM_NODE22_FOR_UI=1`

---

## Commit scope discipline

- Did **not** use `git add .`
- Staged only P16-D script fix + constitution docs
- Commit message scoped to local demo startup / Node 22 helper

---

*End of P16-D Phase 4 — Git Hygiene Review*
