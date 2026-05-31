# P16-D Phase 7 — Preview Readiness Decision

**Date:** 2026-05-31  
**Sprint:** P16-D — Local Developer Entry Stabilization  
**Prior gate:** P16-C answered YES to Preview (code-ready)

---

## Are we ready for Preview deploy?

## **YES**

P16-D removed the last **local validation blocker** (Node 20 UI failure). Sprint A code was already Preview-ready per P16-C. Local founder path now matches trial script behavior.

---

## Remaining blockers (none for Preview)

| Blocker | Status after P16-D |
|---------|-------------------|
| Node 20 breaks local UI | **Resolved** |
| Sprint A code on branch | ✅ `sprint-a/broker-front-door` |
| Guardrail PASS | ✅ P16-C validated |
| UI build on Node 22 | ✅ Validated |
| Vercel Preview deployed | ❌ **Not yet — P16-E action** |
| Persistent Vercel env | ❌ P16-E post-deploy |
| CORS for Preview origin | ⚠️ May need post-deploy fix |
| Andy 5-minute dry-run | ❌ After Preview URL exists |

---

## Exact next command sequence (P16-E)

```bash
# 1. Confirm branch and guardrail
git checkout sprint-a/broker-front-door
bash scripts/guardrail_inbox_triage.sh

# 2. Build verify (Node 22 auto via helper)
source scripts/with_node22_path.sh
cd ui && VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1 \
  VITE_API_BASE_URL=https://fiqa-api-g7zatxrycq-uw.a.run.app \
  npm run build

# 3. Deploy Vercel Preview
cd /home/andy/searchforge/ui
source ../scripts/with_node22_path.sh
vercel deploy --yes \
  -b VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1 \
  -b VITE_API_BASE_URL=https://fiqa-api-g7zatxrycq-uw.a.run.app

# 4. Record URL → Andy incognito dry-run (P16-C checklist)
# 5. If demo queue fails → add Preview origin to Cloud Run ALLOWED_ORIGINS
```

---

## Verdict

**Local entry:** Ready  
**Preview deploy:** Ready to execute (P16-E)  
**Production / Chen Kui unsupervised:** Still NO

---

*End of P16-D Phase 7 — Preview Readiness Decision*
