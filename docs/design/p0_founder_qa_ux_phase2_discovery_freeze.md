# P0 Founder QA UX — Phase 2 Discovery and Freeze

**Status:** Architecture frozen; Phase 2 implementation authorized and landed  
**Date:** 2026-07-22  
**Scope:** One Golden QA session supports sequential supported Broker Request More tasks after one Preview QR scan.

## P20 header

**One user-facing objective:** After one QR scan, the Founder can complete multiple supported Broker Request More tasks for the same Camry Golden QA case without scanning again.

**Explicitly out of scope:** WebSockets, push notifications, a QA scenario picker, a new customer account system, new customer-facing identity UI, new task APIs, a Preview/QR redesign, production behavior changes, and Phase 2 implementation.

**Stop rule:** This document is the Phase 2 freeze. Do not implement from it until separately authorized.

## 1. Current-state trace

```text
Founder Launch Golden QA
  -> reset_golden_qa(target=qa, reseed=true)
     -> remove only prior camry_golden_qa + workbench_test cases
     -> seed fresh Camry case
     -> create initial Slice1 Request More: 上传保险卡
     -> verify case/projection/API
     -> mint one signed customer launch token for that case
  -> prepare DevTools compile query: pages/entry/entry?token=...
  -> Founder generates Preview QR and scans it once
  -> Entry resolves query token, fetches /api/h5/tasks/{token}/intake,
     and stores that same token as mp_prototype_resume_token
  -> Task Home / Request Item render the server-owned current task
  -> Broker creates a supported Request More through
     POST /api/inbox/cases/{case_id}/request-more
  -> Slice1 changes the server projection for the same case
  -> phone foregrounds Task Home, Receipt, or Request Item
  -> page onShow rehydrates GET /api/h5/tasks/{stored-token}/intake
  -> phone renders the new server-owned current task
```

### Ownership boundaries

| Concept | Meaning | Current owner / behavior |
|---|---|---|
| Preview QR | One-time application entry into the Mini Program Preview | DevTools Preview generated after a token is injected into the Entry compile query |
| QA session | The Founder’s currently bound test identity | The signed customer launch token persisted locally after first successful Entry bootstrap; server validates it on every task read |
| Current task | Mutable, customer-safe work for the bound case | Server `GET /api/h5/tasks/{token}/intake` projection, including Slice1 and Constitution task state |
| Request More | Broker command that creates/updates customer work | Existing authorized Slice1 command; its result changes the case projection, not the phone’s QR |

The Preview QR is therefore an **entry bootstrap**. It is not a task-delivery channel and must not be regenerated for ordinary Request More updates.

### Why another scan appears necessary today

There is no evidence that a second scan is technically required for an ordinary Request More on the same unexpired Golden case:

1. Entry persists the first valid query token in `mp_prototype_resume_token`.
2. Entry and Home routing reuse that stored token after re-entry.
3. Task Home, Receipt, and Request Item already rehydrate authoritative task state on later `onShow`.
4. `GET /api/h5/tasks/{token}/intake` resolves the current Slice1 projection for the token’s case; it does not bind the token to only the seed task.
5. A completed Request More returns the case to `broker_review_ready`, where the broker can create a later request when no request group remains open.

The observed second-scan ritual has a different cause: **starting Golden launch again intentionally deletes/reseeds the tagged Camry case and mints a new token.** The prior token then correctly points to a removed/stale case and cannot be reused. The current Founder playbook also says to make a new Preview QR after every new launch, which is correct for a new run but must not be interpreted as a requirement after Broker Request More.

The actual usability gap is narrower: while a task screen stays continuously foregrounded, it has no active arrival mechanism. It will reconcile on app/page foreground, pull-to-refresh, or another navigation lifecycle event. Phase 2 standardizes foreground reconciliation as the required discovery action and proves it in the Golden run.

## 2. Minimum task-update mechanism decision

| Mechanism | Assessment | Phase 2 decision |
|---|---|---|
| Refresh on page show / app foreground | Existing lifecycle and authoritative GET already exist. No new identity, endpoint, connection, or background work. Founder can briefly background and reopen the same Mini Program. | **Choose** |
| Lightweight polling while active | Could remove the foreground action, but adds timing, battery, duplicate-load, stale-response, and failure-state behavior. No evidence it is needed for the Founder run. | Deferred |
| Manual “Check for new task” | Safe fallback but adds a Founder operation and competes with the one-clear-next-action rule. | Do not add in Phase 2 |
| WebSocket / push | Requires connection/auth/session lifecycle, delivery/reconnect semantics, and a larger QA/Production isolation surface. | Rejected for Phase 2 |

**Frozen mechanism:** the phone performs a single authoritative task refresh when the relevant task surface becomes visible after Mini Program foreground/resume. The existing `taskPage.ensureTaskInitialized()` path is the mechanism for Task Home and Receipt; Request Item has an equivalent bootstrap/rehydrate path. The server response replaces local task state; clients do not infer a new task.

**No polling in Phase 2.** Reconsider only if Founder evidence shows that foreground refresh is materially insufficient for the real test cadence.

## 3. Session behavior contract

### Validity

- A Golden QA session begins when Entry accepts the Preview query token and persists it locally.
- It remains valid until the token expires, the Founder explicitly starts a new Golden test, or server validation rejects it.
- Existing Golden launch tokens use the customer-launch policy: **7 days**. This is the frozen Phase 2 duration; do not introduce a separate QA TTL.
- The existing token remains server-validated and case-bound. Local storage alone is never authority.

### Same-session reuse

- On foreground, Mini Program Home, reopening the Preview, or navigation back to a task surface, resolve the stored token through Entry/task loading and fetch the current task projection.
- A broker Request More changes only the server case/projection. It does not mint, send, display, or require another QR/token.
- The response must be applied only if it belongs to the currently valid token/case; existing request generation and page-alive guards remain in force.

### Sequential Request More

1. Golden seed starts with the first supported task: Insurance Card.
2. Founder submits it; the server returns an authoritative completion/waiting projection.
3. Broker observes the accepted result through the authoritative Workbench projection (read-after-write).
4. Broker creates the next supported request, for example Vehicle Information, against the same case after the first request group is complete.
5. Founder foregrounds the same Mini Program. It fetches the same token’s current task and displays the new request.
6. Repeat for later supported Request More tasks while the case is non-terminal and the session is valid.

The current Slice1 invariant of one open request group remains unchanged. “Sequential” means a later broker request after the prior group is complete, not two concurrently open broker request groups.

### Submission and receipt

- After a request-item submission, the phone must show the server result immediately and preserve the same stored token.
- If the projection says waiting for broker review, the receipt/task surface remains a valid bound surface—not a terminal logout.
- A later Broker Request More becomes visible on the next foreground rehydrate and replaces the stale wait state with the new server-owned task.

### Expiry

- If server validation returns `invalid_or_expired_task_link`, clear the stored resume token and show the existing customer-safe expiry recovery copy.
- Do not attempt token repair, silently create a claim, expose a case ID, or send the Founder to DevTools.
- The Founder starts a new Golden test run through the existing launch surface, which creates a new case, token, Preview, and one new QR scan.

### Explicit new test

“Start a new Golden test” means the existing **Launch Golden QA** action:

- delete only tagged Golden QA test data;
- seed and verify a clean Camry case;
- mint a new token;
- prepare a new Preview;
- require exactly one scan for that new run.

It must not be triggered by Request More, task refresh, app foreground, or a normal customer submission.

## 4. Phase 2 implementation boundary

### In scope when implementation is authorized

1. Preserve the existing persisted-token binding and current-task GET contract.
2. Make foreground/task-surface rehydration an explicit Golden QA requirement and test it against a broker-created second Request More.
3. Ensure all three relevant surfaces apply the refreshed server projection safely:
   - Task Home;
   - Receipt / waiting-for-broker surface;
   - active Request Item if it is foregrounded when broker state changes.
4. Add focused regression coverage for:
   - one scan + persisted binding;
   - first Request More completion;
   - broker creates second supported request without Preview/token regeneration;
   - foreground refresh displays the second task for the same case;
   - expired token clears binding and gives a customer-safe recovery state.
5. Update the Founder QA playbook and Golden manual evidence checklist to distinguish **new run → new QR** from **new Request More → foreground refresh**.

### Not in scope

- New API endpoints, token formats, session tables, WebSockets, push, polling, notification permissions, QR payload changes, task polling dashboards, or raw session/task identifiers in the Mini Program.
- Changing QA/Production routing, support authorization, token secrecy, or Golden reset deletion scope.
- Adding unsupported Request More item types.

### Existing APIs are sufficient

No new API is needed. The existing authorized broker command writes Request More and the existing authorized customer task GET reads the current projection:

```text
POST /api/inbox/cases/{case_id}/request-more
GET  /api/h5/tasks/{stored-valid-token}/intake
```

The customer call keeps its opaque token in the URL path as the existing contract requires; no case ID, raw token, or QA identifier is rendered or copied into customer UI.

## 5. Likely affected files/components

| Area | Likely files | Intended Phase 2 work |
|---|---|---|
| Founder procedure | `docs/FOUNDER_QA_PLAYBOOK.md`; Golden evidence/manual QA script | Document one-scan-per-run rule and foreground-refresh step |
| Golden fixture / flow test | `scripts/camry_golden_qa.py`, `tests/test_camry_golden_qa_reset.py`, targeted Golden flow harness | Prove seed → submit → second Request More on same case/token |
| Broker command verification | `ui/src/features/intake/components/StructuredRequestMorePanel.tsx`, Slice1 service/API tests | Confirm later supported request is created only after prior group completion and does not touch Preview |
| Customer task read | `services/fiqa_api/inbox_triage/h5_task_intake.py`, `services/fiqa_api/routes/h5_task_intake.py` | Contract tests only unless a projection defect is found |
| Mini Program binding / lifecycle | `miniapp/services/taskLaunchContext.ts`, `miniapp/utils/storage.ts`, `miniapp/behaviors/taskPage.ts` | Preserve same-token binding and authoritative foreground rehydrate |
| Task surfaces | `miniapp/pages/task-home/task-home.ts`, `miniapp/pages/receipt/receipt.ts`, `miniapp/pages/request-item/request-item.ts` | Focused lifecycle tests; change code only if the Phase 2 test exposes a real stale-state defect |
| Mini Program regression tests | `miniapp/tests/taskHomePage.test.ts`, `miniapp/tests/receiptPage.test.ts`, request-item/lifecycle tests | Same-session foreground-refresh tests |

`LaunchGoldenQaPanel.tsx`, `scripts/launch_golden_qa.sh`, and Preview preparation are not expected to change. They remain responsible for a **new run** only.

## 6. Risks and rollback

| Risk | Containment |
|---|---|
| Stale projection appears after broker creates task | Foreground rehydrate must replace state only with the authoritative GET response; retain generation/page-alive guards and test stale-response rejection |
| Broker tries to create a second request before first group completes | Preserve one-open-group and expected-version checks; return current authoritative projection without duplicate work |
| Expired token leaves user stranded | Existing invalid/expired handling clears the resume token and shows visible customer-safe recovery; test it |
| Reset accidentally treated as continuation | Keep reset scoped to `demo_name=camry_golden_qa` plus `workbench_test`; new reset deliberately invalidates the former run |
| QA data or token crosses into Production | Retain separate QA host/database/profile and fail-closed launch verification; no new transport or token channel |
| Active-screen wait creates expectation of instant delivery | Founder instructions specify foreground/reopen to reconcile; do not claim push behavior |

**Rollback:** Phase 2 is additive client reconciliation and tests/documentation. If a regression occurs, revert the Phase 2 client lifecycle change (if any) and retain the existing server projection, token, and accepted Request More data. Do not delete cases, request groups, evidence, tokens, or command outcomes. The fallback Founder procedure is foreground/reopen the same Mini Program; it never calls for QR regeneration unless the session is expired or a new run is explicitly started.

## 7. Acceptance criteria

### Required end-to-end Founder QA

- [ ] One Golden test run requires exactly one QR scan.
- [ ] Founder enters the Mini Program once and completes at least two sequential supported Request More tasks in the same session: Insurance Card, then Vehicle Information (or another supported item).
- [ ] Broker sends the second request from the same Camry case without launching Golden QA again, regenerating Preview, or creating a new QR.
- [ ] Founder backgrounds and foregrounds/reopens the same Mini Program; the phone displays the second server-owned current task without scanning again.
- [ ] The same opaque token remains bound to the same Golden case for both tasks; no raw token, case ID, session ID, DevTools instruction, or copy/paste is exposed in Founder/customer UI.
- [ ] After each submission, the Broker Workbench shows the same accepted item/result for the same case and request group (read-after-write).
- [ ] A broker-created task does not overwrite completed default or previously accepted work.
- [ ] An expired session visibly fails with customer-safe recovery, clears stale local resume, and requires a new Golden launch/one new QR.
- [ ] Explicit **Launch Golden QA** creates a clean new run and is the only ordinary action that causes a new QR.
- [ ] QA/Production isolation remains fail-closed: QA profile/host/database only; no QA token accepted by Production.
- [ ] Build Gate passes before device QA; all touched task surfaces render a non-blank loading, content, or recovery state.

### Focused automated evidence required before Founder QA

- [ ] Current token can read the current task before and after the first Request More submission.
- [ ] Same case/token receives the second broker Request More projection.
- [ ] Task Home, Receipt, and Request Item foreground paths reconcile correctly or show visible recovery.
- [ ] Expired/invalid token behavior is covered.
- [ ] Duplicate/stale Request More and request-item submission do not create duplicate events.

## 8. Suggested implementation split (maximum two commits)

### Commit 1 — `test: prove same-session Golden QA task refresh`

- Add focused backend and Mini Program lifecycle tests for one case/token across two sequential supported Request More tasks.
- Add test coverage for foreground rehydrate from Task Home and Receipt; include Request Item only where its existing lifecycle needs coverage.
- Add the manual Founder QA evidence script/checklist update.
- No polling, WebSocket, new endpoint, token change, or QR change.

### Commit 2 — `fix: reconcile current Golden task on foreground`

- Only if Commit 1 exposes a real gap, apply the smallest lifecycle fix to the affected task surface(s).
- Preserve the existing task GET, stored token, single-flight/generation guards, and customer-safe expiry handling.
- Update the Founder QA playbook to say: one scan per launch; foreground the same Mini Program after Broker Request More.
- Run Build Gate, focused tests, and recorded physical Founder QA before declaring the capability done.

## 9. Frozen decision record

| Decision | Frozen choice |
|---|---|
| QR role | Initial application entry only |
| Session identity | Existing persisted, server-validated signed task token |
| Mutable work authority | Existing current-task GET projection |
| Update mechanism | Foreground/page-show authoritative refresh |
| Active-screen delivery | No guarantee in Phase 2; no polling/push |
| Session lifetime | Existing 7-day Golden launch-token policy |
| New launch | Explicit Founder action only; clean case + new token + new QR |
| New API | None |
| WebSocket / push | Not Phase 2 |
| Completion definition | Automated evidence plus recorded one-scan Founder device QA |

## 10. P20 freeze scorecard

- **Reliability:** CONDITIONAL — architecture uses proven token/read paths; require the sequential physical-device evidence above.
- **Simplicity:** PASS — one scan, then use the same Mini Program; no new Founder control.
- **Smoothness:** CONDITIONAL — foreground rehydrate is the smallest supported discovery behavior; validate on device.
- **Business Value:** PASS — Broker can request the next supported item without interrupting the Founder’s QA session.
- **Scope Control:** PASS — no new transport, identity, API, or customer surface is introduced.

**Implementation authorization:** YES (Phase 2 implementation).  
**QA deploy authorization:** NO (device Founder QA still required before capability done).  
**Capability verdict:** Phase 2 implemented in repo; physical one-scan Founder QA pending.
