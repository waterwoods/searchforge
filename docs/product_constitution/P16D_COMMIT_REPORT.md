# P16-D Phase 5 — Commit Report

**Date:** 2026-05-31  
**Sprint:** P16-D — Local Developer Entry Stabilization  

---

## Commit

| Field | Value |
|-------|-------|
| **Hash** | `c92cabf` |
| **Branch** | `sprint-a/broker-front-door` |
| **Message** | Fix local demo startup with Node 22 helper |

---

## Files changed

| File | Change |
|------|--------|
| `scripts/run_demo_local.sh` | Modified |
| `docs/product_constitution/P16D_ROOT_CAUSE.md` | Added |
| `docs/product_constitution/P16D_DEV_EXPERIENCE_AUDIT.md` | Added |
| `docs/product_constitution/P16D_VALIDATION.md` | Added |
| `docs/product_constitution/P16D_GIT_REVIEW.md` | Added |
| `docs/product_constitution/P16D_PREVIEW_READY.md` | Added |
| `docs/product_constitution/P16D_FINAL_REVIEW.md` | Added |

---

## Stats

| Metric | Value |
|--------|-------|
| Files changed | 7 |
| Insertions | 440 |
| Deletions | 1 |
| `run_demo_local.sh` delta | +18 / −1 lines |

---

## Core change

`run_demo_local.sh` now sources `scripts/with_node22_path.sh` before `npm run dev`, with `[INFO]`/`[WARN]` diagnostics and `SKIP_NVM_NODE22_FOR_UI=1` escape hatch.

---

*End of P16-D Phase 5 — Commit Report*
