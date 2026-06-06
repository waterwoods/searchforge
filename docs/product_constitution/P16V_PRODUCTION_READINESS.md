# P16-V Phase 7 — Production Promotion Readiness

**Date:** 2026-06-01  
**Rule:** DO NOT deploy to Production during P16-V  
**Question:** If Andy approves Preview today, can Production safely receive the same build?

---

## Short answer

**Not yet.** Preview must pass cold-access gate first. Once Preview is 10/10 and Andy completes E2E, Production promotion is **technically straightforward** but carries **UX regression risk** for any existing Production users until validated.

---

## Preconditions before Production promote

| # | Gate | Status |
|---|------|--------|
| 1 | Preview cold HTTP 200 | ❌ FP-004 |
| 2 | `post_sprint_check.sh` 10/10 | ❌ 8/10 |
| 3 | Andy 15-min Preview E2E log | ❌ blocked on #1 |
| 4 | Preview bundle = promote target | ✅ `index-CKPYkrkL.js` |
| 5 | Production env vars set | ✅ `VITE_UNIFIED_INTAKE_PRODUCT_ONLY` saved (not deployed) |
| 6 | CORS includes prod origin | ✅ |

---

## If Andy approves Preview (SSO off + E2E pass)

### Can Production safely receive the same build?

**Conditional YES** — with explicit founder sign-off after Preview E2E.

| Factor | Assessment |
|--------|------------|
| Same commit family | ✅ `d05e94d` already deployed to Preview |
| Build flags | ✅ `-b VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1 -b VITE_API_BASE_URL=…` documented |
| API compatibility | ✅ `/readyz` ready; CORS already includes prod |
| Rollback | ✅ Redeploy previous prod deployment via Vercel dashboard |

---

## Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| **Default tab change** (customer → broker) | P0 | FP-016 — validate with Andy before promote; brokers may expect current prod GTM |
| **product_only hides customer tab** | P1 | Intentional for trial; document for Chen Kui |
| **Stale prod users bookmark old flows** | P2 | Communicate URL unchanged; behavior changes |
| **Preview env not persisted in dashboard** | P1 | Next Preview deploy without `-b` flags may revert UI — link Git or add Preview env vars |
| **CORS drift on new preview hash** | P2 | Patch ALLOWED_ORIGINS on each manual deploy |
| **Promote before E2E** | P0 | Do not promote until Preview paste loop verified |

---

## Missing items

| Item | Owner | Blocker |
|------|-------|---------|
| Preview SSO off | Andy | FP-004 |
| Andy deployed E2E log | Andy | FP-010 / FP-015 |
| Preview env vars in dashboard | Eng/Andy | Git not linked |
| Commercial pack (invoice, pricing) | Andy | FP-009 (Day 7, not Day 0) |
| Observation log row 1 | Andy | Trial protocol |

---

## Rollback plan

### Production rollback (if promote goes wrong)

1. Vercel dashboard → `ui` project → Deployments
2. Find last known-good Production deployment (`index-ctrXdUgj.js` era)
3. **Promote to Production** on that deployment
4. Verify `curl -sI https://ui-smoky-beta.vercel.app` → 200
5. Confirm bundle hash reverts to `index-ctrXdUgj.js`

**Time:** ~5 minutes  
**Data impact:** None (frontend-only; API unchanged)

### Preview rollback (if SSO re-enabled)

Re-enable Deployment Protection → Preview returns 401 → runner 8/10 (expected)

---

## Recommended promote sequence (post Preview gate)

```
1. Andy: disable Preview SSO → verify 10/10 runner
2. Andy: 15-min Preview E2E (paste → queue → draft → copy)
3. Eng: vercel deploy --prod -b VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1 -b VITE_API_BASE_URL=<cloud run>
4. bash scripts/post_sprint_check.sh --production https://ui-smoky-beta.vercel.app
5. Andy: smoke prod in incognito
```

**Estimated time:** ~25 min after SSO fix

---

## Production readiness verdict

| Question | Answer |
|----------|--------|
| Ready to promote today? | **NO** |
| Ready after Preview 10/10 + E2E? | **YES (conditional)** |
| Safe rollback available? | **YES** |

---

*End of P16-V Phase 7 — Production Promotion Readiness*
