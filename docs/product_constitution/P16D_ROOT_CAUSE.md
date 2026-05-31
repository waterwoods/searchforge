# P16-D Phase 0 — Root Cause Analysis

**Date:** 2026-05-31  
**Sprint:** P16-D — Local Developer Entry Stabilization  
**Scope:** Why `run_demo_local.sh` backend PASS / frontend FAIL on WSL default Node  

---

## Context

P16-C validated Sprint A locally using `source scripts/with_node22_path.sh` before UI commands. The default founder entry `bash scripts/run_demo_local.sh` did **not** source that helper — causing silent frontend failure on environments where Node 20 is default.

---

## 1. Why backend succeeds

| Factor | Detail |
|--------|--------|
| Runtime | Python 3 + uvicorn — **no Node dependency** |
| Start command | `python3 -m uvicorn services.fiqa_api.app_main:app --host 0.0.0.0 --port 8001` |
| Health check | `curl -sf http://127.0.0.1:8001/healthz` — independent of Node |
| WSL default | System Python works out of the box |

Backend path in `run_demo_local.sh` never touches Node. On WSL with Node 20.18, uvicorn starts and `/healthz` returns OK within the 60s wait loop.

---

## 2. Why frontend fails

| Factor | Detail |
|--------|--------|
| UI stack | Vite **7.2.x** (`ui/package.json`) |
| Node requirement | Vite 7: **Node >= 20.19** OR **Node >= 22.12** |
| Repo policy | `.nvmrc` + `engines.node`: **>= 22.22.0** |
| WSL default | **Node 20.18.2** — below both Vite floor and repo policy |
| Failure mode | `npm run dev` → Vite refuses to start or exits with engine error |
| Script gap | `run_demo_local.sh` ran `npm run dev` on default PATH without Node 22 prep |

Symptom chain:

```
bash scripts/run_demo_local.sh
  → [1] Backend PASS (Python)
  → [2] Health check PASS
  → [3] npm run dev FAIL (Node 20.18 < required)
  → User sees "backend healthy" but blank/broken UI
```

P16-C discovery #6 and regression #8 documented this as dev UX friction — not broker-facing, but blocks every local validation session.

---

## 3. Why Node 22 workaround succeeds

`scripts/with_node22_path.sh`:

1. Reads required version from `.nvmrc` (`22.22.0`)
2. Prepends `$HOME/.nvm/versions/node/v22.22.0/bin` to PATH if installed
3. Falls back to `nvm use 22` via `nvm.sh` if direct path missing
4. **Must be sourced** (not executed) — modifies caller shell PATH

After sourcing:

```
node -v  →  v22.22.0
npm run dev  →  Vite 7 starts on :5173
```

P16-C validation used this pattern explicitly. Trial scripts (`trial_readiness_check.sh`, etc.) already source the helper automatically. Only `run_demo_local.sh` — the primary founder entry — was missing it.

---

## 4. Safest permanent fix

**Source `with_node22_path.sh` inside `run_demo_local.sh` before UI startup.**

| Requirement | How fix satisfies it |
|-------------|---------------------|
| Backend unchanged | Helper sourced only at step [3], after backend start |
| No new nvm dependency | Reuses existing helper; nvm only if already installed |
| No breaking existing envs | `SKIP_NVM_NODE22_FOR_UI=1` escape hatch preserved |
| Clear diagnostics | `[INFO] Loading Node 22 helper…` + `[INFO] Node version: v22.x.x` |
| Graceful degradation | If helper missing → `[WARN]` + continue (same as before) |

**Not chosen:**

- Pin Vite to 6.x — fights repo policy, loses security/features
- Document-only fix — P16-C proved engineers forget manual `source`
- Require global Node 22 install — breaks clean laptops without nvm
- Wrap npm in nvm shell — heavier than PATH prepend

---

## Summary

| Layer | Root cause | Fix |
|-------|------------|-----|
| Backend | None — works | No change |
| Frontend | Node 20 on PATH when Vite 7 starts | Auto-source `with_node22_path.sh` in `run_demo_local.sh` |
| Operator | Manual workaround required | One-line fix, permanent |

---

*End of P16-D Phase 0 — Root Cause Analysis*
