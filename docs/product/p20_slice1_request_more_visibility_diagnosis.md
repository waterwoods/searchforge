# P20 Slice 1 Request More Visibility Diagnosis

**Status:** PASS - diagnosis complete  
**Date:** 2026-07-15  
**Scope:** Read-only diagnosis of why structured Request More is not visible in the currently opened `/workbench/document-intake` case drawer on `ui-smoky-beta.vercel.app`. No production code, deploy, mutation endpoint, commit, or subagent use.

## 1. Exact Drawer Component

The opened right-side drawer at:

```text
https://ui-smoky-beta.vercel.app/workbench/document-intake
```

is rendered by:

- File: `ui/src/pages/DocumentIntakeInboxPage.tsx`
- Page component: `DocumentIntakeInboxPage`
- Drawer body component: `BrokerCaseDetail`
- Route wiring: `ui/src/App.tsx` maps `/workbench/document-intake` to `OfficeReviewShell` -> `DocumentIntakeInboxPage`

Rendering path from the blue `Open` button:

```text
App route /workbench/document-intake
  -> DocumentIntakeInboxPage
  -> table actions column Button "Open"
  -> openCase(row.case_id)
  -> setOpenId(caseId), setDetail(stub), optional getSavedCase(caseId)
  -> Ant Design Drawer open={Boolean(openId)}
  -> BrokerCaseDetail(caseItem={detail})
  -> ClaimCaseBriefPanel / ClaimEvidenceChecklist / CaseAttachmentsPanel / broker done/delete actions
```

Observed deployed case:

- Opened case id from browser performance resources: `case_874d750b5d5f`
- Visible lane/status: `Claim · 记录中`, `BROKER_REVIEW`
- Visible drawer content: claim brief, evidence checklist, 11 attachments, `陈总已确认 / 结束收集`, delete action
- No `Structured Request More`, `Request more`, `Add Request`, or `补充资料` control in the rendered drawer.

`BrokerWorkbenchTab` is **not** mounted in this route. It is mounted under `UnifiedIntakePage` (`/workbench/unified-intake`) and the single-tab broker variant, not under `/workbench/document-intake`.

## 2. Exact Request More Component / Location

The structured Request More UI exists locally in:

- File: `ui/src/features/intake/components/BrokerWorkbenchTab.tsx`
- Component: `BrokerWorkbenchTab`
- Local render function: `renderSlice1RequestMorePanel`
- Modal/action path: `Request more` button -> `openRequestMoreComposer` -> `handleSubmitRequestMore` -> `createCaseRequestMore`
- API client: `ui/src/api/inboxTriage.ts`, `createCaseRequestMore`
- Backend route: `POST /api/inbox/cases/{case_id}/request-more`

It was not added to:

- `ui/src/pages/DocumentIntakeInboxPage.tsx`
- `BrokerCaseDetail`
- the Ant Design `Drawer` opened by the blue `Open` button on `/workbench/document-intake`

Therefore the Step 2 component was added to a different Workbench surface than the currently observed production route.

## 3. Visibility Conditions

Conditions that can hide or prevent structured Request More:

1. **Wrong route/component:** `/workbench/document-intake` renders `DocumentIntakeInboxPage` / `BrokerCaseDetail`, not `BrokerWorkbenchTab`. This currently hides the UI unconditionally on that route.
2. **Deployment missing:** the deployed Vercel bundle does not contain Step 2 Request More strings, so the deployed alias cannot render the local Step 2 UI anywhere in that artifact.
3. **Claim lane/type:** `renderSlice1RequestMorePanel` returns `null` unless `currentCase.service_lane === "claim"`.
4. **Case capability version:** `BrokerWorkbenchTab` treats a case as enabled only when `slice1_capability_version >= 1`, `p20_slice1_capability_version >= 1`, or a Slice 1 projection is already present.
5. **Backend feature flag:** backend command/projection support is enabled by `P20_SLICE1_REQUEST_MORE` or case-level capability.
6. **Workbench eligibility calculation:** `slice1CanCreateRequest` requires Slice 1 enabled and either `broker_next_action.action_type === "create_request"` or no projection/open request with `workflow_phase`/`claim_phase === "broker_review"`.
7. **Structured projection availability:** existing projection fields are read from `slice1_projection` / `p20_slice1_projection`; missing projection falls back to legacy behavior unless case capability and phase allow create.
8. **Legacy-case fallback:** non-enabled cases keep legacy notes, attachments, follow-up, status, and claim brief behavior.
9. **Existing open request:** if request summary status is `open`, create action is hidden and progress is shown instead.
10. **Terminal status:** backend rejects terminal states (`case_complete`, `cancelled`, `rejected`, `archived`) and claim broker-done cases are excluded from the document-intake queue.
11. **Illegal case state:** backend accepts create only from canonical `broker_reviewing`; other non-terminal states return `illegal_state`.
12. **Authorization / actor identity:** backend requires office access and broker actor identity (`office:{office_id}` or `client:{client_id}`); failures return `403`.
13. **Loading/error state:** drawer can show stub/loading fallback; Step 2 conflict/submit errors are only handled inside `BrokerWorkbenchTab`.
14. **API/projection failure:** Slice 1 store creation requires `SERVICE_RECORD_DATABASE_URL` / `DATABASE_URL`; otherwise the command path can return `503`. H5 projection fetch falls back to legacy if projection fetch fails and no compatible projection exists.
15. **API error behavior:** `404` maps to not found, `403` to authorization, `422 slice1_not_enabled` to feature-disabled UI error, `409 version_conflict` to conflict refresh.
16. **`productOnlyUi` / UI flags:** `BrokerWorkbenchTab` changes layout/filtering under product-only mode, but the Slice 1 panel itself is not hidden by `productOnlyUi`. This flag is not relevant to `/workbench/document-intake` because that route does not mount `BrokerWorkbenchTab`.

For the currently opened case, the most likely false condition is the route/component condition: the mounted drawer has no Request More render path. The case appears to be a Claim/BROKER_REVIEW case, but the capability fields could not be read directly because unauthenticated direct API fetch returned `401 intake_api_unauthorized`.

## 4. Feature Flag / Capability-Version Behavior

Backend:

- `P20_SLICE1_REQUEST_MORE` is read by `slice1_feature_flag_enabled`.
- Truthy values are `1`, `true`, `yes`, `on`.
- `case_supports_slice1` returns true when `slice1_capability_version` or `p20_slice1_capability_version` is at least `1`.
- `slice1_enabled_for_case` is `P20_SLICE1_REQUEST_MORE || case_supports_slice1(case)`.
- If neither is true, create returns `422` with `error_code: "slice1_not_enabled"`.

Workbench Step 2 client:

- `slice1EnabledForWorkbenchCase` requires `service_lane === "claim"` and either capability version >= 1 or an existing Slice 1 projection.
- `slice1CanCreateRequest` allows create when broker projection says `create_request`, or when there is no projection/open request and phase is `broker_review`.
- Missing capability fields default to version `0`, which means not enabled unless a projection exists.

Existing demo cases are not automatically Slice 1-enabled by the checked docs/scripts. The Step 4 validation report explicitly says preview preflight does **not** create Slice 1 test cases automatically and enabling a QA claim remains an operator step.

How a test case is supposed to become enabled:

1. Deploy/apply the companion-table migration in QA/non-prod Postgres.
2. Deploy backend command/projection code.
3. Enable either backend flag `P20_SLICE1_REQUEST_MORE` or set `slice1_capability_version: 1` / `p20_slice1_capability_version: 1` on the target Claim case.
4. Ensure the case is `service_lane: "claim"` and in broker review (`claim_phase` / derived phase `broker_review`).
5. Open that enabled claim in a UI route that actually renders the Slice 1 panel.

## 5. Deployment Status

Local git state:

- Branch: `sprint/p16-trust-layer`
- HEAD: `0ea4b72 feat: stabilize evidence gallery and mobile photo workflow`
- Relevant Step 2 files are uncommitted:
  - `ui/src/api/config.ts`
  - `ui/src/api/inboxTriage.ts`
  - `ui/src/features/intake/components/BrokerWorkbenchTab.tsx`
  - `ui/src/api/inboxTriage.requestMore.test.ts` (untracked)
  - `tests/test_p20_slice1_api.py` (untracked)
  - `docs/product/p20_slice1_workbench_step2_implementation_report.md` (untracked)
- Relevant Step 1 backend files are also uncommitted/untracked, including `services/fiqa_api/inbox_triage/p20_slice1_command_service.py` and migration `002_p20_slice1_request_more.sql`.

Vercel config:

- `ui/vercel.json` builds with `npm run build`, outputs `dist`, and rewrites `/workbench/:path*` to `/`.
- `ui/vite.config.ts` requires `VITE_API_BASE_URL` for Vercel production builds.
- Current deployed bundle contains API base: `https://fiqa-api-1013093472160.us-west1.run.app`.

Deployed alias probe:

- Fetched `https://ui-smoky-beta.vercel.app/workbench/document-intake`.
- Current JS asset: `/assets/index-DyQovF8y.js`.
- Bundle contained `Office Review Queue`.
- Bundle did **not** contain:
  - `Structured Request More`
  - `Request More sent to customer`
  - `Slice 1 enabled`
  - `Create Structured Request More`

Conclusion: the current `ui-smoky-beta.vercel.app` deployment does **not** contain the local Step 2 Request More UI. Because the relevant code is uncommitted, a normal Vercel deployment from the committed branch cannot contain it unless a deploy was made from a dirty local working tree; the live bundle probe confirms it was not.

## 6. Most Likely Root Cause

Confirmed independent blockers:

- **A. UI implemented but not deployed:** confirmed for current Vercel alias. The live bundle lacks Step 2 Request More strings.
- **D. UI added to the wrong component/path:** confirmed for the observed drawer. The current route uses `DocumentIntakeInboxPage` / `BrokerCaseDetail`, while Step 2 UI was added to `BrokerWorkbenchTab`.

Most precise diagnosis:

- For the currently opened deployed drawer, the immediate cause is **A + D**.
- Deployment alone is not sufficient, because the local Step 2 UI still is not wired into the `/workbench/document-intake` drawer.
- A code wiring change is required if Request More must appear on this specific drawer.

Not the primary observed cause:

- **B. Deployed but feature flag disabled:** unknown on backend, but the deployed UI does not contain the control.
- **C. Case not capability-enabled:** likely for existing demo cases unless explicitly enabled, but not the first blocker because the mounted component cannot render Request More.
- **E. Runtime/API projection failure:** possible later if backend store/env is missing, but not needed to explain current invisibility.

## 7. Evidence

Code evidence:

- `ui/src/App.tsx` maps `/workbench/document-intake` to `DocumentIntakeInboxPage`.
- `ui/src/pages/DocumentIntakeInboxPage.tsx` defines the `Open` button, `openCase`, Ant Design `Drawer`, and `BrokerCaseDetail`.
- `BrokerCaseDetail` renders claim brief, accident basics, evidence checklist, attachments, broker done, copy/delete actions. It has no Slice 1 Request More import, client call, panel, or modal.
- `ui/src/features/intake/components/BrokerWorkbenchTab.tsx` contains `renderSlice1RequestMorePanel`, `slice1EnabledForWorkbenchCase`, `slice1CanCreateRequest`, and `handleSubmitRequestMore`.
- `ui/src/pages/UnifiedIntakePage.tsx` mounts `BrokerWorkbenchTab`; `/workbench/document-intake` does not.
- `services/fiqa_api/inbox_triage/p20_slice1_command_service.py` gates Slice 1 by `P20_SLICE1_REQUEST_MORE` or capability version.
- `services/fiqa_api/routes/inbox_triage.py` exposes `POST /api/inbox/cases/{case_id}/request-more`.

Live evidence:

- Browser route opened: `https://ui-smoky-beta.vercel.app/workbench/document-intake`.
- First blue `Open` opened a drawer with `Accident Basics`, `照片清单`, 11 attachments, `陈总已确认 / 结束收集`, and delete action.
- Browser resource list showed `GET /api/inbox/cases/case_874d750b5d5f`.
- Direct unauthenticated fetch of that case returned `401 intake_api_unauthorized`; no mutation endpoints were called.
- Vercel bundle probe found `Office Review Queue` but none of the Step 2 Request More strings.

## 8. Smallest Safe Next Action

Smallest safe next action:

1. Decide whether structured Request More belongs on `/workbench/document-intake` or only `/workbench/unified-intake`.
2. If it belongs on `/workbench/document-intake`, port/extract the Step 2 panel into a shared Claim drawer component and mount it inside `BrokerCaseDetail` for Claim cases.
3. Create or enable one QA Claim test case with `slice1_capability_version: 1` and broker-review phase.
4. Verify locally/non-prod with read-only GET plus one explicit QA create command only after approval.
5. Deploy backend/migration/env and UI only after explicit deploy approval.

## 9. Whether Code Change Is Required

Yes, if the target surface is the currently observed `/workbench/document-intake` drawer. The Request More UI is not wired into that component.

No production code was changed in this diagnosis.

## 10. Whether Deployment Is Required

Yes. The current Vercel alias does not contain Step 2 UI. After any code wiring fix, deployment is required for `ui-smoky-beta.vercel.app` to show it.

Backend deployment/migration/env may also be required because Step 1 backend files and the Slice 1 migration are uncommitted locally and the live backend feature/env status is not confirmed.

## 11. Whether A New Enabled Test Case Is Required

Yes. Existing demo cases are not automatically Slice 1-enabled. Manual QA requires a test Claim with either `slice1_capability_version: 1` or a backend flag enabled, in broker review, with Workbench office access.

