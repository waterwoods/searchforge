# P16-Q Phase 1 — Preview Verification

**Date:** 2026-06-01  
**Sprint:** P16-Q Reality Validation  
**Method:** `vercel ls`, `vercel inspect`, `vercel curl`, HTTP headers, bundle string grep, repo git state  
**Constraint:** No code changes. Evidence only.

---

## Latest Preview URL

| Field | Value |
|-------|-------|
| **Primary URL** | https://ui-fvxlrxp4u-andys-projects-1f411b73.vercel.app/workbench/unified-intake |
| **Alias** | https://ui-waterwoods-andys-projects-1f411b73.vercel.app |
| **Deployment ID** | `dpl_9g9SJYNDNxgKKE872M9Adq1REvKN` |
| **Status** | ● Ready (Preview) |
| **Age at verification** | ~20 hours (created Sun May 31 2026 02:55:28 PDT) |

---

## Git / Branch / Commit

| Field | Value | Verified? |
|-------|-------|-----------|
| **Repo branch (HEAD)** | `sprint-a/broker-front-door` | ✅ |
| **Repo commit (HEAD)** | `901b0dfaee67c4e954a0d866a7a5675cfbeb4836` | ✅ |
| **Commit message** | `P16-I simplify product-only intake UI` | ✅ |
| **Commit date** | 2026-05-31 08:50:49 PDT | ✅ |
| **Vercel → git SHA (inspect)** | Not exposed in CLI output | ⚠️ Unconfirmed |
| **P16-O customer changes on HEAD** | **No** — P16-O exists as **uncommitted local diff** only | ✅ Critical |

**Reality:** Preview was deployed ~18 hours after P16-I commit. P16-O (2026-06-01) was never committed or deployed.

---

## Deployment Time

| Event | Timestamp |
|-------|-----------|
| Preview deploy created | 2026-05-31 02:55:28 PDT |
| Production `last-modified` (HTTP) | 2026-05-30 11:01:17 GMT (~43h older than Preview) |
| Local HEAD commit | 2026-05-31 08:50:49 PDT |

Preview is the newest **deployed** frontend. Production alias is a **different, older bundle**.

---

## Environment Variables

### Vercel dashboard (`vercel env ls`)

| Variable | Environments | Persisted? |
|----------|--------------|------------|
| `VITE_API_BASE_URL` | Production only | ✅ Encrypted |
| `VITE_UNIFIED_INTAKE_PRODUCT_ONLY` | **Not listed** | ❌ **Missing** |
| Preview-specific env vars | **None visible** | ❌ |

**Reality:** `VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1` was documented as CLI-injected on last Preview deploy (P16-J), not persisted. Redeploy without CLI flag would revert to full dev UI.

### Runtime API (Preview builds)

| Variable | Value |
|----------|-------|
| Remote API | `https://fiqa-api-g7zatxrycq-uw.a.run.app` (from P16-J baseline; CORS patched P16-G) |
| Local demo API | `http://127.0.0.1:8001` |

### Local stack (this verification run)

| Variable | Value |
|----------|-------|
| `UNIFIED_INTAKE_PRODUCT_ONLY` | `1` (backend) |
| `VITE_UNIFIED_INTAKE_PRODUCT_ONLY` | `1` (UI :5173) |
| `VITE_API_BASE_URL` | `http://127.0.0.1:8001` |
| `/readyz intake_path_ready` | `true` |

---

## HTTP Access Tests

| URL | Cold HTTP | Product loads? |
|-----|-----------|----------------|
| Preview primary | **401** + `_vercel_sso_nonce` cookie | ❌ Vercel Deployment Protection |
| Preview alias | **401** | ❌ Same |
| Preview via `vercel curl` (bypass) | **200** | ✅ HTML + `index-97qCgvUS.js` |
| Production alias | **200** | ✅ Loads — **wrong bundle** (see below) |

**Cold broker/customer cannot use Preview URL without Vercel account or bypass secret.**

---

## Bundle Reality Check

Strings grep in deployed JS (`index-97qCgvUS.js` via `vercel curl`):

| String | Preview deploy | Meaning |
|--------|----------------|---------|
| `粘贴客户消息` | ✅ 6× | Sprint A product_only broker copy present |
| `办理加车报价` | ✅ 8× | Add-car chrome still in bundle |
| `请把您的需求发给我们` | ❌ absent | **P16-O customer landing NOT deployed** |
| `发送给办公室` | ❌ absent | **P16-O CTA NOT deployed** |

Production bundle (`index-ctrXdUgj.js` on `ui-smoky-beta`):

| String | Production | Meaning |
|--------|------------|---------|
| `办理加车报价` | ✅ 8× | Pre–Sprint A customer-first chrome |
| `粘贴客户消息` | ✅ 3× | Partial broker strings |
| P16-O / P16-I product_only markers | ❌ | **Not a trial-ready broker URL** |

Browser snapshot on Production (2026-06-01): **4 tabs visible** (客户报送 default, 场景仿真, 办公室工作台). `?tab=broker` **ignored** — stays on customer tab.

---

## Guardrail / API (local, same commit family)

| Check | Result |
|-------|--------|
| `guardrail_inbox_triage.sh` | **PASS** |
| `run_inbox_triage_scenarios.py` | **64/64** (rules fallback; OpenAI 429 quota) |
| `demo_quick_validate.sh` | **PASS** |

Engine is healthy locally. **Deploy surface ≠ local surface.**

---

## Phase 1 Verdict

| Claim | Reality |
|-------|---------|
| "Latest Preview has P16-O customer UX" | **FALSE** — P16-O uncommitted |
| "Preview is broker-stable URL" | **FALSE** — 401 SSO for cold users |
| "Preview has product_only" | **LIKELY TRUE** (bundle grep) but **not dashboard-persisted** |
| "Production is safe fallback" | **FALSE** — older full dev UI, wrong default tab |
| "Andy can verify Preview in browser" | **Requires Vercel login** — still not logged this sprint |

**Blocking gap unchanged since P16-J:** no authenticated Andy E2E on Preview; no deploy of P16-O; no env var persistence.

---

*End of P16-Q Phase 1 — Preview Verification*
