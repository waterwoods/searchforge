# P16-D Phase 2 — Developer Experience Audit

**Date:** 2026-05-31  
**Sprint:** P16-D — Local Developer Entry Stabilization  
**Entry point under review:** `bash scripts/run_demo_local.sh`

---

## Startup Scenarios

### 1. Andy runs `bash scripts/run_demo_local.sh`

| Step | Before P16-D | After P16-D |
|------|--------------|-------------|
| Backend | Starts on 8001, health check PASS | Unchanged |
| UI | `npm run dev` on Node 20 → **FAIL** | Auto-loads Node 22 helper → **PASS** |
| Output | Misleading "ready" with dead UI | `[INFO] Node version: v22.22.0` + Vite on :5173 |
| Workbench URL | Broken unless manual `source` | http://localhost:5173/workbench/unified-intake works |

**Andy path:** One command, no manual Node prep (assuming nvm + Node 22 installed per `NODE_22_SETUP.md`).

### 2. Cursor agent runs `bash scripts/run_demo_local.sh`

| Step | Before P16-D | After P16-D |
|------|--------------|-------------|
| Shell | WSL default Node 20.18 | Helper prepends Node 22 to PATH in script subshell |
| Backend | PASS (Python) | PASS |
| UI | FAIL — agent sees backend OK, UI silent fail | PASS — Vite starts |
| Validation | P16-C required explicit `source scripts/with_node22_path.sh` | Automatic |

**Cursor path:** Same one command; no agent memory required for Node workaround.

### 3. Clean laptop (fresh clone)

| Prerequisite | Status |
|--------------|--------|
| Python 3 + deps | Required for backend — not auto-installed by script |
| Node 22 via nvm | Required — helper warns if missing, UI fails gracefully |
| `npm install` in `ui/` | Required — not run by `run_demo_local.sh` |
| `.env` | Optional — script loads if present |

**Clean laptop path:** Still needs one-time `nvm install 22.22.0` + `cd ui && npm install`. P16-D removes the **per-session** Node PATH friction, not first-time setup.

### 4. Remaining onboarding friction

- First-time Node 22 install not automated
- `ui/node_modules` must exist before dev server starts
- Backend may need `.env` / Cloud Run keys for full triage (intake core works without Qdrant)
- No single "zero to workbench" script for truly empty machine
- Vercel Preview still requires manual deploy + env (P16-E scope)

---

## TOP_10 Developer Friction Points (ranked by ROI)

| Rank | Friction | Impact | ROI fix | Status after P16-D |
|------|----------|--------|---------|-------------------|
| 1 | **Node 20 default breaks UI on every `run_demo_local.sh`** | Blocks all local demo/validation | **Fixed** — auto-source helper | ✅ Resolved |
| 2 | **Vercel Preview not deployed** — Sprint A invisible remotely | Blocks broker/founder E2E proof | Deploy gate (P16-E) | Open |
| 3 | **`VITE_UNIFIED_INTAKE_PRODUCT_ONLY` build-time only** | Wrong UI on Production/Preview without env | Vercel env vars at deploy | Open |
| 4 | **Manual `source with_node22_path.sh` for build/deploy** | Forgotten step breaks CI-like local builds | Extend pattern to other entry scripts | Partial — trial scripts already OK |
| 5 | **First-time `npm install` not in run_demo_local** | Clean clone fails at step 3 | Add check + hint if `node_modules` missing | Open |
| 6 | **Backend warming / embedding 503** | Workbench appears broken after start | `restore_8001_readiness.sh` exists but not auto-linked | Open (documented) |
| 7 | **CORS on Preview origin** | Demo queue fails on Vercel URL | Cloud Run ALLOWED_ORIGINS update | Open (P16-E) |
| 8 | **Two runtime paths (8001 vs 8000)** | Confusion for new engineers | Documented in RUNTIME_PATH_STANDARD | Open (docs) |
| 9 | **Large repo / reduction work in working tree** | Git noise, wrong staging | P16-D git hygiene sprint pattern | Process |
| 10 | **No health check on UI bind** | Script prints "ready" before Vite actually listens | Add port probe or Vite log wait | Open (low priority) |

---

## ROI Summary

**Highest ROI fix (P16-D):** Item #1 — 5-minute code change, permanent savings on every local session for Andy, Cursor, and future engineers.

**Next highest ROI:** Item #2 + #3 — Vercel Preview with correct build args (P16-E).

---

*End of P16-D Phase 2 — Developer Experience Audit*
