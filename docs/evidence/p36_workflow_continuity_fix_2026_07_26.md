# P3.6 Workflow Continuity Fix — Evidence

**Date:** 2026-07-26  
**Type:** Workflow continuity fix (not a new Capability / not architecture redesign)  
**ONE OBJECTIVE:** Customer never lands on Waiting while a next unfinished default task remains.  
**OUT OF SCOPE:** C01/C02/C03 redesign, new workflow states, Capability redesign, photos productization beyond transition continuity.

## Root cause

After Story + Insurance, Constitution still named Today=`补充照片` and kept photos actionable, but `_customer_current_stage` fell through to `waiting` because `_has_incomplete_default_intake` ignored unfinished photos. Client `customerOwesWork` treated stage `waiting` as done → Case Status (“已收到，陈总正在看”) too early.

## Design decision

**Owner: Completion Detection (Constitution), with Navigation consuming that truth.**

- Completion Detection decides whether the default journey is finished (story + insurance + photos).
- Navigation (`resolveWorkflowContinueRoute`) goes directly to the next unfinished task page; Waiting only when nothing remains.
- No new states. No Capability redesign. C01/C02/C03 untouched.

## Files changed

| File | Role |
|------|------|
| `services/fiqa_api/inbox_triage/constitution_projection.py` | Incomplete default intake includes photos; non-wait Today ⇒ Action Needed |
| `services/fiqa_api/inbox_triage/p0_customer_context.py` | Actionable tasks / Action Needed beat wait signals for Continue |
| `miniapp/utils/customerCaseSurface.ts` | `customerOwesWork` + `resolveWorkflowContinueRoute` |
| `miniapp/pages/request-item/request-item.ts` | Post-submit → next task |
| `miniapp/pages/case-status/case-status.ts` | Redirect remaining work → next task |
| `miniapp/pages/entry/entry.ts` | Continue resolves concrete next task |
| `miniapp/pages/photos/photos.ts` | Done → Waiting / next via continue route |
| `tests/test_p36_workflow_continuity.py` | Scenario A–C server probes |
| `miniapp/tests/customerCaseSurface.test.ts` | Scenario A–D client probes |

## Why this preserves architecture

- Reuses Constitution Today / stage / task cards as SoR.
- Does not add Workflow states, Task Queue, or Capability packages.
- Waiting Broker still means “customer finished everything currently expected.”
- Request More / broker follow-up paths unchanged in shape.

## Workflow before / after

**Before:** Story → Insurance → Waiting (“陈总正在看”) → Continue → Photos  

**After:** Story → Insurance → Photos → Waiting  

Resume mid-journey: Continue → next unfinished task (Photos), never Waiting detour.

## Acceptance test results

| Scenario | Result |
|----------|--------|
| A Story → Insurance → Photos → Waiting | **PASS** (automated: Constitution + continue route + miniapp tests) |
| B Story → Insurance → close → Continue → Photos → Waiting | **PASS** (automated: context + entry continue route + client owe-work) |
| C Story only → broker requests Insurance later → Insurance → Waiting | **PASS** (automated: Request More Action Needed path) |
| D Several remaining tasks → always next unfinished; never Waiting detour | **PASS** (automated: `resolveWorkflowContinueRoute`) |

Also: `cd miniapp && npm run build:gate` → **PASSED**  
Focused: `tests/test_p36_workflow_continuity.py` → **PASSED**  
Focused: miniapp P3.6 customerCaseSurface tests → **PASSED**

## Founder walkthrough result

**READY FOR FOUNDER PHYSICAL QA** — code + automated gates PASS. Physical DevTools/phone walkthrough is Founder-owned (not run in this loop).
