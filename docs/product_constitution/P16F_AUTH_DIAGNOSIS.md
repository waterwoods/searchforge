# P16-F Phase 3 — API Key / Auth Check

**Date:** 2026-05-31  
**Backend:** https://fiqa-api-g7zatxrycq-uw.a.run.app

---

## Direct API test (no browser, no Origin header)

```bash
curl -si -X POST https://fiqa-api-g7zatxrycq-uw.a.run.app/api/inbox/triage \
  -H "Content-Type: application/json" \
  -d '{"text":"客户说收到取消通知，问今天是不是必须处理"}'
```

```
HTTP/2 200
(content-type: application/json, triage payload returned)
```

Wrong field name test (`message` instead of `text`):

```
HTTP/2 400  {"detail":"text is required unless inline_image_base64 provides OCR text"}
```

This is validation, not auth.

---

## Cloud Run intake key posture

```bash
gcloud run services describe fiqa-api … | grep UNIFIED_INTAKE_INTAKE_API_KEY
# (no result — variable unset)
```

Per `services/fiqa_api/security/intake_api_gate.py`:

- When `UNIFIED_INTAKE_INTAKE_API_KEY` is **unset**, inbox routes are **anonymous_ok** (demo default).
- When set, requests need `X-Unified-Intake-Api-Key` or `Authorization: Bearer`.

---

## Frontend key sending

Grep of `ui/src/**`: **no** references to `x-intake-api-key`, `INTAKE_API`, or intake key env vars. Frontend does not send an intake API key (consistent with open demo perimeter).

CORS preflight already advertises `x-intake-api-key` in allowed headers — that is server middleware config, not evidence that a key is required today.

---

## Answers

### 1. Is endpoint anonymous?

**YES** on current Cloud Run deployment (`UNIFIED_INTAKE_INTAKE_API_KEY` not set).

### 2. Does it require intake key?

**NO** for this deployment. Direct curl succeeds without key.

### 3. Is frontend configured to send it?

**NO** — and none is required today.

### 4. Is Network Error actually auth failure or CORS?

**CORS, not auth.**

- Auth failure would typically surface as HTTP **401** with JSON `intake_api_unauthorized` (if key were configured).
- Andy sees **Network Error** on page load — matches CORS-blocked `GET /api/inbox/cases`, confirmed by OPTIONS probe.

### 5. What is safest fix?

**Add Preview origin to `ALLOWED_ORIGINS` on Cloud Run** (env patch only — no triage logic change).

Do **not** add intake API key requirement as part of this debug sprint; that would be a separate hardening change.

---

*End of P16-F Phase 3*
