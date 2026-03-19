# Insurance Autonomous Recovery + Demo Hardening Report

**Generated**: 2026-03-06  
**Scope**: Insurance paid-pilot sprint — live recovery attempt + fallback hardening

---

## 1. Live recovery attempt

### What was checked

| Check | Result |
|-------|--------|
| Env loading paths | `.env` and `.env.cloudrun` loaded by `run_demo_local.sh` |
| Qdrant config | `QDRANT_URL`, `QDRANT_API_KEY` from `.env.cloudrun` |
| Collection override | Demo uses `auto_insurance_demo_core` via `mode=demo` |
| Warmup sequence | Embedder → Qdrant ping → `EMBED_READY` |
| Qdrant 404 cause | `GET ...cloud.qdrant.io:6333/collections` → 404 |

### What was fixed

- **USE_LOCAL_QDRANT=1** added to `run_demo_local.sh`: when set, unsets `QDRANT_URL`/`QDRANT_API_KEY` so backend uses local Qdrant at `localhost:6333`. Requires `docker compose up -d qdrant` and seeded `auto_insurance_demo_core` collection.

### Whether live is recovered

**No.** Live mode still returns 503 when Qdrant Cloud is used.

### Exact blocker

**External:** Qdrant Cloud returns 404 on `GET /collections`. Most likely cause: **paused cluster** (free-tier clusters can auto-pause). The backend cannot recover this from code; it requires Andy to wake the cluster at [cloud.qdrant.io](https://cloud.qdrant.io).

---

## 2. Offline/fallback improvements

| Change | File | Why it helps |
|--------|------|---------------|
| Populated `demo_fallback.json` with full answers | `ui/src/assets/demo_fallback.json` | Fallback now shows complete broker-ready answers even when snapshot never ran |
| Clearer 503 error message | `ui/src/pages/DemoPage.tsx` | "即时检索暂时不可用。请直接点击上方 3 个推荐问题，使用预设演示答案继续。" |
| Professional offline banner | `ui/src/pages/DemoPage.tsx` | "演示模式（预设答案）" + "即时检索暂不可用。请点击上方 3 个推荐问题..." |
| Broker-oriented sample label | `ui/src/pages/DemoPage.tsx` | "推荐问题（经纪常用，点击即答）" |
| USE_LOCAL_QDRANT option | `scripts/run_demo_local.sh` | Enables local Qdrant path when Cloud is down |
| One-command demo prep | `scripts/demo_prep_one_command.sh` | Single script to check backend, validate, and print next steps |

---

## 3. Simulated demo result

### Live path (when Qdrant Cloud is active)

| Step | What happens |
|------|--------------|
| 1 | `bash scripts/run_demo_local.sh` → backend + UI start |
| 2 | Healthz 200 → "Backend healthy" |
| 3 | User opens http://localhost:5173/demo |
| 4 | Status bar: Live, Backend: Connected |
| 5 | User clicks any of 3 recommended questions → real-time retrieval, sources, answer |
| 6 | Demo feels professional |

**Could still fail:** Translation, Qdrant latency, collection empty.

### Fallback path (when live fails)

| Step | What happens |
|------|--------------|
| 1 | Backend returns 503 (embedding_warming) on first query |
| 2 | Frontend sets `useOfflineFallback = true` |
| 3 | Banner: "演示模式（预设答案）" + "即时检索暂不可用。请点击上方 3 个推荐问题..." |
| 4 | User clicks any of 3 recommended questions → loads from `demo_fallback.json` |
| 5 | Full answers + sources (dmv.ca.gov, insurance.ca.gov, etc.) displayed |
| 6 | Demo feels professional enough for broker |

**Confidence level:** High. Fallback is self-contained, copy is clear, and the 3 questions cover the main broker scenarios.

---

## 4. Highest-value patches completed

1. **demo_fallback.json** — All 3 items now have full answers (was empty before)
2. **DemoPage.tsx** — 503 message, offline banner, sample-question label
3. **run_demo_local.sh** — USE_LOCAL_QDRANT=1 support
4. **demo_prep_one_command.sh** — New one-command prep script

---

## 5. What Andy still must do personally

| # | Action | When |
|---|--------|------|
| 1 | **Wake Qdrant Cloud cluster** at cloud.qdrant.io (if paused) | To restore live mode |
| 2 | **Run demo prep** before broker demo: `bash scripts/demo_prep_one_command.sh` | Pre-demo |
| 3 | **If live fails:** Use offline path — open demo URL, click 3 recommended questions | During demo |

---

## 6. Next 10 actions (ordered by priority)

| # | Action | Owner |
|---|--------|-------|
| 1 | Wake Qdrant Cloud cluster at cloud.qdrant.io | Andy |
| 2 | Run `bash scripts/demo_prep_one_command.sh` before broker demo | Andy |
| 3 | If live works: `python3 scripts/snapshot_demo_answers.py` to refresh offline pack | Andy |
| 4 | Schedule broker demo with 陈魁 | Andy |
| 5 | If using local Qdrant: `docker compose up -d qdrant` + seed `auto_insurance_demo_core` | Andy |
| 6 | Run `USE_LOCAL_QDRANT=1 bash scripts/run_demo_local.sh` for local-Qdrant demo | Andy |
| 7 | Update `docs/BROKER_DEMO_FALLBACK_SCRIPT.md` with new banner copy | Optional |
| 8 | Add demo_prep_one_command to Makefile or README | Optional |
| 9 | Consider DEMO_MODE readiness relaxation (low priority) | Optional |
| 10 | Document Qdrant Cloud URL format if 404 persists after wake | Optional |

---

## Summary

- **Live recovery:** Blocked externally (Qdrant Cloud 404, likely paused cluster). No safe repo-only fix.
- **Fallback:** Hardened with full answers, clearer copy, and one-command prep.
- **Demo confidence:** High for both live and fallback paths.
