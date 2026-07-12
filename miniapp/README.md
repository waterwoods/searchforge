# P19M-1 Unified Claim Mini Program Prototype

**Prototype only — not for production publish.**

## Purpose

Native WeChat Mini Program shell for the **sole Customer Task App** path (P19M-0 / P19M-0A SSOT). Implements one minimal Claim loop:

Dev/Mock Task Invitation → Open → Task Home → Story → 2 Photos → Review → Submit → Receipt → Resume → Workbench readback.

## Warnings

- No production `openid` / `unionid` binding
- No production auth or tenant admin
- No official WeChat category /主体 approval assumed
- No voice, video, Add Car, OCR, carrier integration, or formal insurance filing
- H5 remains fallback/API reference — this is **not** an H5 reskin

## Architecture

```
TaskLaunchContext (token query / dev config / resume)
  → CustomerTaskApi (facade)
    → GET/PATCH/POST /api/h5/tasks/{token}/*  (existing backend)
    → POST /api/h5/tasks/{uploadToken}/upload   (claim_evidence_pack)
  → Native pages (WXML/WXSS)
  → Broker Workbench (unchanged)
```

## Directory

```
miniapp/
  config.defaults.ts         ← committed compile-safe defaults
  config.example.ts          ← copy to config.local.ts for overrides (gitignored)
  app.json / app.ts / app.wxss
  services/ utils/ types/ pages/
```

## Setup (WeChat DevTools)

1. **Start backend** (must match token secret + case store):

```bash
bash scripts/run_demo_local.sh
# or: PYTHONPATH=. uvicorn services.fiqa_api.app_main:app --host 0.0.0.0 --port 8001
```

2. **Mint QA token** (same shell env as API — source `.env` / `.env.cloudrun`):

```bash
set -a && . .env && . .env.cloudrun && set +a
UNIFIED_INTAKE_CASES_PATH=data/unified_intake_cases.json \
  PYTHONPATH=. python3 scripts/p19m1_mint_prototype_token.py --api-base http://127.0.0.1:8001
```

3. **Optional local override:** copy `config.example.ts` → `config.local.ts` (gitignored); set `apiBaseUrl` and/or `devTaskToken`.

4. Open **`miniapp/`** in **微信开发者工具** (`touristappid` OK).

5. **详情 → 本地设置 → 不校验合法域名** (required for `http://127.0.0.1:8001`).

6. **Launch:** compile mode query `token=h5t1…` (preferred) or `devTaskToken` in `config.local.ts`.

## HTTP E2E verification (no DevTools)

Proves the same API sequence the mini program uses:

```bash
# Requires running local API + aligned env
set -a && . .env && . .env.cloudrun && set +a
UNIFIED_INTAKE_CASES_PATH=data/unified_intake_cases.json \
  PYTHONPATH=. python3 scripts/p19m1a_devtools_e2e_smoke.py \
  --base-url http://127.0.0.1:8001 --shared-local-store

# In-process (no network)
PYTHONPATH=. python3 scripts/p19m1a_devtools_e2e_smoke.py --inprocess
```

## Manual DevTools loop

1. Launch with valid `h5t1` token → Task Home (`我的事故资料`)
2. Story → Basics (if needed) → 2 photos → Review → Submit once
3. Receipt → reload app → resume same task (no new Claim)
4. Workbench: find case by QA label `P19M1A-DEVTOOLS-E2E-*`

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `ERR_CONNECTION_REFUSED` / `backend_unreachable` | Start API: `bash scripts/run_demo_local.sh`; verify `curl http://127.0.0.1:8001/healthz`. Real-device preview: set `apiBaseUrl` in `config.local.ts` to your PC **LAN IP** (not `127.0.0.1`). WSL2: use `grep nameserver /etc/resolv.conf` host IP or `hostname -I`. |
| `invalid_or_expired_task_link` | Token secret mismatch — mint with same `H5_TASK_TOKEN_SECRET` as API |
| `case_not_found` on local HTTP | Use `--shared-local-store` smoke flag; align `UNIFIED_INTAKE_CASES_PATH` |
| Upload fails | Enable 不校验合法域名; confirm GCS credentials on API |
| Compile error missing config | Use committed `config.defaults.ts`; override via `config.local.ts` |

## Developer reset

In DevTools console: import `clearPrototypeSession` from `utils/storage` logic, or clear storage keys `mp_prototype_resume_token` / `mp_prototype_submit_intent`.

## Tests

```bash
PYTHONPATH=. python3 -m pytest tests/test_p19m1_mini_program_logic.py -q
PYTHONPATH=. python3 -m pytest tests/test_h5_claim_intake_form.py \
  tests/test_p19h3i_claim_task_dashboard_always_return_h5.py \
  tests/test_p19h3h_append_first_split_later.py -q
```

*No production publishing — Gate 0 local prototype only. P19M-1A: DevTools UI verification requires Windows/macOS.*
