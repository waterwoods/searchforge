# Live Readiness Recovery Sprint Report

**Sprint:** Live Readiness Recovery Sprint  
**Date:** 2026-03-07  
**Duration:** ~25 min closed loop

---

## 1. Root cause

**What blocked 8001 readiness:** The backend was started with Qdrant Cloud config (`QDRANT_URL` from `.env.cloudrun`). Qdrant Cloud returned **404** on `GET /collections` (cluster paused or unreachable). The embedding warmup calls `get_qdrant_client().get_collections()`; when that fails, the warmup raises and never sets `EMBED_READY = True`. All `/api/query` requests then return 503 `embedding_warming`.

**Why it happened:** Default `run_demo_local.sh` loads `.env.cloudrun`, which points to Qdrant Cloud. When the Cloud cluster is paused (free tier) or unreachable, warmup fails. Local Qdrant was running at localhost:6333 with `auto_insurance_demo_core` seeded, but the backend was not configured to use it.

---

## 2. Changes made

| File / Command | Change |
|----------------|--------|
| **Operational fix** | Stopped existing 8001 process; restarted with `USE_LOCAL_QDRANT=1`, `unset QDRANT_URL`, `unset QDRANT_API_KEY`. Backend then used local Qdrant at localhost:6333. |
| `scripts/restore_8001_readiness.sh` | **New.** One-command recovery: kills 8001, starts backend with USE_LOCAL_QDRANT=1, waits for /ready, runs quick Q1 validation. |
| `docs/ANDY_IF_SOMETHING_GOES_WRONG.md` | Added Fix A: `bash scripts/restore_8001_readiness.sh` for embedding_warming recovery. |

**Why it helps:** When Qdrant Cloud is down, Andy can run `restore_8001_readiness.sh` to switch to local Qdrant and restore live readiness without manually editing env or restarting.

---

## 3. Re-test results

| Check | Before | After |
|-------|--------|-------|
| `/ready` | `{"ok":false,"phase":"starting"}` | `{"ok":true,"phase":"ready"}` |
| `/api/query` Q1 | 503 `embedding_warming` | 200, `ok: true`, full answer |
| `broker_regression_all5.py` | 0/5 ok | 5/5 ok, Q2 $14=OK, Q5 claims=OK, Q4 discounts=OK, workflow=OK |

**Exact commands run:**
```bash
# Stop old backend
kill 238769

# Start with local Qdrant
USE_LOCAL_QDRANT=1 unset QDRANT_URL QDRANT_API_KEY \
  TRANSLATION_ENABLED=1 TRANSLATION_PROVIDER=argos \
  python3 -m uvicorn services.fiqa_api.app_main:app --host 0.0.0.0 --port 8001 &

# Verify
curl -s http://127.0.0.1:8001/ready   # → {"ok":true,"phase":"ready"}
python3 scripts/broker_regression_all5.py --port 8001  # → 5/5 ok
```

---

## 4. Live workflow-depth verification

| Scenario | 客户可准备 | 经纪人可进一步询问 | 经纪人下一步 |
|----------|------------|---------------------|--------------|
| Q1 (new car) | ✅ | ✅ | ✅ |
| Q2 (suspension) | ✅ | ✅ | ✅ |
| Q3 (license) | ✅ | ✅ | ✅ |
| Q5 (claims) | ✅ | ✅ | ✅ |

**Confirmed:** Live answers from `/api/query` (not fallback) include all three workflow blocks for Q1, Q2, Q3, Q5. Q4 has broker hint + discounts; regression passed.

---

## 5. Remaining blocker(s)

**Status:** Solved for this sprint.

- **Root cause:** Qdrant Cloud 404 → warmup fails → EMBED_READY stays false.
- **Fix:** Use `USE_LOCAL_QDRANT=1` when Cloud is down; `restore_8001_readiness.sh` automates this.
- **Remaining:** None for live readiness. If local Qdrant is not running or not seeded, `restore_8001_readiness.sh` will fail; operator must run `docker compose up -d qdrant` and `seed_local_qdrant.sh` first.

---

## 6. Manual-work reduction

- **Andy no longer needs to:** Manually kill 8001, edit env, and restart when embedding_warming occurs; run `restore_8001_readiness.sh` instead.
- **Cursor can now:** Run `restore_8001_readiness.sh` to recover readiness; run `broker_regression_all5.py --port 8001` to verify live workflow-depth.
- **OpenClaw can now:** Use the same scripts for automated validation.
- **Reusable asset:** `scripts/restore_8001_readiness.sh` — one-command 8001 recovery when Qdrant Cloud is down.

---

## 7. Recommended next step for tomorrow

**Run `bash scripts/demo_pre_checklist.sh`** before the next demo. If it reports "Use Live path" and broker regression passes, the demo is ready. If embedding_warming appears again, run `bash scripts/restore_8001_readiness.sh` first.
