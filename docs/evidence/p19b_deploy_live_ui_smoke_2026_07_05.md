# P19B Deploy + Live UI Smoke

**Date:** 2026-07-05  
**Branch:** `sprint/p16-trust-layer`  
**Scope:** Deploy P19B-2 workbench attachment UI + live smoke on stable QA URL

---

## Commits deployed

| Commit | Message |
|--------|---------|
| `7023c22` | feat: show WeCom attachments in workbench |
| `f206823` | docs: add P19B guided workflow and attachment UI recon |

Pushed to `origin/sprint/p16-trust-layer` before deploy.

---

## Backend deploy

| Field | Value |
|-------|-------|
| Script | `bash scripts/deploy_paid_pilot.sh` |
| Project | `optimal-disk-472305-e2` |
| Service | `fiqa-api` |
| Region | `us-west1` |
| **Revision** | **`fiqa-api-00150-f6h`** |
| URL | `https://fiqa-api-g7zatxrycq-uw.a.run.app` |
| DB secret | `fiqa-service-record-database-url-cloudsql-private` (unchanged) |
| Cloud SQL | `caseiq` @ `10.73.0.3` private VPC (unchanged) |
| Neon | Not used |
| WeCom callback URL | Unchanged |
| `google-cloud-storage` | Available — preview proxy returns 200 for WeCom JPEG |

No schema migration. No VPC/NAT/Secret/callback changes.

---

## Frontend deploy

| Field | Value |
|-------|-------|
| Command | `vercel deploy --yes` with `VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1`, `VITE_API_BASE_URL`, `VITE_UNIFIED_INTAKE_INTAKE_API_KEY` |
| Preview deployment | `https://ui-3cltugt32-andys-projects-1f411b73.vercel.app` |
| **Stable alias** | **`https://ui-smoky-beta.vercel.app`** |
| Target page | `/workbench/document-intake` (unchanged route) |
| Build | PASS |

Live bundle contains P19B strings: `Uploaded Documents`, `No uploaded documents yet`, `WeCom Photo`.

---

## QA gate (post-deploy)

```text
bash scripts/check_chen_kui_demo_environment.sh --cloud-api
Result: PASS — revision fiqa-api-00150-f6h, Cloud SQL aligned
```

---

## Live UI smoke — Queue

**URL:** https://ui-smoky-beta.vercel.app/workbench/document-intake

| Check | Result |
|-------|--------|
| Page loads | ✅ HTTP 200 |
| Existing demo rows (张先生/李先生/王女士/赵先生/陈女士) | ✅ Present |
| Lanes: Add Car, Policy Review, Claim Lite, Coverage Risk | ✅ Visible |
| **WeCom Photo** holding case at top | ✅ |
| Status **UNASSIGNED** on WeCom row | ✅ |
| Summary classification hint | ✅ |
| Paperclip **📎 1** on WeCom row | ✅ |

---

## Live UI smoke — Drawer (normal case, no attachments)

**Case opened:** 陈女士 · Add Car (READY)

| Check | Result |
|-------|--------|
| Next Step banner | ✅ |
| **Uploaded Documents / Attachments (0)** | ✅ |
| Empty state text | ✅ "No uploaded documents yet. Customer can send photos through WeCom." |
| Customer / Vehicle sections | ✅ |
| Copy Report / Confirm / Delete | ✅ |

---

## Live UI smoke — Drawer (WeCom Photo holding case)

**Case:** `case_82092cc39bae`  
**Attachment:** `att_92f722de864d`

| Field visible | Result |
|---------------|--------|
| Uploaded Documents / Attachments (1) | ✅ |
| Thumbnail (JPEG) | ✅ |
| Unknown document / Needs broker classification | ✅ |
| Source WeCom | ✅ |
| received_at Jul 5, 8:50 PM | ✅ |
| JPEG · 231.9 KB | ✅ |
| Binding: unknown | ✅ |
| OCR: not started | ✅ |
| Broker confirmed: no | ✅ |
| Stored | ✅ |
| UNASSIGNED + WeCom Photo tags | ✅ |
| Next Step broker attach guidance | ✅ |

---

## Preview smoke

| Check | Result |
|-------|--------|
| Preview / Open full click | ✅ Opens blob URL (axios-fetched, not public GCS) |
| Backend proxy `GET .../preview` | ✅ HTTP 200, `content-type: image/jpeg`, 237473 bytes |
| Public GCS URL in UI | ❌ Not exposed |
| `storage_uri` in API JSON | ❌ Not returned |
| `external_userid` in API JSON | ❌ Not returned |
| Full external_userid in UI | ❌ Not visible (masked customer label only) |

Cloud Run logs show preview 200s; no access token or image binary in log lines.

---

## API sanitization (live)

`GET /api/inbox/cases/case_82092cc39bae` attachment keys:

`attachment_id`, `source`, `msgtype`, `document_type`, `document_type_confidence`, `mime_type`, `size_bytes`, `received_at`, `binding_confidence`, `ocr_status`, `broker_confirmed`, `intake_status`, `preview_available`, `preview_url`, `storage_status`

Absent: `storage_uri`, `external_userid`, `media_id`, public/signed URL.

---

## Safety checklist

| Item | Status |
|------|--------|
| OCR / LLM | ❌ Not introduced |
| Schema migration | ❌ None |
| Neon | ❌ Not used |
| Public GCS URL | ❌ Not exposed |
| Cloud SQL / VPC / NAT / Secret / callback | ❌ Unchanged |
| Second Workbench page | ❌ Not created |

---

## Known issues / risks

| Issue | Severity |
|-------|----------|
| P19A note: WeCom download httpx URL may log token in some paths | Low — pre-existing; not expanded in P19B |
| Redis/Qdrant warmup errors on cold start | Non-blocking for intake (expected on intake-core deploy) |

---

## Bugfixes during deploy

None required.

---

## Recommendation

**GO for P19B final sign-off** — live Workbench shows WeCom attachments with safe preview proxy. Ready to plan P19D guided workflow; **STOP before P19C/P19D implementation**.

---

*P19B deploy + live UI smoke complete.*
