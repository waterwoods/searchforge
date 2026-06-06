# P16-F Phase 1 — Frontend Env Inspection

**Date:** 2026-05-31  
**Preview:** https://ui-fvxlrxp4u-andys-projects-1f411b73.vercel.app  
**Method:** `vercel inspect`, `vercel ls`, `vercel curl` (protection bypass), bundle grep on `index-97qCgvUS.js`

---

## Commands run

```bash
vercel ls                                    # Preview deployment listed (Ready, 3h)
vercel inspect https://ui-fvxlrxp4u-…        # target: preview, id dpl_9g9SJYNDNxgKKE872M9Adq1REvKN
vercel env ls                                # saved vars audit
vercel curl -y "/" --deployment https://ui-fvxlrxp4u-…   # HTML → index-97qCgvUS.js
vercel curl -y "/assets/index-97qCgvUS.js" --deployment … # bundle grep
```

Local parity build (validation):

```bash
VITE_API_BASE_URL=https://fiqa-api-g7zatxrycq-uw.a.run.app \
VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1 npm run build
```

---

## Saved Vercel dashboard env

| Variable | Production | Preview | Development |
|----------|------------|---------|-------------|
| `VITE_API_BASE_URL` | ✅ Encrypted | ❌ Missing | ❌ Missing |
| `VITE_UNIFIED_INTAKE_PRODUCT_ONLY` | ❌ Missing | ❌ Missing | ❌ Missing |

This deployment used **CLI build flags** (`-b`) per P16-E, not saved Preview env.

---

## Bundle evidence (`index-97qCgvUS.js`)

| Check | Result |
|-------|--------|
| API host | `fiqa-api-g7zatxrycq-uw.a.run.app` only |
| Stale localhost / old API | **None found** |
| Product-only UX strings | `经纪人：请在本页`, `原样粘贴微信`, `取消/付款风险`, `办公室工作台` |
| Hidden-tab strings (dead code) | `客户报送`, `场景仿真`, `我的办理` still in bundle but runtime-gated |

---

## Answers

### 1. Is product-only active?

**YES.** Build was deployed with `VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1`. Bundle contains product-only wayfinding and practice-scenario copy; env var name is dead-code-eliminated (expected Vite behavior).

### 2. Is API base URL correct?

**YES.** Single API host in bundle: `https://fiqa-api-g7zatxrycq-uw.a.run.app` (no trailing slash issues observed).

### 3. Is Preview calling the expected backend?

**YES (intent).** `ui/src/api/config.ts` uses `VITE_API_BASE_URL` in production builds; bundle confirms Cloud Run URL. Browser requests from Preview origin are blocked by CORS before/ during response — not because the URL is wrong.

### 4. Is there any stale API URL in bundle?

**NO.** Grep found only `fiqa-api-g7zatxrycq-uw.a.run.app`. No `localhost`, no alternate Cloud Run hostnames.

---

*End of P16-F Phase 1*
