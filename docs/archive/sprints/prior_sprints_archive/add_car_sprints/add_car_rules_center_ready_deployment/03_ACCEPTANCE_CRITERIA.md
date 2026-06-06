# Add-Car Rules Center Ready Deployment — Acceptance / Operational Criteria

**Sprint:** Add-Car Rules Center Ready Deployment  
**Purpose:** Practical criteria for deployment success.

---

## 1. Successful Frontend Deploy

- [ ] `cd ui && npm run build` succeeds
- [ ] `vercel --prod` completes without error
- [ ] Production alias updated
- [ ] Route `/workbench/add-car-rules` loads on production URL

---

## 2. Successful Backend Deploy

- [ ] `bash scripts/deploy_rag_demo.sh` completes
- [ ] Cloud Run service returns 200 on /healthz
- [ ] GET `/api/inbox/add-car-rules` returns JSON with `publishable` field

---

## 3. Successful Production Verification

- [ ] Production frontend route exists and loads
- [ ] Production backend returns `publishable` in GET response
- [ ] UI shows "预览模式" badge when `publishable=false`
- [ ] UI disables publish button when `publishable=false`
- [ ] UI shows warning text when in preview mode
- [ ] Editable rule fields visible
- [ ] Preview sample buttons work
- [ ] Page does not over-promise

---

## 4. What Would Block Founder Inspection

- Route 404 or blank page
- Backend 503 or missing `publishable`
- Publish button enabled when it should be disabled (misleading)
- Confusing error when clicking publish in production
- CORS or API base URL misconfiguration

---

## 5. Definition of "Good Enough"

Andy can open the page on Vercel, show Chen Kui the flow, edit a rule, run a preview, and explain honestly that "publish works locally; online we're in preview mode for now" — without confusion or embarrassment.

---

*See also: 01_SPRINT_BLUEPRINT.md, 02_EXECUTION_OUTLINE.md*
