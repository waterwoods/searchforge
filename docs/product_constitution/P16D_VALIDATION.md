# P16-D Phase 3 — Validation Report

**Date:** 2026-05-31  
**Sprint:** P16-D — Local Developer Entry Stabilization  
**Branch:** `sprint-a/broker-front-door`

---

## Static checks

| Command | Result |
|---------|--------|
| `bash -n scripts/run_demo_local.sh` | **PASS** |
| `bash -n scripts/with_node22_path.sh` | **PASS** |

---

## Node 22 helper

```bash
source scripts/with_node22_path.sh
node -v
```

| Check | Result |
|-------|--------|
| Default PATH before source | `v20.18.2` |
| After source | **v22.22.0** |
| Helper visible | **PASS** |

---

## Simulated startup path

Reproduced the UI branch of `run_demo_local.sh` (source helper → `cd ui` → `npm run dev`):

| Check | Result |
|-------|--------|
| Node after helper in script context | **v22.22.0** |
| Vite starts | **PASS** — `VITE v7.2.2 ready in 148 ms` |
| Bind address | `http://localhost:5173/` |
| Backend path | **Unchanged** — not modified in P16-D |

Full `run_demo_local.sh` end-to-end was not left running (long-lived process); UI simulation confirms the fixed path works. Backend startup logic was not touched.

---

## Environment notes

| Item | Status |
|------|--------|
| WSL Node default | 20.18.2 (expected failure without helper) |
| nvm Node 22.22.0 | Installed at `$HOME/.nvm/versions/node/v22.22.0/bin` |
| Blockers | **None** for P16-D fix validation |

---

## Verdict

**P16-D local entry fix: VALIDATED**

- Backend startup unchanged
- Frontend path uses Node 22 via auto-sourced helper
- Vite 7 dev server starts successfully

---

*End of P16-D Phase 3 — Validation Report*
