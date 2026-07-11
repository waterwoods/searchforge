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

### Adapter seams

| Adapter | Prototype behavior |
|---------|-------------------|
| `taskLaunchContext` | `?token=h5t1…`, `config.devTaskToken`, resume storage |
| `sessionIdentityAdapter` | Anonymous mock session only |
| `mediaCaptureAdapter` | `wx.chooseMedia` photos only, max 2 demo |
| `CustomerTaskApi` | Wraps H5 routes; pages never import H5 paths |

## Directory

```
miniapp/
  app.json / app.ts / app.wxss
  config.example.ts          ← copy to config.ts
  services/                  ← API + adapters
  utils/                     ← request, storage, taskMapping
  types/
  pages/entry|task-home|story|photos|basics|review|receipt|error
```

## Setup

1. Copy `config.example.ts` → `config.ts` (gitignored).
2. Mint a QA token (local API on 8001 or Cloud Run):

```bash
PYTHONPATH=. python3 scripts/p19m1_mint_prototype_token.py --api-base http://127.0.0.1:8001
```

3. Paste `devTaskToken` into `config.ts` **or** use DevTools compile mode query `token=h5t1…`.
4. Open `miniapp/` in **微信开发者工具** (tourist AppID OK for local compile).
5. In DevTools: **详情 → 本地设置 → 不校验合法域名** (required for prototype API).

## Mock mode

If API is unreachable, entry page shows retry/error — no silent bypass. Point `apiBaseUrl` at local `http://127.0.0.1:8001` with domain check disabled.

## Backend endpoints reused

| Facade method | Backend |
|---------------|---------|
| `getTask()` | `GET /api/h5/tasks/{token}/intake` |
| `saveStory()` / `saveBasics()` | `PATCH /api/h5/tasks/{token}/fields` |
| `submitTask()` | `POST /api/h5/tasks/{token}/submit` + `X-Submit-Intent-Id` |
| `uploadPhoto()` | `POST /api/h5/tasks/{uploadToken}/upload` (from `upload_url`) |

Story field: `accident_description` (step `story`). Photos use separate `claim_evidence_pack` token from `upload_url`.

## Manual test loop

1. Launch with valid `h5t1` token → Task Home
2. Fill story → save
3. Fill basics (injury, time, location, vehicle)
4. Upload 2 photos
5. Review → Submit (once)
6. Receipt → reload app → resume same task
7. Verify Workbench shows submitted intake
8. Invalid token → error + retry

## Developer reset

Call `clearPrototypeSession()` from `utils/storage.ts` in DevTools console to clear resume token.

## STOP conditions

Stop and report if: H5 UI copied mechanically, unverified WeChat API hard-depended, scope expands beyond Claim loop, backend regressions, schema migration, or production deploy attempted.

## Tests

```bash
PYTHONPATH=. python3 -m pytest tests/test_p19m1_mini_program_logic.py -q
PYTHONPATH=. python3 -m pytest tests/test_h5_claim_intake_form.py tests/test_p19h3i_claim_task_dashboard_always_return_h5.py tests/test_p19h3h_append_first_split_later.py -q
```

*No production publishing instructions — Gate 0 approves local prototype only.*
