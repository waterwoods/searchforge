# P16-V Phase 2 — Preview Protection Audit

**Date:** 2026-06-01  
**Project:** `ui` (`prj_EKrXJgchOmcIMNNVhYiLIcg5B7TO`)  
**Owner:** andys-projects-1f411b73 (`waterwoods`)

---

## Why Preview returns 401

Preview URLs are gated by **Vercel Deployment Protection** (Standard Protection / Vercel Authentication). Unauthenticated cold requests receive HTTP 401 and a Vercel SSO login wall — not the React app.

### Evidence chain

| Signal | Preview alias | Preview deploy URL | Production |
|--------|---------------|-------------------|------------|
| HTTP status | **401** | **401** | **200** |
| `set-cookie` | `_vercel_sso_nonce=…` | `_vercel_sso_nonce=…` | (none) |
| HTML title | `Authentication Required` | `Authentication Required` | App title |
| Body class | `sso-enabled` | `sso-enabled` | N/A |
| `x-robots-tag` | `noindex` | `noindex` | (none) |

### curl headers (2026-06-01)

**Preview alias** (`ui-waterwoods`):

```
HTTP/2 401
set-cookie: _vercel_sso_nonce=7740e7fff573c5764bd05c1a327507357039cfc26b043867; Max-Age=3600; Path=/; Secure; HttpOnly; SameSite=Lax
server: Vercel
content-type: text/html; charset=utf-8
```

**Preview deploy** (`ui-iwnyo9ufa`):

```
HTTP/2 401
set-cookie: _vercel_sso_nonce=adbc1587c0f025948ba8485ec6bb7d04cbe4f8e0e2685d79; …
```

**Production** (`ui-smoky-beta`):

```
HTTP/2 200
access-control-allow-origin: *
content-type: text/html; charset=utf-8
```

### Browser behavior (cold / incognito)

1. Navigate to `https://ui-waterwoods-andys-projects-1f411b73.vercel.app`
2. Vercel serves SSO redirect page (`Authenticating…`)
3. Auto-redirect to `https://vercel.com/sso-api?url=…`
4. Final landing: **Vercel Login page** — broker never sees product UI

**Screenshot captured:** Browser session redirected to `vercel.com/login` with SSO nonce in query string. No product UI rendered.

---

## Vercel project settings (verified via CLI)

| Field | Value |
|-------|-------|
| Project name | `ui` |
| Project ID | `prj_EKrXJgchOmcIMNNVhYiLIcg5B7TO` |
| Latest Preview deploy | `dpl_9zWWj1payFg4NuGdNVVe4C6aenwv` |
| Preview deploy URL | `https://ui-iwnyo9ufa-andys-projects-1f411b73.vercel.app` |
| Preview alias | `https://ui-waterwoods-andys-projects-1f411b73.vercel.app` |
| Deploy target | `preview` |
| Deploy status | Ready (59m ago at audit time) |
| Production URL | `https://ui-smoky-beta.vercel.app` |
| Git integration | **Not connected** (CLI deploy only) |

### Dashboard settings path (requires Andy login)

```
https://vercel.com/andys-projects-1f411b73/ui/settings/deployment-protection
```

**Agent access:** Dashboard returned login wall. Deployment Protection toggle state could not be read or changed programmatically. Inferred **ON for Preview** from deployed behavior (401 + `_vercel_sso_nonce`).

---

## Protection type determination

| Protection mode | Evidence | Verdict |
|-----------------|----------|---------|
| **Vercel Authentication (SSO)** | `_vercel_sso_nonce`, redirect to `vercel.com/sso-api`, body `sso-enabled`, title `Authentication Required` | **ACTIVE** |
| Password Protection | No password form rendered on cold load (SSO redirect fires first) | Not primary |
| Production Protection | Production returns 200 cold | **OFF or not blocking** |

The 401 is **Vercel platform SSO**, not application-level auth. The React bundle is healthy but unreachable without authenticated bypass (`vercel curl --deployment`).

---

## What works despite 401

| Check | Method | Result |
|-------|--------|--------|
| Bundle fetch | `vercel curl / --deployment ui-iwnyo9ufa` | ✅ HTML + `index-CKPYkrkL.js` |
| P16-O markers | vercel curl bundle grep | ✅ `请把您的需求发给我们` present |
| product_only | vercel curl bundle grep | ✅ `快速体验（可选）` present |
| CORS | OPTIONS from preview origin | ✅ 200 |

**Conclusion:** Build is correct; **access model is wrong** for broker trial sharing.

---

## Current state summary

| Setting | Preview | Production |
|---------|---------|------------|
| Deployment Protection | **ON (SSO)** | **OFF** (cold 200) |
| Public cold access | ❌ 401 | ✅ 200 |
| Shareable trial URL | ❌ | ⚠️ (wrong bundle) |
| Bundle content | ✅ P16-O / product_only | ❌ 41-day stale |

---

*End of P16-V Phase 2 — Preview Protection Audit*
