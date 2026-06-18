# P16 Preview Blank Page — Local Reproduction

**Sprint:** P16-PREVIEW-BLANK-PAGE-RECOVERY  
**Date:** 2026-06-07

---

## Build environment

| Item | Value |
|------|-------|
| Node (required) | v22.22.0 via `scripts/with_node22_path.sh` |
| Command | `cd ui && npm run build` |
| Pre-fix build | ✅ Succeeds (ReferenceError is runtime-only) |
| Post-fix build | ✅ Succeeds |

**Note:** Default WSL Node 20.18.2 fails Vite 7 — use Node 22.

---

## Bundle verification

| Check | Pre-fix (`index-CjaKqTZ8.js` at HEAD before import) | Post-fix |
|-------|-----------------------------------------------------|----------|
| Bare `ADD_CAR_FIELD_LABELS` in bundle | Present (count ≥ 1) | **0** occurrences |
| Build exit code | 0 | 0 |
| Build time | ~21s local | ~21s local |

---

## Local serve

```bash
export PATH="$HOME/.nvm/versions/node/v22.22.0/bin:$PATH"
cd ui && npm run build && npm run preview -- --host 0.0.0.0 --port 4173
```

| Route | Pre-fix | Post-fix |
|-------|---------|----------|
| `/workbench/unified-intake` | Blank `#root` | UI renders |
| `/workbench/unified-intake?tab=customer` | Blank | Customer First entry |
| `/workbench/unified-intake?tab=office` | Blank | Office workbench |
| `/workbench/unified-intake?tab=simulation` | Blank | Simulation controls |

---

## Typecheck / tests

| Command | Result |
|---------|--------|
| `npm run typecheck` | Skipped (scaffold placeholder in package.json) |
| Unit tests | None configured for this path |
| `run_p16_customer_status_simplification_simulations.py` | **7/7 PASS** against Cloud Run (status logic unchanged by fix) |

---

## Env shape (matched Preview)

Local build for deploy used same `-b` flags as Preview:

- `VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1`
- `VITE_UNIFIED_INTAKE_SUPERVISED_DEMO=1`
- `VITE_API_BASE_URL=https://fiqa-api-g7zatxrycq-uw.a.run.app`
- `VITE_UNIFIED_INTAKE_INTAKE_API_KEY` from `.env.cloudrun` (not logged)

---

*End of P16 Preview Blank Page Local Repro*
