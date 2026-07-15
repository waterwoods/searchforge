# P20 Slice 1 Manual QA Script (≈10–15 min)

**Purpose:** Prove Broker Request More → Customer Continue on Workbench + WeChat DevTools / iPhone Preview.  
**Date:** 2026-07-15  
**Env:** non-production only (QA backend + DevTools Preview)

## Preconditions

- [ ] QA API reachable; Mini Program `apiProfile: "qa"`
- [ ] `npm run preview:preflight` PASS from `miniapp/`
- [ ] Slice 1 enabled on a **test claim** (`slice1_capability_version: 1` or flag)
- [ ] Workbench office access to that claim; claim in broker review
- [ ] Valid customer H5/Mini Program task token for the same case
- [ ] WeChat DevTools: **清缓存 → 全部清除 → 重新编译** (Gate 3)

Capture for each step: screenshot or short note of customer UI, Workbench panel, and (if visible) Timeline/request progress.

---

## A. Broker requests VIN from Document Intake drawer

| | |
|---|---|
| **Action** | Open `/workbench/document-intake` → click **Open** on the enabled claim → BrokerCaseDetail drawer → Structured Request More → add VIN → submit once |
| **Customer** | Task Home shows one primary: provide VIN; no competing CTAs |
| **Broker** | Request open; active=VIN; broker action=waiting for customer |
| **Timeline** | One `broker_request_more_created` |
| **Evidence** | Workbench progress 0/1; customer CTA routes to request-item |

Pass / Fail: ____

## B. Customer submits VIN

| | |
|---|---|
| **Action** | Mini Program → open task → primary CTA → enter valid 17-char VIN → submit |
| **Customer** | Immediate “submitting”; then “资料已提交，等待经纪人审核” (single-item) |
| **Broker** | Request completed; broker action=review customer response |
| **Timeline** | `customer_continue_started` → `field_saved` → `customer_request_item_satisfied` → `supplement_submitted` (once each) |
| **Evidence** | No second VIN primary; aggregate version advanced |

Pass / Fail: ____

## C. Broker requests VIN + insurance card + photos

| | |
|---|---|
| **Action** | New/enabled claim in review → Request More with ordered items: 1 VIN, 2 insurance card, 3 damage photos |
| **Customer** | Only VIN is primary; queued list shows insurance + photos (not tappable as primary) |
| **Broker** | Active=VIN; queued=2; progress 0/3 |
| **Timeline** | One create event; three items persisted |
| **Evidence** | Positions 1→2→3; insurance/photo action_type evidence |

Pass / Fail: ____

## D. Customer completes items in order

| | |
|---|---|
| **Action** | Submit VIN → upload insurance card → upload damage photo; one at a time |
| **Customer** | After VIN: insurance primary; after insurance: photos primary; after photos: waiting for broker |
| **Broker** | Active item advances; finally review-ready |
| **Timeline** | Per item: receipt + satisfied; final `supplement_submitted` once |
| **Evidence** | Never two primaries; queued never skipped |

Pass / Fail: ____

## E. Network retry

| | |
|---|---|
| **Action** | On active item, throttle network / kill response after submit; tap **重试提交** (same session) |
| **Customer** | Uncertain → retry; ends in confirmed next action or waiting |
| **Broker** | Single satisfaction for that item |
| **Timeline** | No duplicate event set for same command identity |
| **Evidence** | Same `command_id` / idempotency key reused |

Pass / Fail: ____

## F. Background and resume

| | |
|---|---|
| **Action** | Mid-draft on VIN: background app → reopen next day (or clear page stack and re-enter token) |
| **Customer** | Server Next Action wins; matching draft may restore; wrong item draft discarded |
| **Broker** | Unchanged pending item |
| **Timeline** | No new events from resume alone |
| **Evidence** | Exactly one primary after resume |

Pass / Fail: ____

## G. Final return to Broker review

| | |
|---|---|
| **Action** | Complete last queued item from scenario C/D |
| **Customer** | Waiting copy; submit CTA gone |
| **Broker** | `broker_review_ready` / review customer response; can continue review |
| **Timeline** | Final `supplement_submitted`; group completed |
| **Evidence** | Customer + broker projections same version |

Pass / Fail: ____

---

## Sign-off

| Check | Result |
|---|---|
| No duplicate request groups / items from double-submit | |
| Legacy (non-Slice-1) claim still uses old Task Home | |
| No white screen / endless spinner | |
| Preview AppID + QA domain correct | |

Tester: ________  Date: ________  Device: DevTools / iPhone ________
