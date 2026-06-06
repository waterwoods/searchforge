# P16-F Phase 4 — Browser-Level Reproduction

**Date:** 2026-05-31  
**Target:** https://ui-fvxlrxp4u-andys-projects-1f411b73.vercel.app/workbench/unified-intake  
**Test message:** 客户说收到取消通知，说如果今天不处理保险就会断掉。他问现在怎么办，已经很着急。

---

## Automation status

| Tool | Result |
|------|--------|
| Cursor IDE browser MCP | **Blocked** — redirects to Vercel Login (Deployment Protection / SSO) |
| Raw `curl` | **Blocked** — `Authentication Required` HTML |
| `vercel curl` (CLI bypass) | **HTML + JS bundle only** — no DOM interaction |

**Screenshot:** Not captured — automation never reached workbench UI (stopped at Vercel login). Andy's authenticated session is required for live DOM/network capture.

---

## Inferred reproduction (code path + CORS probes + Andy report)

### Expected page load sequence

1. `UnifiedIntakePage` resolves initial tab → **`broker`** when `productOnlyUi` is true (`resolveInitialTab`).
2. `BrokerWorkbenchTab` mounts and immediately calls `loadRecent()` → `GET {API_BASE}/api/inbox/cases`.
3. Browser sends `Origin: https://ui-fvxlrxp4u-andys-projects-1f411b73.vercel.app`.
4. Cloud Run CORS middleware rejects origin → preflight/response blocked.
5. Axios throws network error → UI sets error banner with CORS hint.

Relevant UI code:

```274:277:ui/src/features/intake/components/BrokerWorkbenchTab.tsx
            const msg =
                typeof raw === 'string' && /network error/i.test(raw)
                    ? `${raw}（若控制台有 CORS 提示，请确认地址栏域名与后端 ALLOWED_ORIGINS 一致，优先打开生产别名 URL。）`
                    : raw;
```

### Observed (Andy + probes)

| Field | Value |
|-------|--------|
| **Console error** | Expected: CORS policy blocked request to `https://fiqa-api-g7zatxrycq-uw.a.run.app/api/inbox/cases` (browser DevTools — not captured by agent) |
| **Failed request URL** | `https://fiqa-api-g7zatxrycq-uw.a.run.app/api/inbox/cases` (initial load); paste/triage would hit `…/api/inbox/triage` |
| **Response status** | **None visible to JS** (CORS block — network layer failure, not HTTP 401/500) |
| **User-facing error** | `Network Error（若控制台有 CORS 提示…）` |
| **Default tab** | **Expected:** 办公室工作台 (bundle + source confirm product_only default; DOM not verified on Preview) |
| **Paste/triage test message** | Would fail same CORS path if queue error did not already degrade trust |

### Likely root cause

**Cloud Run `ALLOWED_ORIGINS` missing Preview hostname** — confirmed by OPTIONS returning `Disallowed CORS origin`.

---

## What Andy can still verify manually (authenticated)

1. Confirm address bar origin matches `ui-fvxlrxp4u-…`
2. Open DevTools → Network → filter `cases` and `triage`
3. Confirm red failed requests to `fiqa-api-g7zatxrycq-uw.a.run.app` with CORS message in console
4. Confirm UI shell (wayfinding, paste box, practice scenarios) renders despite API failure

---

*End of P16-F Phase 4*
