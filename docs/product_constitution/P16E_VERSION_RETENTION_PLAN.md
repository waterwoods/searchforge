# P16-E Version Retention Plan

**Goal:** Andy can compare Sprint A Preview vs Production and roll back safely.

---

## Policy

| Surface | Count | Action |
|---------|-------|--------|
| **Production** | **One only** | Keep `ui-smoky-beta.vercel.app` unchanged until explicit Production deploy after merge approval |
| **Preview (Sprint A)** | **One canonical** | Keep https://ui-fvxlrxp4u-andys-projects-1f411b73.vercel.app until merge or superseding Preview |
| **Git tag** | **One after approval** | `sprint-a-preview` — do **not** create until Andy says yes |

Do **not** maintain multiple Production deployments or aliases for comparison.

---

## Comparison workflow for Andy

1. **Sprint A Preview:** URL above (Vercel login may be required).
2. **Baseline Production:** https://ui-smoky-beta.vercel.app/workbench/unified-intake (pre-Sprint A).
3. Document differences in founder notes; do not redeploy Production for A/B.

---

## After Andy approval (commands — do not run yet)

```bash
git tag sprint-a-preview c92cabf
git push origin sprint-a-preview
```

Optional: annotate tag message with Preview URL and deployment ID `dpl_9g9SJYNDNxgKKE872M9Adq1REvKN`.

---

## Rollback

| If… | Then… |
|-----|--------|
| Preview bad | Redeploy older Preview from Vercel dashboard or `vercel ls` → pick prior Preview URL |
| Production accidentally promoted | Re-alias to last known-good Production deployment in Vercel (40d deployment still listed) |
| Git rollback | `git checkout sprint-a-preview` or reset branch — **only after tag exists** |

---

*End of P16-E Version Retention Plan*
