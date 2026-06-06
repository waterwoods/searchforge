# P16-V Phase 3 — Safe Removal Plan

**Date:** 2026-06-01  
**Action under review:** Disable Vercel Deployment Protection for **Preview only**  
**Owner required:** Andy (`waterwoods`) — Vercel dashboard

---

## Exact change plan

### Step 1 — Open Vercel Deployment Protection settings

```
https://vercel.com/andys-projects-1f411b73/ui/settings/deployment-protection
```

### Step 2 — Disable protection for Preview deployments only

| Setting | Before (inferred) | After (target) |
|---------|-------------------|----------------|
| Preview Deployment Protection | **Standard Protection / Vercel Authentication ON** | **OFF** |
| Production Deployment Protection | OFF (cold 200 confirmed) | **UNCHANGED — leave OFF** |

Do **not** enable protection on Production. Do **not** change Password Protection unless explicitly needed.

### Step 3 — Verify (no redeploy required)

```bash
curl -sI https://ui-waterwoods-andys-projects-1f411b73.vercel.app | head -5
# Expected: HTTP/2 200 (no _vercel_sso_nonce)

bash scripts/post_sprint_check.sh
# Expected: 10/10 PASS
```

**Estimated time:** ~5 minutes

---

## Safety questions

### Will removing Preview protection expose secrets?

**No meaningful additional exposure.**

| Asset | Risk assessment |
|-------|-----------------|
| Vercel env vars (`VITE_API_BASE_URL`, `VITE_UNIFIED_INTAKE_PRODUCT_ONLY`) | Encrypted at rest on Vercel; baked into JS bundle at build time — already extractable via `vercel curl` today |
| API keys / DB credentials | Not in frontend bundle; live in Cloud Run Secret Manager |
| Cloud Run API | Already public HTTPS; CORS-restricted to known origins |
| Broker trial UI | Designed for external broker access — protection currently **blocks** intended use |

The Preview bundle is already readable by anyone with Vercel team access or CLI auth. Disabling SSO removes an **artificial distribution blocker**, not a security boundary that protects secrets.

### Will Preview remain safe?

**Yes, for trial purposes.**

| Control | Status |
|---------|--------|
| `x-robots-tag: noindex` | Already set on protected responses; likely persists |
| No multi-tenant data | Single pilot broker context |
| No Stripe / payment in scope | Out of pilot scope |
| API CORS | Restricted to registered origins (`ui-iwnyo9ufa`, aliases) |
| App auth | None by design (broker paste trial) |

Preview becomes **publicly reachable** — same as Production today. Acceptable for Chen Kui trial URL sharing.

### Will Production be affected?

**No.**

Vercel Deployment Protection is configured **per environment** (Preview vs Production). Disabling Preview protection does not change Production settings. Production currently returns cold HTTP 200 and will continue to serve `ui-smoky-beta` unchanged until an explicit `vercel deploy --prod`.

---

## What NOT to do

| Action | Why avoid |
|--------|-----------|
| Disable Production protection (if ever enabled) | Not needed; Production already public |
| Promote to Production in same step | P16-V scope: Preview only; prod promote is separate gate |
| Add bypass tokens as permanent solution | Workaround for automation, not broker cold access |
| Modify application code | No code change fixes platform SSO |

---

## Rollback plan

If Preview should be re-protected after trial:

1. Re-enable Deployment Protection for Preview in same dashboard path
2. Verify `curl -I` returns 401 again
3. Runner will return to 8/10 — expected if protection restored

---

## Approval gate

| Question | Answer |
|----------|--------|
| Safe to apply? | **YES** — Preview-only toggle, no prod impact, no secret exposure |
| Agent can apply? | **NO** — requires Andy Vercel dashboard session |
| Blocks 10/10 runner? | **YES** — sole remaining automated FAIL |

---

*End of P16-V Phase 3 — Safe Removal Plan*
