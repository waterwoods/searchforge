# P19H-3h-1F — Append-first, Split-later Manual WeCom Checklist

**Date:** 2026-07-10  
**Policy:** Append-first, Split-later (先归档，后拆分)  
**Prerequisite:** Backend deploy with P19H-3h-1F patch  
**Environment:** Chen pilot WeCom KF (post-deploy)

---

## Pre-check

- [ ] Branch `sprint/p16-trust-layer` deployed to pilot backend
- [ ] Claim H5 MVP live (`p19h-claim-h5-mvp-predeploy-20260710` baseline)
- [ ] Broker Workbench accessible for timeline verification

---

## Manual retest steps

| # | Customer action | Expected | Pass |
|---|-----------------|----------|------|
| 1 | Send「我要理赔」 | H5 Start Card / intake link; no injury menu for new case | |
| 2 | Send ordinary accident narrative (e.g. 昨天在 Santa Ana 红绿灯被追尾) | Append ack or H5 continue; **no**「新事故？」confirm | |
| 3 | Send「进度」 | Status Card with current phase | |
| 4 | Send「补充一下，对方保险是 State Farm」 | Append to current Claim; no collision card | |
| 5 | Send「这是另一个事故」 | Explicit confirm card **or** broker warning; not silent new case | |
| 6 | Open Broker Workbench | Timeline shows all supplements; no duplicate case unless step 5 confirmed new | |
| 7 | (If multi-open exists) Ordinary supplement | Appends to newest Claim; `possible_multi_claim_context` flag on Workbench | |

---

## Workbench verification

- [ ] All WeCom supplements visible on single Claim timeline
- [ ] `possible_multi_claim_context` shown when multiple open Claims exist
- [ ] No customer-facing multi-case picker
- [ ] H5 continue link on Status Card when intake not submitted
- [ ] No H5 continue link after H5 submit / broker review phase

---

## Regression guards

- [ ] Lane switch (Add Car → Claim) still shows confirm; H5 Start Card on confirm
- [ ] Broker Done End Card unchanged
- [ ] Legacy injury quick-reply still works on legacy cases
- [ ] Random photo before Claim start still hidden (no silent case create)

---

## Sign-off

| Role | Name | Date | GO/HOLD |
|------|------|------|---------|
| Engineer | | | |
| Founder | Andy | | |

**Notes:**
