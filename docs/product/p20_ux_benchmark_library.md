# P20 UX Benchmark Library

**Sprint:** P20-RC1.3
**Status:** Durable benchmark-method library for Insurance Unified Intake
**Date:** 2026-07-14
**Scope:** Reusable interaction methods for Mini Program, H5, and Broker Workbench task flows.

---

## 1. Purpose

This library extracts reusable methods from mature task products without copying visual design. It exists so future P20 work can borrow proven interaction discipline from high-throughput mobile workflows while staying faithful to the Insurance Unified Intake product constitution.

Reference categories:

- Walmart / Spark Driver
- Uber Eats Driver
- Amazon Flex
- McDonald's App
- TurboTax
- Strong Chinese WeChat Mini Programs
- Mature insurance claim intake products

The benchmark lesson is not "make P20 look like these products." The lesson is how they reduce uncertainty: one task, one status, one action, visible progress, fast feedback, recoverable failure, and authoritative completion.

---

## 2. How To Use This Library

Use this document during:

- Sprint prompt writing.
- Design review.
- Focused test planning.
- Founder phone QA.
- UX Problem Ledger updates.
- Smoothness Scorecard scoring.
- Short release readiness audits.

For any task UX change, choose the patterns that apply, translate them into P20-specific acceptance criteria, and avoid visual copying.

---

## 3. Benchmark Patterns

### Pattern 1 — Task Clarity

**Product/category example**

Spark Driver and Amazon Flex orient drivers around the current pickup/dropoff task; TurboTax orients taxpayers around the current question/interview step; mature claim intake tools orient customers around the next evidence or fact needed.

**What users perceive**

"I know what I am doing right now, why it matters, and what happens next."

**Hidden engineering discipline**

The product maintains a single current task projection, derived missing/received items, route-safe task state, and consistent status labels across customer and operator surfaces.

**How P20 should apply it**

Task Home, step pages, Review, Receipt, and Workbench must all agree on current status, received items, missing items, and next action. Customer screens must not expose internal concepts such as tokens, lanes, tenant IDs, workflow phases, confidence, or provenance jargon.

**What not to copy**

Do not copy driver-map layouts, gamified metrics, delivery timing pressure, or dense tax/legal forms.

**Suggested measurable acceptance threshold**

A first-time tester can say the next action in one sentence on every customer page; Workbench can show the broker the case gist in about 10 seconds.

---

### Pattern 2 — One Primary CTA

**Product/category example**

Uber Eats Driver and Spark Driver flows usually present one operational next action: accept, navigate, picked up, delivered. McDonald's App checkout keeps one dominant order action.

**What users perceive**

"There is one obvious button. I am not choosing between product paths."

**Hidden engineering discipline**

The view model resolves a single primary action from task state and demotes all secondary or recovery actions. Duplicate taps are guarded by busy/idempotency state.

**How P20 should apply it**

Each customer page has one primary CTA or one automatic primary transition. Submitted Task Home and Receipt use one primary `补充或修改资料` action sheet plus one secondary status/overview action. Review must not make `返回我的资料` the only way to fix missing fields.

**What not to copy**

Do not copy marketplace upsells, promos, order add-ons, driver incentives, or competing commercial CTAs.

**Suggested measurable acceptance threshold**

Reviewers can point to exactly one primary action per screen, and double-tapping it creates one logical save, upload, submit, or navigation.

---

### Pattern 3 — Staged Progress

**Product/category example**

TurboTax stages a complex tax filing into interview sections; Amazon Flex stages route work into pickup, scan, deliver, and completion; claim intake tools stage incident, vehicle, parties, photos, review, submit.

**What users perceive**

"The task is complex, but I only need to finish this stage."

**Hidden engineering discipline**

The system separates page state, item state, required vs optional work, submit readiness, and true business completion.

**How P20 should apply it**

Show received vs missing items instead of fake percentages. Formal submit readiness is not broker completion. Customers can append legitimate evidence or corrections until a business limit or broker-controlled closure.

**What not to copy**

Do not copy long progress bars that imply false precision or "100%" while required items are missing.

**Suggested measurable acceptance threshold**

Task Home and Review always show received/missing truth from the same server projection used by Workbench; no customer page claims complete while blocking missing items remain.

---

### Pattern 4 — Local-First Visual Feedback

**Product/category example**

McDonald's App gives immediate tap/cart feedback; driver apps acknowledge scan/photo actions immediately; WeChat Mini Programs rely on quick tap, toast, and local preview feedback.

**What users perceive**

"My tap worked. The app is doing something."

**Hidden engineering discipline**

Tap handlers update local render state quickly, duplicate actions are disabled, and server confirmation later upgrades the state from local/in-flight to confirmed.

**How P20 should apply it**

Photo selection should show local preview immediately. Save/upload/submit buttons should enter busy state within 100-300 ms. Received counts and broker-visible success should wait for server read-back.

**What not to copy**

Do not copy fake instant success where the backend has not accepted the work.

**Suggested measurable acceptance threshold**

Every primary tap shows visible feedback within 100-300 ms; customer-visible "saved/uploaded/submitted" success appears only after authoritative confirmation.

---

### Pattern 5 — Background Confirmation

**Product/category example**

Food delivery and logistics apps often let users continue seeing current work while background confirmation or sync completes. Mature claim intake products accept raw evidence first and classify later.

**What users perceive**

"My evidence is not lost, and I do not have to wait for every backend process."

**Hidden engineering discipline**

The product distinguishes customer-blocking confirmation from background enrichment, OCR, AI summary, dedup, and broker-only processing.

**How P20 should apply it**

Upload transport and server attachment record are customer-blocking; OCR/classification/broker brief enrichment should not block the customer when raw evidence can already be retained and broker-visible.

**What not to copy**

Do not copy opaque "processing" states that hide whether the user's evidence was actually received.

**Suggested measurable acceptance threshold**

Raw evidence appears as received/broker-visible before nonessential enrichment is complete; background failures do not erase customer work.

---

### Pattern 6 — Resume And Recovery

**Product/category example**

TurboTax is strong at leaving and returning to a partially completed interview. WeChat Mini Programs commonly need safe resume after app switch, phone lock, or chat return.

**What users perceive**

"I came back and my work is still here."

**Hidden engineering discipline**

Server authority, local draft preservation, lifecycle-safe initialization, stale-response guards, and idempotent mutations work together.

**How P20 should apply it**

Resume from Entry, Task Home, step pages, Review, and Receipt. Mid-task resume restores safe draft/server state. Post-submit resume routes to submitted status or Receipt, not a new task or duplicate submit.

**What not to copy**

Do not copy account-login portals or email/password recovery as a requirement for customer intake.

**Suggested measurable acceptance threshold**

Kill/reopen mid-task and kill/reopen after submit both pass manual QA without duplicate case, duplicate submit, lost draft, or stale status.

---

### Pattern 7 — Weak-Network Behavior

**Product/category example**

Driver apps and Chinese Mini Programs are designed for parking lots, elevators, stores, and low-signal moments. Mature claim intake must tolerate customers uploading photos from the roadside.

**What users perceive**

"The app did not freeze. I know whether to retry or contact someone."

**Hidden engineering discipline**

Timeouts, bounded retries, safe local retention, differentiated error semantics, and retry intent IDs prevent infinite spinners and duplicate mutations.

**How P20 should apply it**

Network failure shows Chinese retry/contact copy. Upload failure keeps the local image for retry. Expired token does not offer false retry. Busy state always clears on failure or timeout.

**What not to copy**

Do not copy aggressive background polling, silent retry loops, or technical diagnostic screens.

**Suggested measurable acceptance threshold**

Forced unreachable API, upload failure, save failure, and expired token scenarios all show bounded recovery or contact path with no raw technical details and no infinite loading.

---

### Pattern 8 — Photo Evidence Capture

**Product/category example**

Amazon Flex delivery proof, driver app pickup/dropoff photos, and insurance claim intake products treat photos as task evidence, not generic attachments.

**What users perceive**

"The product is asking for the right photo, and it confirms the photo was received."

**Hidden engineering discipline**

Photo slots have identity, local preview, upload progress, read-back confirmation, duplicate guard, retry semantics, and broker-visible metadata.

**How P20 should apply it**

Use required-first guidance, clear slot labels, local preview, slot-level progress, retry with existing local file, and success only after read-back. Broker Workbench must show the attachment, source, and received status.

**What not to copy**

Do not copy package-scan workflows, location surveillance, or camera overlays that are irrelevant to accident intake.

**Suggested measurable acceptance threshold**

One successful upload with read-back, one failed upload with retry, one duplicate tap attempt, and one Workbench attachment readback must pass for any photo-flow release.

---

### Pattern 9 — Multi-Photo Gallery

**Product/category example**

Claim intake products and strong Mini Programs often keep existing uploaded images visible while new items upload or confirm.

**What users perceive**

"I can see what I already uploaded and add more if needed."

**Hidden engineering discipline**

Page-level loading is separated from item-level progress; thumbnails are lazy; full image loads on demand; refreshes do not wipe usable content.

**How P20 should apply it**

Existing content remains usable during refresh. `已上传，正在确认` is item-level. Minimum required photos do not permanently lock legitimate additional evidence if business rules allow append.

**What not to copy**

Do not copy social media galleries, filters, decorative grids, or heavy full-image preloading.

**Suggested measurable acceptance threshold**

During one active upload/confirmation, already received thumbnails remain visible and previewable; gallery first render does not require loading every full-size image.

---

### Pattern 10 — Error Semantics

**Product/category example**

TurboTax distinguishes validation errors from filing/transmission problems. Mature insurance intake distinguishes missing required information from duplicate, expired link, and backend failure.

**What users perceive**

"The message tells me what I can do next."

**Hidden engineering discipline**

Errors are classified by cause and mapped to retryable, non-retryable, already-complete, validation, duplicate, or contact-broker behavior.

**How P20 should apply it**

Transport errors offer Retry/contact. Expired or invalid tokens route to contact guidance. Validation errors point to fields. Duplicate submit says no resubmit needed. Completed upload does not show retry.

**What not to copy**

Do not copy raw insurer claim codes, stack traces, HTTP payloads, or overly legal language for customers.

**Suggested measurable acceptance threshold**

At least six error classes are tested or manually verified when the path changes: transport, token, validation, duplicate, completed, and server error.

---

### Pattern 11 — Progressive Disclosure

**Product/category example**

TurboTax hides tax complexity behind one question at a time. McDonald's App hides fulfillment complexity until the user needs status. Strong Mini Programs avoid making users understand backend state.

**What users perceive**

"This is simple even though the business is complicated."

**Hidden engineering discipline**

The system maintains rich backend state, provenance, and broker detail while projecting a simple customer view and richer operator view.

**How P20 should apply it**

Customer screens show task, status, missing items, next action, and simple recovery. Workbench may show richer timeline, source, received time, attachments, and supplement history.

**What not to copy**

Do not expose broker audit detail, AI confidence, internal lanes, or workflow codes to customers.

**Suggested measurable acceptance threshold**

Customer-facing screens contain no forbidden internal concepts; broker screens expose enough provenance to trust the case without reading chat history.

---

### Pattern 12 — Broker / Operator Visibility

**Product/category example**

Mature insurance claim intake products succeed when adjusters or brokers can quickly see facts, evidence, missing items, and source. Delivery operations tools similarly expose the task state to operators, not just end users.

**What users perceive**

Customers perceive confidence when broker responses match what they submitted. Brokers perceive speed and trust.

**Hidden engineering discipline**

Customer-side writes, server projections, Workbench API, attachment display, missing-item model, and timeline/provenance stay aligned.

**How P20 should apply it**

Every saved field, uploaded attachment, post-submit supplement, and source/timestamp needed for broker review must be visible in Workbench. Vehicle/opposing-party data and photo attachments require real browser verification, not only code tests.

**What not to copy**

Do not copy full carrier claim management systems, legal adjudication tools, or operator dashboards that imply coverage/fault decisions.

**Suggested measurable acceptance threshold**

For touched paths, one Workbench readback shows fields, attachments, source/timeline, supplements, and missing items; broker can understand the case in about 10 seconds.

---

### Pattern 13 — Low Input Burden

**Product/category example**

McDonald's App minimizes typing for ordering. TurboTax uses guided questions instead of free-form forms. Chinese Mini Programs often favor choice chips, pickers, scan/photo, and short prompts.

**What users perceive**

"This is not a paperwork session on my phone."

**Hidden engineering discipline**

The task contract chooses component types intentionally: selection, photo, scan, confirmation, and short text only where text is truly necessary.

**How P20 should apply it**

Prefer choices for injury/police and structured basics. Use photos for evidence. Keep story text short but large and phone-friendly. Avoid adding dense fields unless they directly improve broker readiness.

**What not to copy**

Do not copy full tax interview length, restaurant customization density, or carrier claim forms with many required text fields.

**Suggested measurable acceptance threshold**

New fields must justify why they are choice/photo/scan/text; text is last resort, labels are persistent, and tap targets are usable in Founder phone QA.

---

### Pattern 14 — Confidence At Completion

**Product/category example**

TurboTax separates "ready to file" from "filed/accepted." Food apps separate "order placed" from "being prepared" and "ready." Claim intake separates broker intake submission from formal carrier claim filing.

**What users perceive**

"My submit counted, I know what happens next, and I can still correct or supplement if needed."

**Hidden engineering discipline**

Completion copy is tied to server-confirmed state, next-step projection, broker authority, and append/supplement rules.

**How P20 should apply it**

Receipt says the materials were submitted to Chen Kui/broker office for review, not formally filed with a carrier. It shows next step, broker contact expectation, possible supplement, and submitted timestamp when available.

**What not to copy**

Do not copy hard SLA promises, coverage/fault decisions, carrier filing language, or "case closed" language.

**Suggested measurable acceptance threshold**

After submit, customer can answer: Did my submit count? Who reviews it? Can I return? Is this a formal carrier filing? The UI answers without support intervention.

---

## 4. Benchmark-Derived Engineering Rules

These engineering rules are the shared implementation substrate behind the benchmark patterns:

1. **Single-flight initialization:** One owner for first render; first `onShow` must not duplicate `onLoad`.
2. **Stable render shape:** All render-bound fields have defaults, and `Page.data` remains JSON-serializable.
3. **Bounded loading:** Every async path has success, recoverable failure, or timeout cleanup.
4. **Stale-response protection:** Request generations, cancellation guards, and page-destruction checks prevent old responses from overwriting newer state.
5. **Item-level async state:** Upload/save/confirmation state belongs to the affected item when the rest of the page remains usable.
6. **Idempotent retry:** Retry reuses stable intent identity; duplicate taps are blocked; completed items never retry.
7. **Lifecycle-safe resume:** `onLoad`, `onShow`, `onHide`, and `onUnload` responsibilities are explicit; resume never duplicates requests, uploads, or submits.
8. **Preflight configuration gates:** Real AppID, QA HTTPS, legal domains, valid launch token, no embedded secrets, clean cache compile, and component Three Gates are release requirements.

---

## 5. P20 Application Map

- **Mini Program customer flow:** Apply task clarity, one CTA, staged progress, local-first feedback, weak-network behavior, photo capture, gallery, resume, error semantics, low input burden, and confidence at completion.
- **H5 task flow:** Apply the same interaction rules as Mini Program, with extra attention to browser refresh, local draft, and server read-back.
- **Broker Workbench:** Apply broker visibility, progressive disclosure, source/timeline clarity, and confidence at completion from the operator side.
- **Evidence/photo workflow:** Apply local-first preview, item-level async state, read-back confirmation, idempotent retry, gallery performance, and Workbench readback.
- **Release readiness:** Apply weak-network behavior, preflight gates, Founder phone QA, and Smoothness Scorecard thresholds before claiming pilot readiness.

---

## 6. Required Prompt Header

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

## 7. How Future Work Uses These Benchmarks

- **Sprint prompt header:** Include the required prompt header before implementation details.
- **Design review:** Name the benchmark patterns that apply and translate them into P20-specific behavior.
- **Focused tests:** Test the hidden engineering discipline behind the chosen patterns, not only visual output.
- **Founder phone QA:** Validate tap feedback, local preview, weak-network copy, upload confirmation, resume, and completion confidence on the target device path.
- **UX Problem Ledger update:** Record any gap between benchmark expectation and current product behavior.
- **Smoothness Scorecard:** Score impacted categories using evidence, especially Upload Experience, Error Recovery, Resume Experience, Broker Workflow, Performance Perception, and Founder Phone QA.
- **Short release readiness audit:** Confirm the release does not copy benchmark visuals, does satisfy benchmark-derived engineering rules, and does not ship over Critical/High ledger issues without explicit acceptance.

---

## 8. Non-Copying Boundary

P20 may reuse interaction methods from benchmark products:

- one current task
- one primary action
- staged progress
- immediate feedback
- background confirmation
- clear retry/contact semantics
- resume without data loss
- evidence capture with confirmation
- operator visibility
- confidence at completion

P20 must not copy:

- visual layouts, brand styles, icons, color systems, or animations
- delivery-driver incentives, map-first routing, or labor metrics
- restaurant upsell patterns
- tax filing density or legal jargon
- carrier claim adjudication language
- account/login portal assumptions
- SLA, coverage, fault, or filing promises that the broker product cannot make
