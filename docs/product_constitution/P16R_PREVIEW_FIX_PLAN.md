# P16-R Phase 5 — Preview Fix Plan

**Date:** 2026-06-01  
**Goal:** Preview = Local (bundle + runtime + cold URL)

---

## Current state (post Phase 8 partial execution)

| Step | Status |
|------|--------|
| Commit P16-O | ✅ `d05e94d` |
| Push branch | ✅ `origin/sprint-a/broker-front-door` |
| Preview deploy with `-b` flags | ✅ `ui-iwnyo9ufa` |
| CORS for new Preview origin | ✅ `ui-iwnyo9ufa` in Cloud Run |
| Persist Preview dashboard env | ❌ Blocked (no Git on Vercel project) |
| Disable SSO | ❌ Not done — **still 401** |

---

## Exact steps to make Preview = Local

### A. Code (done)

| # | Action | Commit | Verify |
|---|--------|--------|--------|
| A1 | Commit P16-O + ui_copy + UnifiedIntakePage | `d05e94d` | `git log -1` |
| A2 | Push `sprint-a/broker-front-door` | remote `d05e94d` | `git ls-remote` |

### B. Deploy (done — must repeat on every change)

```bash
cd ui
vercel deploy --yes \
  -b VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1 \
  -b VITE_API_BASE_URL=https://fiqa-api-g7zatxrycq-uw.a.run.app
```

| Verify | Command / evidence |
|--------|-------------------|
| Bundle has P16-O | `grep -o '请把您的需求发给我们' <bundle>` count ≥ 1 |
| Bundle has broker trial | `粘贴客户消息` count ≥ 6 |
| Alias | `vercel inspect <url>` lists `ui-waterwoods` |

### C. Environment (remaining)

| # | Action | Owner | Verify |
|---|--------|-------|--------|
| C1 | Vercel → link GitHub repo **or** add Preview env for all branches in dashboard | Andy/Eng | `vercel env ls` shows Preview column |
| C2 | `VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1` Preview | Eng | rebuild without `-b` still passes grep |
| C3 | `VITE_API_BASE_URL` Preview | Eng | build succeeds without `-b` |
| C4 | Disable **Deployment Protection** on Preview (Standard Protection → off) | Andy | `curl -I` → **200** not 401 |
| C5 | After each new Preview deploy: patch `ALLOWED_ORIGINS` + `.env.cloudrun` | Eng | OPTIONS 200 |

### D. Verification (Andy — required)

| # | Action | Evidence |
|---|--------|----------|
| D1 | Open `https://ui-waterwoods-…/workbench/unified-intake` logged out | Screenshot 200 + paste box |
| D2 | Paste cancellation notice → queue → draft → copy | 15-min log |
| D3 | `?tab=customer` on product_only URL → redirects broker | Screenshot |
| D4 | Customer path on **full dev** or dedicated customer URL | P16-O empty state screenshot |

---

## Commit / push / deploy sequence (canonical)

```
1. git commit  (P16-O + broker on sprint-a/broker-front-door)
2. git push origin sprint-a/broker-front-door
3. vercel deploy --yes -b VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1 -b VITE_API_BASE_URL=<cloud run>
4. gcloud run services update … ALLOWED_ORIGINS=…,<new-preview-host>,…
5. vercel inspect → note URL + alias
6. bundle grep + curl OPTIONS CORS
7. Andy cold-browser E2E (after SSO off)
```

---

## Done definition (Preview = Local)

- [x] Same commit family (`d05e94d`) deployed
- [x] P16-O strings in bundle
- [x] P16-I broker strings in bundle
- [x] product_only flag baked
- [x] API CORS for Preview origin
- [ ] Cold URL returns 200 (SSO)
- [ ] Dashboard env persisted (no `-b` required)
- [ ] Andy signed E2E log

---

*End of P16-R Phase 5 — Preview Fix Plan*
