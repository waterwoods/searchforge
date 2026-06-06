# P16-C Phase 5 — Preview Readiness Gate

**Date:** 2026-05-31  
**Branch:** `sprint-a/broker-front-door` @ `c2e3dff`  
**Question:** Should Andy create a Vercel Preview?

---

## Answer: **YES**

Create a **Vercel Preview** (not Production) to validate Sprint A on a shareable URL before merge or Chen Kui access.

---

## Required Reasoning

### Product readiness

| Check | Status |
|-------|--------|
| Sprint A code complete on branch | ✅ `c2e3dff` |
| Default broker tab | ✅ Verified local product_only |
| Engineer chrome hidden | ✅ Verified local |
| Wayfinding + inline practice | ✅ Verified local |
| Demo queue E2E | ⚠️ Not verified remote |
| Guardrail regression | ✅ PASS |
| Triage API (Cloud Run) | ✅ `/readyz` + smoke 5/5 |

**Verdict:** Product **code** is ready for Preview validation. Not ready for unsupervised Chen Kui or Production.

### UX readiness

| Check | Status |
|-------|--------|
| 5-minute North Star (simulation) | **64–72** depending on demo queue |
| First 30 seconds orientation | ✅ **73 avg** across personas |
| Residual Add-Car copy | ⚠️ P1 — not Preview blocker |
| Empty queue first load | ⚠️ Acceptable if demo queue works |

**Verdict:** UX **ready for founder Preview review**. Not ready for broker self-serve until Preview E2E PASS.

### Trial readiness

| Check | Status |
|-------|--------|
| Cap 1 trial-ready | **Conditional** — needs deployed Preview |
| Commercial pack (pricing, terms) | ❌ Sprint B |
| 7-day trial process | ❌ Not started |
| Production Postgres validation | ❌ Parallel track |
| Chen Kui unsupervised URL | ❌ **NO-GO** until Preview + kickoff |

**Verdict:** Preview is the **correct next gate** — not trial launch.

---

## Exact Deployment Checklist (if YES)

### Pre-deploy

- [ ] Confirm branch: `git checkout sprint-a/broker-front-door && git log -1` → `c2e3dff`
- [ ] Confirm guardrail: `bash scripts/guardrail_inbox_triage.sh` → PASS
- [ ] Confirm UI build: `source scripts/with_node22_path.sh && cd ui && VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1 VITE_API_BASE_URL=https://fiqa-api-g7zatxrycq-uw.a.run.app npm run build`

### Deploy Preview (CLI — immediate)

```bash
cd /home/andy/searchforge/ui
source ../scripts/with_node22_path.sh

vercel deploy --yes \
  -b VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1 \
  -b VITE_API_BASE_URL=https://fiqa-api-g7zatxrycq-uw.a.run.app
```

- [ ] Record printed URL: `https://ui-________.vercel.app`

### Post-deploy env (persistent — before Production)

```bash
cd ui
vercel env add VITE_UNIFIED_INTAKE_PRODUCT_ONLY preview    # value: 1
vercel env add VITE_UNIFIED_INTAKE_PRODUCT_ONLY production # value: 1
vercel env add VITE_API_BASE_URL preview                   # value: Cloud Run URL
```

### CORS (if demo queue fails)

- [ ] Add Preview origin to Cloud Run `ALLOWED_ORIGINS`
- [ ] Retest 「加载演示队列」 → progress → cancellation auto-open

### Andy 5-minute dry-run on Preview URL

- [ ] Fresh incognito → `/workbench/unified-intake`
- [ ] Default tab = 办公室工作台
- [ ] Zero engineer labels in screenshot
- [ ] Click 「取消/付款风险」 → paste fills → 开始整理 → case card
- [ ] Click 「加载演示队列」 → progress → cancellation visible
- [ ] Confirm 我的办理 + 场景仿真 absent

### Gate outcomes

| Outcome | Next step |
|---------|-----------|
| Preview dry-run PASS | Merge to main; plan Production redeploy with env |
| Preview dry-run FAIL | Fix P0 only (CORS, env, API); no new features |
| Chen Kui demo | Supervised kickoff on Preview URL only |

---

## Blocker List (if answer were NO)

*Not applicable — gate is YES. For reference, these would block Preview:*

1. Sprint A code not merged to deployable branch — **false** (branch exists)
2. Guardrail FAIL — **false** (PASS)
3. UI build broken — **false** (build PASS on Node 22)
4. Explicit founder cancel — **not indicated**

**What still blocks Production / Chen Kui (not Preview):**

1. No persistent `VITE_UNIFIED_INTAKE_PRODUCT_ONLY` on Vercel  
2. Production alias serves pre-Sprint A UI  
3. No founder dry-run on Preview  
4. Sprint B commercial pack missing  
5. No 7-day trial evidence  

---

## Preview vs Production Decision Matrix

| Action | Verdict |
|--------|---------|
| Create Vercel Preview | **YES** ✅ |
| Merge to main | **After** Preview PASS |
| Vercel Production deploy | **NO** |
| Chen Kui unsupervised trial URL | **NO** |
| Supervised founder demo on Preview | **YES** (after deploy) |

---

*End of P16-C Phase 5 — Preview Readiness Gate*
