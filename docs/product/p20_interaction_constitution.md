# P20 Interaction Constitution

**Sprint:** P20-RC1.3
**Status:** Mandatory interaction and frontend-state constitution for Insurance Unified Intake
**Date:** 2026-07-14
**Scope:** Mini Program, H5, and Workbench task flows that touch task UX, lifecycle, loading, retry, upload, resume, evidence, or broker review.

---

## 1. Purpose

This constitution defines the interaction and frontend-state rules that prevent recurring Mini Program and mobile task failures: duplicate initialization, stale response overwrites, infinite loading, upload ambiguity, post-submit dead ends, blank screens, and config mistakes that only appear in WeChat DevTools or on a real phone.

It complements:

- `docs/product/p20_smooth_task_experience_constitution.md`
- `docs/product/ux_problem_ledger.md`
- `docs/product/smoothness_scorecard.md`
- `docs/product_constitution/P16_CUSTOMER_FIRST_CONSTITUTION.md`
- `docs/design/p20_production_constitution_master_design_2026_07_12.md`

It does not replace the product constitution. It turns the customer-first and task-first principles into mandatory interaction engineering behavior.

---

## 2. Authority

These rules apply before visual preference, local implementation convenience, and feature expansion.

Any future work touching task UX, lifecycle, loading, retry, upload, resume, evidence, Broker Workbench behavior, or Mini Program/H5 state must identify the applicable rules before changing code and must add focused regression tests for those rules.

---

## 3. Mandatory Interaction Rules

### Rule 1 — One Page, One Initialization Owner

**Principle**

Each page has exactly one owner for first initialization. Refresh, reconciliation, resume repair, and `onShow` cannot also own first render.

**Why it exists**

Mini Program pages often run `onLoad` and first `onShow` close together. If both fetch and set state independently, the user sees duplicate requests, stale state, duplicate uploads, route loops, or flicker.

**Required implementation behavior**

- Use single-flight initialization for page bootstrap.
- Treat first `onShow` as a no-op or reconciliation-only pass when `onLoad` already owns the first fetch.
- Separate initial fetch from foreground refresh.
- Make initialization idempotent by token, route, and request generation.
- Preserve a visible loading shell while initialization runs.

**Anti-pattern**

- `onLoad` fetches task data, then first `onShow` immediately refreshes and overwrites it.
- Upload page first render is owned by both local slot hydration and server read-back.
- A page hides duplicate calls behind broad `loading` flags instead of a single-flight guard.

**Acceptance criteria**

- A cold page open issues one logical task initialization request.
- First `onShow` does not duplicate `onLoad`.
- Refresh/reconciliation can run after first render without changing ownership.
- Double navigation into the same page does not produce duplicate saves, submits, or uploads.

**Example from recent P20 failures**

TaskPhoto evidence required explicit `onShow` hydration coverage and busy/loading cleanup because Photos can be entered, left, and re-entered while upload state and read-back state compete.

---

### Rule 2 — Complete First-Render Data Shape

**Principle**

Every render-bound value exists before the first render and has a safe default.

**Why it exists**

Mini Program WXML evaluates bound fields before async data returns. Optional arrays, strings, and nested objects can crash a page or create a white screen if code calls collection/string methods on missing state.

**Required implementation behavior**

- Define every WXML/render-bound field in `Page.data`.
- Use empty arrays, empty strings, false booleans, and explicit empty objects as defaults.
- Never call `.find`, `.map`, `.filter`, `.startsWith`, or similar methods on optional state without normalization.
- Keep `Page.data` JSON-serializable: no functions, classes, Dates, Promises, files, request handles, or cyclic structures.
- Store non-serializable local handles outside `Page.data`, and project only safe render data.

**Anti-pattern**

- Binding `photos.map(...)` when `photos` is populated only after the API response.
- Storing upload task handles or raw file objects inside `Page.data`.
- Assuming a backend field exists because current test fixtures include it.

**Acceptance criteria**

- Clean-cache compile and first render do not throw with empty API data.
- Old or partial persisted task records render without lifecycle exceptions.
- Component props normalize missing values before rendering.
- New optional fields include defaults and tests for missing/old records.

**Example from recent P20 failures**

Component Gate 3 remains unsigned for the freeze; a real DevTools compile must prove new Task UI components do not fail on missing modules, missing components, or incomplete first-render data.

---

### Rule 3 — One Explicit State Machine

**Principle**

Every task page has one page-level state machine: `loading`, `ready`, or `recoverable_error`. Item states are separate and must not contradict page state.

**Why it exists**

Contradictory booleans such as `isLoading`, `loaded`, `hasError`, `uploading`, `success`, and `empty` create impossible UI states: ready content hidden by a spinner, received photos still retryable, or submit success plus error copy.

**Required implementation behavior**

- Use one page-level state: `loading`, `ready`, or `recoverable_error`.
- Keep item-level state separate: for example `empty`, `local_preview`, `uploading`, `confirming`, `received`, `failed`.
- Document legal transitions for each page and item model.
- Derive booleans from state where possible.
- Reject or normalize impossible states before `setData`.

**Anti-pattern**

- `loading=true` and `error=true` with content hidden indefinitely.
- A photo slot marked both `received` and `failed`.
- A submitted Review page with primary submit enabled and duplicate-submit error hidden elsewhere.

**Acceptance criteria**

- Each page can draw a small state transition diagram.
- Unit tests cover legal transition examples and at least one impossible-state normalization.
- No UI path depends on contradictory booleans.
- Item state changes do not replace page-level readiness.

**Example from recent P20 failures**

The UX ledger records completed uploads still appearing retryable and upload success being perceived as failure. That is an item-state/page-state conflict.

---

### Rule 4 — Every Async Path Must Terminate

**Principle**

Every async operation ends in success, recoverable failure, or timeout. No customer waits forever.

**Why it exists**

Mobile networks, WeChat upload APIs, local proxies, and backend warming can stall. A task app fails when the user sees an infinite spinner without explanation or escape.

**Required implementation behavior**

- Wrap async operations in `try/catch/finally` or equivalent guaranteed cleanup.
- Clear busy/loading state on success, failure, cancellation, and timeout.
- Set maximum durations for loading, upload confirmation, submit, and refresh paths.
- Show customer-safe recovery when timeout occurs.
- Bound retries and cooldown repeated taps.

**Anti-pattern**

- Setting `loading=true` before an API call and clearing it only in the success branch.
- Waiting indefinitely for server read-back.
- Polling until the backend changes state with no maximum attempt count.

**Acceptance criteria**

- Forced network failure clears loading and shows Retry/contact behavior.
- Upload failure and submit failure leave the page usable.
- Timeout copy distinguishes "wait/retry" from permanent failure.
- Tests cover success, failure, and cleanup.

**Example from recent P20 failures**

Photos manual checklist explicitly requires that no endless spinner remains after success or failure paths, and pilot blockers still require manual network failure proof.

---

### Rule 5 — Stale Response Protection

**Principle**

Older async responses cannot overwrite newer customer-visible state.

**Why it exists**

Mobile users navigate quickly, retry, re-enter pages, and foreground apps while old requests are still in flight. Without request generation or cancellation guards, stale responses can erase newer uploads, resurrect errors, or show the wrong case.

**Required implementation behavior**

- Assign request generation IDs or cancellation tokens to load, refresh, save, upload, and submit paths.
- Apply a response only if it matches the latest generation and the page is still alive.
- Block `setData` after `onUnload`.
- Treat foreground reconciliation as newer than old background requests.
- Keep upload intent identity stable across retry and generation-aware across confirmation.

**Anti-pattern**

- First load returns after a refresh and overwrites refreshed task data.
- Failed upload response arrives after retry success and restores a failed slot.
- Receipt reload from an old token overwrites the currently opened submitted task.

**Acceptance criteria**

- Tests simulate out-of-order responses and assert newest state wins.
- `onUnload` prevents late `setData`.
- Retry success cannot be overwritten by an earlier failure.
- Resume refresh cannot regress submitted state to draft.

**Example from recent P20 failures**

Upload success-after-failure and read-back races are called out as critical/high risks in the UX ledger because stale local upload state can outlive server-confirmed success.

---

### Rule 6 — Page Lifecycle Safety

**Principle**

`onLoad`, `onShow`, `onHide`, and `onUnload` each have a narrow responsibility.

**Why it exists**

WeChat lifecycle behavior is normal user behavior, not an edge case. Customers background WeChat, switch to photos, return from upload, kill the app, and reopen from a task link.

**Required implementation behavior**

- `onLoad`: parse launch query, initialize safe render shape, start single-flight first load.
- `onShow`: reconcile foreground state only after first initialization; refresh server truth when needed.
- `onHide`: persist safe local draft state and mark noncritical work as paused.
- `onUnload`: cancel/guard late responses and release local handles.
- Resume must not duplicate requests, uploads, formal submits, or supplement saves.

**Anti-pattern**

- Starting upload in both a tap handler and `onShow`.
- Treating resume as a new task.
- Leaving a page while saving and returning to a stale "saving" UI forever.

**Acceptance criteria**

- Kill/reopen mid-task restores safe server/local state.
- Kill/reopen after submit routes to submitted status/Receipt, not a new claim.
- Returning from background does not duplicate uploads or submit.
- Lifecycle tests or manual checklist rows cover first load, return, and resume.

**Example from recent P20 failures**

DevTools checklist requires resume mid-task, resume after submit, and no duplicate claim/submit after reopening.

---

### Rule 7 — Page-Level vs Item-Level Progress

**Principle**

Page loading must not block content that is already usable. Item confirmation belongs to the item.

**Why it exists**

Photo and evidence workflows are multi-item. One item being uploaded or confirmed should not freeze the whole gallery or make existing evidence unusable.

**Required implementation behavior**

- Keep already received content visible during refresh and upload.
- Use item-level states such as `上传中`, `已上传，正在确认`, `已收到`, and `上传失败`.
- Do not block preview/delete/retry for unrelated items unless required by product law.
- Page-level loading is reserved for first render or blocking recovery.
- Background refresh should preserve usable content.

**Anti-pattern**

- Whole gallery spinner while confirming one upload.
- Hiding all photos during read-back.
- Treating "minimum required photos met" as a reason to lock the gallery.

**Acceptance criteria**

- Upload confirmation does not block viewing already received photos.
- Failed slot retry reuses local image without re-pick.
- Existing content remains usable during refresh.
- Page-level and item-level progress have separate tests.

**Example from recent P20 failures**

TaskPhoto migration added slot-level progress and retry behavior because slow photo upload felt stuck and duplicate taps were a known risk.

---

### Rule 8 — Immediate Feedback and Perceived Performance

**Principle**

The customer sees feedback within 100-300 ms after a tap, even when server confirmation takes longer.

**Why it exists**

Without immediate feedback, users tap repeatedly, exit, or assume failure. Perceived performance is a production requirement for mobile task completion.

**Required implementation behavior**

- Acknowledge taps within 100-300 ms with pressed/busy/progress/local preview state.
- Show local photo preview immediately after the platform returns a selected file.
- Bound server confirmation and show item-level confirmation status.
- Use optimistic UI only after transport success, not before server acceptance.
- Success copy must match the completed operation.

**Anti-pattern**

- Showing "upload success" before the server records the attachment.
- Leaving the upload CTA looking tappable during an active upload.
- Blocking customer navigation for broker-only enrichment or AI summary.

**Acceptance criteria**

- Every primary tap shows visible feedback quickly.
- Duplicate taps are blocked while the intent is in flight.
- Local preview appears before server read-back, but received count increments only after read-back.
- Slow paths show progress, retry, or contact route.

**Example from recent P20 failures**

Photos acceptance requires count increments only after read-back, while local preview and upload progress reduce perceived waiting.

---

### Rule 9 — Idempotent User Actions

**Principle**

Retries repeat the same user intent. Intentional new work gets a new intent. Completed work never retries.

**Why it exists**

Duplicate taps and retry races create duplicate uploads, duplicate submits, noisy broker timelines, and customer distrust.

**Required implementation behavior**

- Generate a stable intent ID for save/upload/submit/retry attempts that represent the same user action.
- Block duplicate taps while an intent is active.
- Reuse the same local file and stable intent when retrying a failed upload.
- Create a new intent only when the user intentionally selects a new item or starts a new logical action.
- Suppress retry for completed/received items.

**Anti-pattern**

- Retry picks a new file without telling the customer.
- Completed upload still shows Retry.
- Formal submit can be sent twice because two tap handlers race.

**Acceptance criteria**

- Double-tap save/submit/upload creates one logical mutation.
- Retry of a failed photo does not require re-pick.
- Completed items cannot be retried.
- Backend/client tests cover duplicate submit and duplicate upload guard.

**Example from recent P20 failures**

TaskPhoto evidence shows duplicate upload blocked while busy; Review/Receipt evidence shows duplicate submit blocked and server read-back required.

---

### Rule 10 — Requirement Met Does Not Mean Flow Complete

**Principle**

Minimum requirements guide formal submit. They do not permanently lock legitimate append or supplement behavior.

**Why it exists**

Insurance intake is partial and evidence-heavy. Customers may have more photos, corrections, or follow-up details after meeting the minimum, and categories should not become permanent locks.

**Required implementation behavior**

- Distinguish minimum submit readiness from business completion.
- Keep legitimate append open until the business limit or broker-controlled closure.
- Treat required categories as guidance, not permanent locks.
- Preserve one formal submit; supplements append after submit where allowed.
- Broker remains the authority on completion.

**Anti-pattern**

- Hiding photo upload after three photos when additional evidence is allowed.
- Returning `already_submitted` for an allowed supplement save.
- Treating category completion as broker/customer task closure.

**Acceptance criteria**

- Submit readiness can be true while optional/additional evidence remains possible.
- Post-submit supplement save succeeds for allowed fields and does not create a second formal submit.
- UI copy explains "submitted" without implying "closed."
- Tests cover append after minimum and post-submit allowed supplement.

**Example from recent P20 failures**

P20 fixed a frontend/backend mismatch where post-submit supplement pages were reachable but backend PATCH returned `409 already_submitted`.

---

### Rule 11 — Server Authority and Local Draft

**Principle**

Server state is authoritative for confirmation. Local state exists only to preserve continuity and reduce anxiety.

**Why it exists**

Local state can be stale, corrupt, partial, or tied to an old token. Blind trust creates false success, wrong case display, and broker/customer mismatch.

**Required implementation behavior**

- Confirm saves, uploads, submits, and received counts from server read-back.
- Keep local drafts only for continuity and retry support.
- Sanitize old local state before use.
- Migrate persisted local drafts when render shape changes.
- Never let local state mark server-owned workflow complete.

**Anti-pattern**

- Toasting "saved" because local state updated.
- Restoring old submitted status from cache without server check.
- Trusting stale local photo slots over attachment read-back.

**Acceptance criteria**

- Server read-back follows customer-visible save/upload/submit success.
- Local drafts preserve text/file references after failure.
- Stale local state cannot override server status.
- Old local data versions are sanitized or ignored safely.

**Example from recent P20 failures**

Workbench readback remains a critical confidence gate because customer-visible saved/uploaded items must match broker-visible server truth.

---

### Rule 12 — Recover Instead of Blank Screen

**Principle**

Every page renders one of: loading, content, or recoverable error. No lifecycle exception may create a white screen.

**Why it exists**

White screens are the worst mobile failure: the customer cannot understand, retry, preserve work, or contact the broker.

**Required implementation behavior**

- Render a safe shell before async data.
- Catch lifecycle and API errors into a recoverable error state.
- Provide Retry when retry can help.
- Provide contact broker path when retry cannot help or when repeated retry fails.
- Avoid exposing raw IPs, scripts, stack traces, tokens, or internal IDs.

**Anti-pattern**

- Throwing from `onLoad` because a launch token is missing.
- Empty page while API warmup or Mini Program component loading fails.
- Raw error object shown to customer.

**Acceptance criteria**

- Missing/expired token shows contact guidance.
- Network failure shows customer-safe retry/contact copy.
- Clean-cache DevTools compile opens key pages without white screens.
- Every blocking error has a visible recovery or contact path.

**Example from recent P20 failures**

DevTools checklist requires Entry failure to show recoverable/contact error and never blank forever.

---

### Rule 13 — Error Semantics

**Principle**

Different errors require different customer behavior, operator interpretation, and diagnostics.

**Why it exists**

Retrying an expired token wastes time. Treating a duplicate as server failure creates duplicate work. Showing raw technical codes damages trust.

**Required implementation behavior**

- Distinguish transport, token, validation, duplicate, completed, and server errors.
- Map each error to retryable, non-retryable, contact, or already-complete behavior.
- Keep customer copy simple and Chinese-first where customer-facing.
- Preserve exact safe diagnostic codes for logs, QA notes, and Workbench/operator use.
- Never show secrets, tokens, stack traces, internal hostnames, or raw tenant identifiers to customers.

**Anti-pattern**

- One generic "failed, retry" message for all failures.
- Showing Retry for expired/missing token.
- Treating duplicate submit as a scary server error instead of already submitted/no need to resubmit.

**Acceptance criteria**

- Forced network, expired token, validation, duplicate submit, completed upload, and server failure paths behave differently.
- Customer copy is simple and actionable.
- Diagnostics are preserved in safe logs/test output.
- Error mapping tests exist for changed paths.

**Example from recent P20 failures**

Pilot blockers still require live DevTools proof for network failure and expired/invalid token paths despite automated mappings.

---

### Rule 14 — Resource and Performance Discipline

**Principle**

Mobile task flows must be responsive and conservative with images, refreshes, retries, and polling.

**Why it exists**

Photo evidence workflows can easily become slow, expensive, and unstable on real phones, especially with HEIC, weak networks, and preview/full-image behavior.

**Required implementation behavior**

- Lazy-load thumbnails.
- Load full image only on demand.
- Bound retries and backoff noisy operations.
- Avoid repeated full refresh when item-level reconciliation is enough.
- Avoid unnecessary polling; prefer event/read-back/explicit refresh.
- Keep image/file handles out of long-lived render state.

**Anti-pattern**

- Downloading full images for every gallery slot on page load.
- Full task refresh after every upload progress tick.
- Infinite polling for OCR/classification before customer can continue.

**Acceptance criteria**

- Gallery first render does not require full-size image downloads.
- Upload progress does not trigger repeated full-page reloads.
- Retry and polling loops have limits.
- HEIC/phone preview compatibility is explicitly tested or documented as blocked.

**Example from recent P20 failures**

UX ledger flags slow photo upload, HEIC uncertainty, attachment preview risk, and real-device path uncertainty as release-sensitive.

---

### Rule 15 — Preview / Experience Preflight

**Principle**

Configuration, AppID, domain, token, cache, and component gates are interaction quality, not deployment paperwork.

**Why it exists**

Mini Program behavior differs between localhost DevTools, tourist AppID, real AppID, LAN, HTTPS, and experience version. A polished code path still fails if the preflight path is wrong.

**Required implementation behavior**

- Use the real AppID locally when validating experience behavior.
- Use a QA HTTPS profile for real phone/preview.
- Do not use localhost for real-device validation.
- Ensure legal request/upload domains are configured.
- Launch with a valid query token.
- Do not embed secrets, private tokens, local AppID overrides, or private project config.
- Clear cache and compile in WeChat DevTools before experience upload.
- Pass the component Three Gates: file completeness, `usingComponents` path/casing, and real DevTools compile.

**Anti-pattern**

- Marking release-ready from unit tests while Gate 3 is unsigned.
- Phone preview points at `127.0.0.1`.
- Committing `config.local.ts`, private DevTools config, local token values, or real AppID overrides.

**Acceptance criteria**

- Gate 1 and Gate 2 validator output is green.
- Gate 3 human DevTools compile is signed for the release candidate.
- Real phone/HTTPS/upload path is verified or release is explicitly blocked.
- Experience launch query token is valid and not embedded in committed code.

**Example from recent P20 failures**

P20 stabilization freeze explicitly leaves Gate 3, HTTPS/legal domains, real-device path, and config freeze open; do not fabricate PASS.

---

### Rule 16 — Safe Component and State Evolution

**Principle**

New UI components, fields, and state projections must be backward-compatible with old task records, local drafts, and resume paths.

**Why it exists**

Mini Program releases and persisted task data do not always change at the same time. Old records, old local drafts, and new components must coexist without white screens or false state.

**Required implementation behavior**

- New optional fields include defaults.
- Old persisted state is migrated, sanitized, or safely ignored.
- Data projections are backward-compatible.
- Component props normalize missing/old values.
- Regression tests include old cases, missing optional fields, and resume state.

**Anti-pattern**

- Adding a required render prop without default.
- Changing slot shape without migrating local failed-upload state.
- Assuming all server records include new field names.

**Acceptance criteria**

- Old task fixtures still render.
- Resume from old local draft does not crash or override server truth.
- New components pass first-render empty-state tests.
- Focused regression tests cover the changed projection and lifecycle path.

**Example from recent P20 failures**

Recent A2b-A2d/e migrations introduced shared Task UI components and require Gate 3 plus manual journey verification because component registration and old state projections can regress runtime behavior despite automated tests.

---

## 4. Mandatory Checklist For Future Cursor Prompts

Every future Cursor prompt that changes task UX, lifecycle, loading, retry, upload, resume, evidence, or Workbench behavior must answer:

1. Which Interaction Constitution rules apply?
2. Who owns first initialization on each touched page?
3. What is the complete first-render `Page.data` or equivalent render shape?
4. What is the explicit page-level state machine and what item-level states are separate?
5. How does each async path terminate on success, recoverable failure, and timeout?
6. How are stale responses, late `setData`, and page destruction guarded?
7. What happens on `onLoad`, first `onShow`, later `onShow`, `onHide`, and `onUnload`?
8. Which progress is page-level and which progress is item-level?
9. What visible feedback appears within 100-300 ms of a tap?
10. What is the idempotency key or stable intent ID for save/upload/submit/retry?
11. What remains open after minimum requirements are met?
12. Which state is server-authoritative and which state is local draft only?
13. What does the user see instead of a blank screen for each failure?
14. How are transport, token, validation, duplicate, completed, and server errors differentiated?
15. What resource/performance limits prevent repeated full refresh, unbounded retry, or unnecessary polling?
16. What Preview/Experience preflight gates must pass before release or phone QA?
17. What old persisted state, old local draft, or resume case is covered by regression tests?
18. What UX Problem Ledger row is updated or referenced?
19. What Smoothness Scorecard categories are affected?
20. What focused tests or manual Founder phone QA prove the change?

---

## 5. Required Prompt Header

Future sprint prompts must include this exact block:

```text
Read and comply with:
- docs/product/p20_smooth_task_experience_constitution.md
- docs/product/p20_interaction_constitution.md
- docs/product/p20_ux_benchmark_library.md

Before changing task UX, lifecycle, loading, retry, upload, resume, evidence or
Workbench behavior, identify the applicable constitution rules and add focused
regression tests.
```

---

## 6. How Future Work Uses This Document

- **Sprint prompt header:** Paste the required header above before implementation instructions.
- **Design review:** Identify which rules are touched and confirm the state/lifecycle model before UI polish.
- **Focused tests:** Add tests for the smallest affected async, lifecycle, idempotency, stale-response, or render-shape rule.
- **Founder phone QA:** Verify real tap feedback, upload confirmation, resume, and recoverable failure on the target device path.
- **UX Problem Ledger update:** Add, fix, verify, reopen, or accept every discovered smoothness issue.
- **Smoothness Scorecard:** Score the categories affected by the change, especially Upload Experience, Error Recovery, Resume Experience, Broker Workflow, Performance Perception, Production Polish, and Founder Phone QA.
- **Short release readiness audit:** Confirm no rule violation is being shipped without an explicit Founder acceptance decision.

---

## 7. Recent P20 Failures Incorporated

This constitution explicitly incorporates:

- Upload success perceived or shown as failure.
- Completed upload still retryable.
- Duplicate upload risk during repeated taps.
- Slow photo upload feeling stuck.
- Server read-back required after upload and submit.
- First manual DevTools walkthrough not signed.
- Real-phone HTTPS / legal domain path not ready.
- Gate 3 real DevTools compile unsigned.
- Post-submit supplement frontend/backend mismatch.
- Review missing-item dead end.
- Repetitive submitted-state CTAs.
- Workbench visibility/readback gap.
- Network failure and expired-token paths not manually proven.
- Basics multi-PATCH partial-save residual risk.
- HEIC and attachment preview uncertainty.
- Local/private config and token/AppID safety risks.
