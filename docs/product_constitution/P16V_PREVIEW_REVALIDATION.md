# P16-V Phase 5 — Preview Revalidation

**Date:** 2026-06-01  
**Context:** Phase 4 fix **not applied** — revalidation confirms blocker persists  
**Methods:** curl, cold browser (no Vercel session), runner-equivalent checks

---

## Test matrix

| Test | URL | Method | Expected (post-fix) | Actual |
|------|-----|--------|---------------------|--------|
| Cold curl HEAD | `ui-waterwoods` alias | `curl -sI` | HTTP 200 | **HTTP 401** ❌ |
| Cold curl HEAD | `ui-iwnyo9ufa` deploy | `curl -sI` | HTTP 200 | **HTTP 401** ❌ |
| SSO cookie absent | alias | grep `_vercel_sso_nonce` | no match | **present** ❌ |
| Incognito browser | alias | navigate cold | Product UI | **Vercel Login** ❌ |
| Authenticated bypass | deploy | `vercel curl /` | 200 + HTML | **200** ✅ |
| Runner `preview_url_reachable` | alias | post_sprint_check | PASS | **FAIL** ❌ |
| Runner `preview_protection_absent` | alias | post_sprint_check | PASS | **FAIL** ❌ |

---

## curl evidence

```bash
# Preview alias — FAIL
$ curl -sI https://ui-waterwoods-andys-projects-1f411b73.vercel.app | awk '/^HTTP|set-cookie|x-robots/'
HTTP/2 401
set-cookie: _vercel_sso_nonce=7740e7fff573c5764bd05c1a327507357039cfc26b043867; …
x-robots-tag: noindex

# Production — PASS (control)
$ curl -sI https://ui-smoky-beta.vercel.app | awk '/^HTTP/'
HTTP/2 200
```

---

## Browser evidence (cold session)

| Step | Observation |
|------|-------------|
| Open Preview URL | Redirect to Vercel SSO |
| Final URL | `https://vercel.com/login?next=%2Fsso-api%3Furl%3D…ui-waterwoods…` |
| Login wall | Yes — email / Google / GitHub options |
| Product UI | **Not reached** |

Production control (`/workbench/unified-intake`): **200**, stale customer-portal UI loads without login.

---

## Revalidation verdict

| Criterion | Result |
|-----------|--------|
| HTTP 200 on Preview | ❌ |
| No login wall | ❌ |
| Broker can open shared link | ❌ |
| Runner Preview checks | ❌ 2/2 FAIL |

**Phase 5: FAIL** — revalidation blocked pending Andy SSO toggle.

---

## Post-fix checklist (for Andy, ~2 min after toggle)

```bash
curl -sI https://ui-waterwoods-andys-projects-1f411b73.vercel.app | head -1
# → HTTP/2 200

curl -s https://ui-waterwoods-andys-projects-1f411b73.vercel.app | grep -o 'index-[A-Za-z0-9]*\.js'
# → index-CKPYkrkL.js

bash scripts/post_sprint_check.sh
# → 10/10 PASS
```

Open Preview in incognito → expect broker paste UI (`请把您的需求发给我们`), not Vercel login.

---

*End of P16-V Phase 5 — Preview Revalidation (FAIL — fix not applied)*
