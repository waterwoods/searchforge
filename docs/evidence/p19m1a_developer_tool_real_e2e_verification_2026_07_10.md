# P19M-1A — Developer Tool Real E2E Verification

**Date:** 2026-07-10  
**Branch:** `sprint/p16-trust-layer`  
**Starting commit:** `32cf490` — feat: build Unified Claim mini program prototype foundation  
**Status:** HTTP E2E **PASS** (local); WeChat DevTools UI **NOT TESTED** (WSL/Linux)

---

## 1. Environment

| Item | Value |
|------|-------|
| OS | Linux WSL2 |
| WeChat DevTools | **Not available** on this host |
| Project mode | Native mini program, `touristappid` |
| Backend (primary) | `http://127.0.0.1:8001` (local uvicorn) |
| Backend (secondary) | Cloud Run `readyz` 200; full HTTP E2E **403** (token secret mismatch) |
| Domain validation | `urlCheck: false` in `project.config.json` |

---

## 2. Integration mode

**Mode A (local HTTP)** — **PASS**  
Shared `data/unified_intake_cases.json` + aligned `.env` / `H5_TASK_TOKEN_SECRET`.

**Mode B (Cloud Run + QA DB)** — **BLOCKED**  
Case seeded to QA Postgres; API returned `403 invalid_or_expired_task_link` (token secret alignment from this IP).

**WeChat DevTools UI** — **NOT TESTED**  
Requires Windows/macOS manual Founder verification.

---

## 3. QA task

| Field | Value |
|-------|-------|
| Label | `P19M1A-DEVTOOLS-E2E-20260711-0348` |
| Case ID | `case_ea87f0036062` |
| Masked token | `h5t1.eyJ…1506b5` |
| Real customer data | **No** — synthetic QA only |
| Workbench flag | `is_test=True` |

---

## 4. Compile result (static)

| Check | Result |
|-------|--------|
| Browser APIs (`fetch`, `localStorage`, etc.) | None found |
| `wx.request` / `wx.uploadFile` / `wx.chooseMedia` | Used correctly |
| Config compile without gitignored file | **Fixed** — `config.defaults.ts` committed |
| Page registration | All 8 pages in `app.json` |
| TypeScript | `typings.d.ts` for `IAppOption` |

**DevTools compile:** NOT TESTED (no DevTools on Linux). Static review: **likely PASS**.

---

## 5. Real E2E result (HTTP-level, mirrors mini program API)

| Step | Result | Evidence |
|------|--------|----------|
| Launch / GET intake | **PASS** | `p19m1a_devtools_e2e_smoke_20260711_0348.json` |
| Task Home semantics | **PASS** | `dashboard_summary.title` = 我的事故资料 |
| Story PATCH | **PASS** | Synthetic QA story persisted |
| Basics PATCH | **PASS** | injury/time/location/vehicle |
| Photo 1 upload | **PASS** | `customer_damage_photo` |
| Photo 2 upload | **PASS** | `other_party_vehicle_photo` |
| Review readiness | **PASS** | `current_step` = review |
| Submit (once) | **PASS** | `submitted=true`, `broker_done` false |
| Submit idempotency | **PASS** | `already_submitted=true`, 1 timeline event |
| Resume GET | **PASS** | `submitted=true`, `current_step=done` |
| Workbench readback | **PASS** | story, 2 photos, submitted phase |

**In-process E2E:** also **PASS** (`p19m1a_devtools_e2e_smoke_20260711_0346.json`).

---

## 6. Bugs found and fixed

| Symptom | Root cause | Fix |
|---------|------------|-----|
| DevTools compile may fail without `config.ts` | `require("../config")` on gitignored file | `config.defaults.ts` + optional `config.local.ts` |
| Resume token saved before API success | `persistLaunchToken` before GET | Move after successful `getTask` |
| Photo page stale after upload | No server refresh | `refreshFromServer()` on show + after upload |
| Mint script wrong env var | `UNIFIED_INTAKE_CASE_STORAGE_PATH` | `UNIFIED_INTAKE_CASES_PATH` |
| HTTP smoke used temp store vs server | Path overwrite | Respect existing `UNIFIED_INTAKE_CASES_PATH` |

---

## 7. Screenshots

**Not captured** — WeChat DevTools unavailable on WSL. Founder manual capture to `docs/evidence/screenshots/p19m1a/` when available.

---

## 8. Manual checklist (honest)

### Launch
- [x] Valid token opens task — **PASS** (HTTP)
- [ ] DevTools query launch — **NOT TESTED**
- [ ] Resume storage — **NOT TESTED** (UI); logic fixed in code
- [x] Invalid token recoverable — **PASS** (unit tests)
- [x] Full token not in evidence — **PASS**

### Task Home / Story / Basics / Photos / Review / Submit / Receipt
- [x] API flow — **PASS** (HTTP smoke)
- [ ] DevTools UI — **NOT TESTED**

### Workbench
- [x] Story, photos, timeline, submitted, broker_done false — **PASS** (enrichment API)

---

## 9. Tests

```bash
# HTTP E2E (local — start API first)
set -a && . .env && . .env.cloudrun && set +a
UNIFIED_INTAKE_CASES_PATH=data/unified_intake_cases.json \
  PYTHONPATH=. python3 scripts/p19m1a_devtools_e2e_smoke.py \
  --base-url http://127.0.0.1:8001 --shared-local-store

# In-process (no server)
PYTHONPATH=. python3 scripts/p19m1a_devtools_e2e_smoke.py --inprocess

# Regression
PYTHONPATH=. python3 -m pytest tests/test_p19m1_mini_program_logic.py \
  tests/test_h5_claim_intake_form.py \
  tests/test_p19h3i_claim_task_dashboard_always_return_h5.py \
  tests/test_p19h3h_append_first_split_later.py -q
```

All regression tests: **PASS**.

---

## 10. Remaining blockers

| Blocker | Impact |
|---------|--------|
| WeChat DevTools on Linux/WSL | UI E2E requires Founder Windows/Mac |
| Cloud Run token secret from laptop | `--qa-db` HTTP blocked (403) |
| Production domain whitelist | DevTools `urlCheck: false` for prototype |
| Official 主体/类目 | Gate 1 HOLD |

---

## 11. GO / HOLD

| Decision | Verdict |
|----------|---------|
| P19M-1A API integration | **GO** |
| P19M-1A DevTools UI E2E | **HOLD** — Founder manual |
| Real prototype demo (Founder DevTools) | **GO** with manual steps |
| UX polish (P19M-2) | After DevTools UI confirm |
| Production publish | **HOLD** |

---

## 12. Founder manual DevTools steps

1. Start local API: `bash scripts/run_demo_local.sh` (or uvicorn on 8001)
2. Mint token: `PYTHONPATH=. python3 scripts/p19m1_mint_prototype_token.py --shared-local-store` (with same env as API)
3. Copy `config.example.ts` → `config.local.ts`; set `apiBaseUrl` + optional `devTaskToken`
4. Open `miniapp/` in 微信开发者工具; **不校验合法域名**
5. Compile mode query: `token=h5t1…` (from mint output — do not commit)
6. Run manual loop; capture screenshots to `docs/evidence/screenshots/p19m1a/`

---

*No deploy. No publish. No secrets in this document.*
