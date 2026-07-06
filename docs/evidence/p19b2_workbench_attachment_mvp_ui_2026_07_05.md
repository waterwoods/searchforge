# P19B-2 — Workbench Attachment MVP UI

**Date:** 2026-07-05  
**Branch:** `sprint/p16-trust-layer`  
**Scope:** Enhance existing `/workbench/document-intake` — no new page, no deploy

---

## Product confirmation

| Item | Status |
|------|--------|
| P19B = Workbench raw attachment visibility | ✅ |
| OCR | **Out of scope** — badge `not_started` only |
| Raw image = evidence | ✅ thumbnail + open full via auth proxy |
| OCR status UI | `not_started` / `unavailable` / future pending label only |
| Broker confirmation | **Not implemented** |
| Customer guided buttons | **Not implemented** |
| Schema migration | **None** |
| Public GCS URL | **Not exposed** |
| Neon as QA truth | **Not used** |

---

## UI placement

**Page:** `/workbench/document-intake` (`DocumentIntakeInboxPage.tsx`)

**Drawer order (P19B):**

1. Status tags  
2. Next Step  
3. Missing Items (if NEED_INFO)  
4. **Uploaded Documents / Attachments (N)** ← new  
5. Customer / Vehicle / Sources / Warnings  
6. Actions  

**Queue:**

- Same Office Review Queue table (no new URL)
- `wecom_media_intake` rows: lane **WeCom Photo**, status **UNASSIGNED**, sorted to top
- Paperclip column: `📎 N` when attachments present

---

## Changed files

| File | Change |
|------|--------|
| `services/fiqa_api/inbox_triage/case_attachment_api.py` | **New** — sanitize API fields, GCS preview resolver |
| `services/fiqa_api/routes/inbox_triage.py` | Sanitize list/get case; `GET .../preview` proxy |
| `ui/src/features/intake/components/CaseAttachmentsPanel.tsx` | **New** — drawer attachment section |
| `ui/src/features/intake/utils/attachmentDisplay.ts` | **New** — display helpers |
| `ui/src/features/intake/utils/attachmentDisplay.test.ts` | **New** — node unit test |
| `ui/src/pages/DocumentIntakeInboxPage.tsx` | Queue + drawer integration |
| `ui/src/api/inboxTriage.ts` | Extended `CaseAttachment` type |
| `tests/test_workbench_attachment_api.py` | **New** — backend tests |

---

## API shape (sanitized `case_attachments[]`)

```json
{
  "attachment_id": "att_…",
  "source": "wecom",
  "msgtype": "image",
  "document_type": "unknown_document",
  "document_type_confidence": "unknown",
  "mime_type": "image/jpeg",
  "size_bytes": 237473,
  "received_at": "2026-07-05T…",
  "binding_confidence": "unknown",
  "ocr_status": "not_started",
  "broker_confirmed": false,
  "intake_status": "unassigned",
  "preview_available": true,
  "preview_url": "/api/inbox/cases/{case_id}/attachments/{attachment_id}/preview",
  "storage_status": "stored"
}
```

**Stripped from API responses:** `storage_uri`, `external_userid`, `media_id`, full `wecom_external_userid` on case.

---

## Preview endpoint (Option A)

`GET /api/inbox/cases/{case_id}/attachments/{attachment_id}/preview`

- Auth-gated (same office access as other case routes)
- WeCom: streams from private GCS via backend (`gs://` never sent to browser)
- Local web uploads: streams from filesystem path
- `Content-Type` set from blob metadata
- No signed/public URL persisted or returned

---

## Tests

| Suite | Result |
|-------|--------|
| `tests/test_workbench_attachment_api.py` | 8 passed |
| `tests/test_wecom_media_intake.py` | 26 passed |
| WeCom regression bundle (7 files) | 137 passed |
| `npx tsx ui/src/features/intake/utils/attachmentDisplay.test.ts` | PASS |
| `npm run build` (ui) | PASS |
| `bash scripts/check_chen_kui_demo_environment.sh --cloud-api` | PASS |

---

## Local smoke notes

- QA gate uses live Cloud SQL (`fiqa-service-record-database-url-cloudsql-private`); revision `fiqa-api-00149-jj4` does **not** include P19B code yet.
- P19A holding case `case_82092cc39bae` / `att_92f722de864d` visible only after backend+frontend deploy.
- Local JSON fixture tests confirm drawer metadata + preview proxy behavior with mocked GCS.

---

## Known gaps

| Gap | Loop |
|-----|------|
| Live UI smoke on QA Vercel | After deploy |
| OCR draft / broker confirm | P19C |
| Slot editor / guided upload buttons | P19D |
| `BrokerWorkbenchTab` parity | Optional post-P19B |
| Vitest in `package.json` | Used `tsx` one-off for helper test |

---

## Deploy / GO recommendation

| Check | Status |
|-------|--------|
| Code complete locally | ✅ |
| Tests pass | ✅ |
| QA gate (pre-deploy baseline) | PASS |
| Frontend deploy | **Not done** (per STOP) |
| Backend deploy | **Not done** (per STOP) |

**Recommendation: GO for P19B deploy + live UI smoke** after single revision deploy (API first, then Vercel UI). Until deploy, live QA drawer will not show attachments.

---

*P19B-2 complete — STOP before P19C/P19D.*
