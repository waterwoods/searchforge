# P19F-1 — Workbench Drawer UX Polish

**Date:** 2026-07-07  
**Branch:** `sprint/p16-trust-layer`  
**Type:** Frontend UX polish + minimal backend preview perf logging  
**Prerequisite:** P19E-2 Progress Card ✅ CLOSED · P19F-0 performance survey ✅

**This loop:** Local dev + deploy + browser smoke prep.

**Verdict:** **DEPLOY PASS** · **QA gate PASS** · **Automated browser smoke PASS (partial)** · **Andy broker smoke PENDING**

---

## 14. Deploy (2026-07-07)

### Commits pushed

| Commit | Message |
|--------|---------|
| `5b6f8ed` | feat: polish Workbench drawer loading experience |

```bash
git push origin sprint/p16-trust-layer   # 4f1818e..5b6f8ed
```

### Frontend deploy

| Field | Value |
|-------|-------|
| Command | `vercel deploy --prod --yes` with `VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1`, `VITE_API_BASE_URL`, `VITE_UNIFIED_INTAKE_INTAKE_API_KEY` |
| Production deployment | `https://ui-ciig5nevj-andys-projects-1f411b73.vercel.app` |
| **Stable alias** | **`https://ui-smoky-beta.vercel.app`** |
| Target route | `/workbench/document-intake` — HTTP 200 |
| Build | PASS (~38s on Vercel) |
| Bundle check | Contains `WORKBENCH_DRAWER_OPEN`, `正在加载预览`, `预览加载失败`, `Refreshing case details` |

### Backend deploy

| Field | Value |
|-------|-------|
| Script | `bash scripts/deploy_paid_pilot.sh` |
| Project | `optimal-disk-472305-e2` |
| Service | `fiqa-api` |
| Region | `us-west1` |
| **Revision (prior)** | `fiqa-api-00163-w4k` |
| **Revision (this deploy)** | **`fiqa-api-00164-8c9`** |
| URL | `https://fiqa-api-g7zatxrycq-uw.a.run.app` |
| GIT_SHA | `5b6f8edaf` |
| Deploy time (UTC) | 2026-07-07 ~20:15 UTC |
| `/health/live` | 200 |
| `/readyz` | 200 (`intake_core_readiness: true`) |
| DB secret | `fiqa-service-record-database-url-cloudsql-private` — unchanged |
| Cloud SQL | `caseiq` @ `10.73.0.3` private VPC — unchanged |
| Neon | Not QA truth |
| WeCom callback / VPC / NAT / min instances | unchanged |

---

## 15. Post-deploy QA gate

```bash
bash scripts/check_chen_kui_demo_environment.sh --cloud-api
# Result: PASS — revision fiqa-api-00164-8c9, Cloud SQL aligned
```

---

## 16. Log check (post-deploy)

Revision `fiqa-api-00164-8c9` startup + runtime logs reviewed (~80 lines):

- **No** import/syntax errors
- **No** Postgres read facade errors
- **No** preview endpoint exceptions at startup
- Expected optional warnings only: embedding warmup deferred, Qdrant/Redis optional

**PREVIEW_PERF sample** (after automated browser opened WeCom case drawer):

```
PREVIEW_PERF case_id=case_82092cc39bae attachment_id=att_92f722de864d total_ms=857.0 gcs_ms=190.3 bytes=237473 status=ok
```

No storage_uri, VIN, phone, or external_userid in log line.

---

## 17. Workbench browser smoke checklist

**URL:** https://ui-smoky-beta.vercel.app/workbench/document-intake  
**Revision:** `fiqa-api-00164-8c9` · **GIT_SHA:** `5b6f8ed` · **Alias:** `ui-smoky-beta`

### Smoke A — Drawer opens

| # | Action | Expected | Automated result |
|---|--------|----------|------------------|
| A1 | Click **Open** on WeCom Photo case | Drawer opens quickly | **PASS** |
| A2 | Observe header / status / Next Step | Visible before images finish | **PASS** — UNASSIGNED + WeCom Photo tags, Next Step card, Customer card rendered first |
| A3 | No long full-drawer blank spinner | Text visible immediately | **PASS** — no centered Spin; `Refreshing case details` absent after hydrate |

### Smoke B — Attachments area

| # | Action | Expected | Automated result |
|---|--------|----------|------------------|
| B1 | Scroll to attachments panel | Below customer / text content | **PASS** |
| B2 | Attachment metadata | Doc type, source, status badges visible | **PASS** — "Unknown document", WeCom/Unassigned/Accepted tags |
| B3 | Loading placeholder | Gray skeleton + "正在加载预览…" while loading | **HOLD** — image loaded fast; strings present in bundle |
| B4 | Image appears | Progressive per attachment | **PASS** — preview image visible |

### Smoke C — Lazy load

| # | Action | Expected | Automated result |
|---|--------|----------|------------------|
| C1 | Text not blocked by images | Known facts / status render first | **PASS** |
| C2 | Images load independently | No drawer crash | **PASS** |
| C3 | Multiple images stagger | One-by-one acceptable | **PENDING** — Andy manual with multi-image case |

### Smoke D — Retry behavior

| # | Action | Expected | Automated result |
|---|--------|----------|------------------|
| D1 | Simulate preview failure | "预览加载失败" + Retry | **PENDING** — not triggered in automated run; retry UI in bundle |

### Smoke E — Logs

| # | Check | Expected | Automated result |
|---|-------|----------|------------------|
| E1 | Browser console | `WORKBENCH_DRAWER_OPEN`, `WORKBENCH_CASE_DETAIL_LOADED`, preview events | **PENDING** — Andy DevTools; bundle contains event names |
| E2 | Cloud Run logs | `PREVIEW_PERF … status=ok` | **PASS** — sample above |
| E3 | No PII in logs | No VIN / storage_uri / phone | **PASS** |

---

## 18. Updated known limitations

- Thumbnails not implemented — full-size preview still proxied from GCS.
- CDN / signed URL not implemented.
- Cloud Run min instances not changed (cold start still possible).
- Unified Intake tab (`BrokerWorkbenchTab`) not updated — only Document Intake drawer.
- Full-size GCS proxy latency remains (~857ms total for one sample image).
- Andy manual DevTools + multi-image / retry smoke still pending.

---

## 19. Deploy verdict

| Gate | Verdict |
|------|---------|
| Feature commit pushed | **GO** — `5b6f8ed` on remote |
| Frontend deployed | **GO** — `ui-smoky-beta.vercel.app` |
| Backend deployed | **GO** — `fiqa-api-00164-8c9` |
| QA gate | **GO** |
| Logs clean | **GO** |
| Automated browser smoke | **GO** (partial — A/B/C core paths) |
| Andy broker smoke | **HOLD** — manual DevTools + multi-image + retry pending |

---

*Evidence loop: P19F-1 deploy complete. STOP — awaiting Andy broker browser smoke.*

## 1. Goal

Make the Workbench drawer feel faster for brokers by:

1. Text-first render (case header, known facts, checklist before images)
2. Attachment skeleton / placeholder while previews load
3. Image lazy load (IntersectionObserver + stagger)
4. Preview / drawer latency logs
5. No thumbnails, CDN, OCR, schema migration, or Cloud config changes

---

## 2. P19F-0 Source Findings

From `docs/p19f0_workbench_performance_scale_survey.md`:

- At ~1,000 users, broker-perceived slowness comes from **N× preview proxy + full GCS download**, not Postgres.
- Case text / known facts return in one API call; images require separate preview fetches.
- Recommended paid-pilot minimum: **text-first render + skeleton + lazy load + latency logs**.

---

## 3. Changed Files

| File | Change |
|------|--------|
| `ui/src/pages/DocumentIntakeInboxPage.tsx` | Text-first drawer open from queue stub; partial refresh indicator; attachments moved below text |
| `ui/src/features/intake/components/CaseAttachmentsPanel.tsx` | Skeleton placeholders, lazy preview, retry on failure, stagger |
| `ui/src/features/intake/utils/workbenchPerfLog.ts` | **New** — frontend perf event helpers |
| `services/fiqa_api/inbox_triage/case_attachment_api.py` | GCS download timing via contextvar |
| `services/fiqa_api/routes/inbox_triage.py` | `PREVIEW_PERF` log on preview endpoint |

---

## 4. Before / After UX Behavior

### Before

- `openCase()` set `detailLoading=true` and the entire drawer showed a centered `Spin`.
- Broker saw blank/spinner for 1–3+ seconds until case GET returned.
- All image previews fetched immediately on mount (N concurrent proxy calls).
- Failed preview showed a generic icon with no retry.
- Attachments panel rendered **above** customer / known facts.

### After

- Drawer opens immediately with queue-row stub data (header, status, known facts, checklist).
- Subtle "Refreshing case details…" line while full case GET hydrates in background.
- Attachments panel renders **after** text content (customer, vehicle, known facts).
- Each image shows gray placeholder + spinner + "正在加载预览…" until loaded.
- Previews load only when thumbnail enters viewport (IntersectionObserver, 80px rootMargin).
- Staggered fetch: 120ms × index to avoid thundering herd.
- Failed preview shows "预览加载失败" + Retry button; drawer stays usable.
- Empty attachment state unchanged (explicit message, not blank).

---

## 5. Text-First Render

- `openCase()` finds `rows[].raw` stub from list API and sets `detail` immediately.
- `createWorkbenchPerfSession()` fires `WORKBENCH_DRAWER_OPEN` on open.
- Full `getSavedCase()` hydrates in background; `WORKBENCH_CASE_DETAIL_LOADED` logs `caseGetMs`.
- If stub unavailable, `Skeleton` shows instead of full-drawer spin.
- On fetch error with stub present, stub remains visible (graceful degradation).

---

## 6. Skeleton Behavior

`PreviewPlaceholder` component per attachment:

- **Loading:** gray 96×96 box, `Spin`, "正在加载预览…"
- **Failed:** icon, "预览加载失败", Retry link
- **Non-image / no preview:** static file-type icon (unchanged)
- Metadata (doc type, source, status badges) always visible immediately

---

## 7. Lazy Load Behavior

- `IntersectionObserver` on thumbnail container; disconnects after first intersection.
- Fetch deferred until `inView=true`.
- Stagger: `previewIndex * 120ms` delay per image.
- Security unchanged: still uses auth-gated preview proxy blob fetch; no public GCS URL.

---

## 8. Latency Logs Added

### Frontend (`console.info`)

| Event | Fields |
|-------|--------|
| `WORKBENCH_DRAWER_OPEN` | `case_id` (shortened), `attachmentCount` |
| `WORKBENCH_CASE_DETAIL_LOADED` | `case_id`, `caseGetMs`, `attachmentCount` |
| `WORKBENCH_FIRST_PREVIEW_LOADED` | `case_id`, `firstPreviewMs` |
| `WORKBENCH_ALL_PREVIEWS_LOADED` | `case_id`, `allPreviewMs`, loaded/failed counts |
| `WORKBENCH_PREVIEW_FAILED` | `case_id`, `failedPreviewCount` |

No PII, VIN, phone, storage_uri, media_id, or external_userid logged.

### Backend (`logger.info`)

```
PREVIEW_PERF case_id=… attachment_id=… total_ms=… gcs_ms=… bytes=… status=ok|not_found|error
```

- `gcs_ms` captured via `contextvars` during GCS download only (0 for local file attachments).
- No storage URI or signed tokens logged.

---

## 9. Security Constraints (Verified)

| Constraint | Status |
|------------|--------|
| No public GCS URL | ✅ unchanged — preview proxy only |
| No GCS exposure | ✅ storage_uri never sent to frontend |
| No schema migration | ✅ none |
| No OCR | ✅ none introduced |
| No Cloud config change | ✅ none |
| No CDN / signed URL | ✅ none |
| No thumbnail generation | ✅ none |
| No Progress Card change | ✅ untouched |

---

## 10. Tests / Build Results

```bash
cd ui && npm run build          # PASS (19.7s)
npx tsx ui/src/features/intake/utils/attachmentDisplay.test.ts  # PASS
PYTHONPATH=. python3 -m pytest tests/test_workbench_attachment_api.py -q  # PASS (10 tests)
```

---

## 11. Pre-deploy QA Gate Result

```bash
bash scripts/check_chen_kui_demo_environment.sh --cloud-api
# Result: PASS — QA UI + Cloud Run API + Cloud SQL aligned
# Cloud revision (pre-deploy): fiqa-api-00163-w4k
```

---

## 12. Pre-deploy Known Limitations

- Thumbnails not implemented — full-size preview still proxied from GCS.
- CDN / signed URL not implemented.
- Cloud Run min instances not changed (cold start still possible).
- Unified Intake tab (`BrokerWorkbenchTab`) not updated — only Document Intake drawer.

---

## 13. Pre-deploy Verdict

| Gate | Verdict |
|------|---------|
| Code ready for deploy | **GO** — build + tests pass, scope contained |

---
