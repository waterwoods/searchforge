# P19F-1 — Workbench Drawer UX Polish

**Date:** 2026-07-07  
**Branch:** `sprint/p16-trust-layer`  
**Type:** Frontend UX polish + minimal backend preview perf logging  
**Prerequisite:** P19E-2 Progress Card ✅ CLOSED · P19F-0 performance survey ✅

**This loop:** Local dev + tests/build + evidence. **No deploy.**

---

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
| No deploy | ✅ local only |

---

## 10. Tests / Build Results

```bash
cd ui && npm run build          # PASS (19.7s)
npx tsx ui/src/features/intake/utils/attachmentDisplay.test.ts  # PASS
PYTHONPATH=. python3 -m pytest tests/test_workbench_attachment_api.py -q  # PASS (10 tests)
```

---

## 11. QA Gate Result

```bash
bash scripts/check_chen_kui_demo_environment.sh --cloud-api
# Result: PASS — QA UI + Cloud Run API + Cloud SQL aligned
# Cloud revision: fiqa-api-00163-w4k (unchanged — no deploy)
```

---

## 12. Known Limitations

- Thumbnails not implemented — full-size preview still proxied from GCS.
- CDN / signed URL not implemented.
- Cloud Run min instances not changed (cold start still possible).
- Backend `PREVIEW_PERF` logs not yet visible in production until deploy.
- Actual broker phone/browser smoke on new UX **pending** (requires deploy + manual test).
- Unified Intake tab (`BrokerWorkbenchTab`) not updated — only Document Intake drawer.

---

## 13. Deploy Verdict

| Gate | Verdict |
|------|---------|
| Code ready for deploy | **GO** — build + tests pass, scope contained |
| Broker smoke | **HOLD** — pending deploy + phone/browser verification |
| Production deploy this loop | **NO** — per P19F-1 scope |

---

*Evidence loop: P19F-1 complete. STOP — no deploy.*
