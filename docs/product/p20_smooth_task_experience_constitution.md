# P20 Smooth Task Experience Constitution

**Sprint:** P20-RC1.3
**Status:** Production UX constitution for Insurance Unified Intake
**Date:** 2026-07-14
**Scope:** Customer Mini Program task flow, evidence/photo workflow, broker Workbench review, and release readiness review
**Relationship to existing constitutions:** Complementary. This document does **not** edit or supersede `docs/product_constitution/P16_CUSTOMER_FIRST_CONSTITUTION.md` or `docs/design/p20_production_constitution_master_design_2026_07_12.md`. It operationalizes their customer-first, append-first, server-driven, broker-controlled rules into a smooth task experience standard.

---

## 1. Purpose

Insurance Unified Intake is a task product, not a generic form, chatbot, CRM, carrier filing system, or visual redesign exercise.

The smooth task standard exists so every future sprint, Cursor prompt, code review, PR review, Founder phone QA pass, and Release Readiness Audit asks the same question:

> Can a stressed insurance customer complete the next small task, trust that nothing was lost, and leave the broker with a clear, sourced case?

This constitution extracts underlying product principles from high-throughput task products such as driver apps, food/order apps, tax interview products, and strong WeChat Mini Programs. It copies no UI. The reusable lessons are:

- one current task
- one current status
- one next action
- low typing
- clear handoff
- durable evidence
- recoverable failure
- fast perceived progress
- human confidence at the decision boundary

---

## 2. Authority and Usage

### Applies To

- Customer task pages: Entry, Task Home, Story, Basics, Photos, Review, Receipt, Error.
- Evidence Gallery / photo slot surfaces.
- Customer Case Builder state, timeline, supplements, and append behavior.
- Broker Workbench queue, case brief, evidence checklist, attachment visibility, and timeline review.
- Release readiness scorecards and Founder phone QA.
- Future Cursor implementation prompts that touch task UX, evidence, upload, retry, resume, Workbench visibility, or pilot polish.

### Does Not Apply To

- Pixel-perfect redesign.
- New feature expansion by itself.
- Carrier claim filing.
- Coverage, fault, rating, payment, or legal decisions.
- Rewriting the existing Product Constitution.

### Review Rule

If a future prompt changes customer flow, evidence capture, upload, retry, resume, or Workbench review, it must reference this document and `docs/product/ux_problem_ledger.md`.

---

## 3. Core Contract

```text
Customer opens one task
  -> sees one current status
  -> sees one next action
  -> provides the smallest useful input
  -> receives immediate feedback
  -> can leave and resume
  -> failures recover or route to broker
  -> evidence appends durably
  -> broker sees a sourced case quickly
```

---

## 4. Principles

### Principle 1 — One Primary Action Per Screen

**Why**

Customers reporting an accident are under stress. A screen with multiple competing primary buttons makes them become product managers. Task apps work because the next action is visually and mentally singular.

**Rules**

- Every customer screen has one primary CTA or one automatic primary transition.
- Secondary actions are visually demoted and never compete with the main CTA.
- Submitted surfaces still obey the rule: one primary post-submit action, not several equivalent supplement buttons.
- Error states may show Retry as primary only when retry can help; contact broker is secondary or sole action for non-retryable cases.

**Examples**

- Photos: primary is `上传下一张` until required slots are received, then `完成并返回我的资料`.
- Review: primary is `提交给陈总审核`; missing rows and supplement actions are recovery paths, not second submits.
- Receipt submitted state: one primary `补充或修改资料` action sheet, plus one secondary overview/status action.

**Anti-patterns**

- Two co-equal buttons such as `继续补充资料` and `继续补充照片` on the same submitted screen.
- A Review page where `返回我的资料` is the only way to fix missing fields.
- Retry shown as primary for an expired token.

**Acceptance Criteria**

- A reviewer can point to exactly one primary action on every screen.
- Double-tapping the primary action cannot create duplicate logical saves, uploads, submits, or navigation.
- Disabled primary actions explain why they are disabled in customer-safe language.

---

### Principle 2 — User Always Knows The Next Step

**Why**

Progress bars and internal workflow names are not enough. Customers need to answer: What has been received? What is still missing? What do I do now?

**Rules**

- Task Home must show current status, received items, missing items, and next action.
- Step pages must explain why the requested information matters.
- Review must distinguish ready vs not ready and provide direct recovery.
- Receipt must say what happens next and whether the broker may ask for more.

**Examples**

- `已收到事故经过` and `还缺事故照片` are better than `60% complete`.
- Receipt copy should say `资料已提交，陈总会查看，可能还需补充`.
- Broker Workbench should mirror the same missing items in broker language.

**Anti-patterns**

- Spinner or `processing` with no explanation.
- `Almost done` while required fields are still missing.
- Showing a missing item but no route to fix it.

**Acceptance Criteria**

- On every screen, a first-time customer can say the next step in one sentence.
- Missing item labels match the actual server/workbench truth.
- No customer-visible internal state names such as `h5t1`, `tenant_id`, `workflow_phase`, or raw `case_id`.

---

### Principle 3 — Never Lose Customer Work

**Why**

The product promise fails the moment a customer types, uploads, or submits and the system loses it. Insurance workflows are evidence-heavy; data loss creates customer anxiety and broker distrust.

**Rules**

- In-progress text must be preserved on save failure, retry, navigation interruption, and resume where feasible.
- Uploaded evidence must be recorded with durable metadata or an explicit recoverable failure state.
- Success must be confirmed only after authoritative read-back when the backend is the source of truth.
- Customer-confirmed facts cannot be silently overwritten by AI or later chat extraction.

**Examples**

- Story text remains visible after a network save failure.
- Photo count increments only after upload and server read-back.
- Post-submit supplement writes timeline before/after metadata and preserves submitted status.

**Anti-patterns**

- Clearing a textarea before save confirmation.
- Toasting upload success before the case attachment exists.
- Broker cannot see a field or attachment the customer was told was saved.

**Acceptance Criteria**

- Kill/reopen, network failure, and retry QA include data-preservation checks.
- Workbench readback confirms customer-visible saved items are broker-visible.
- Any save/upload error leaves the customer with retry or broker-contact recovery.

---

### Principle 4 — Append First, Split Later

**Why**

Customers should not manage case boundaries while under stress. Ordinary supplements belong to the current task/timeline first. AI, broker, and backoffice can classify, split, merge, or flag exceptions later.

**Rules**

- Ordinary inbound text/photos append to the current task timeline.
- Ambiguous media is retained, never discarded, and made visible to broker review.
- Strong new-case signals may trigger confirmation or broker review, but the default is not to make the customer choose internal boundaries.
- Append events must keep source, timestamp, actor, and provenance.

**Examples**

- WeCom photo after claim start is received into the current claim evidence flow.
- Post-submit edits append supplement timeline events instead of reopening submit.
- Possible duplicate/multi-claim context becomes a broker-visible flag, not a customer-facing lane puzzle.

**Anti-patterns**

- Asking `Is this a new accident or the old accident?` for every photo.
- Dropping an attachment because its slot is unclear.
- Silently merging conflicting facts without timeline evidence.

**Acceptance Criteria**

- New media/text has a durable event even if binding is uncertain.
- Broker can see append history and source channel.
- Customer is asked a boundary question only when the system has a strong reason and no safer broker-side path.

---

### Principle 5 — Async Whenever Possible

**Why**

The customer should not wait for enrichment, OCR, AI summary, broker analysis, or slow downstream processing when the next customer action can proceed.

**Rules**

- Customer-critical save/upload/submit paths return quickly with authoritative receipt or clear pending state.
- AI extraction, OCR, summaries, dedup checks, and broker brief enrichment run in the background when they are not required to unblock the customer.
- Async tasks must expose enough status to prevent confusion.

**Examples**

- Upload records the photo and confirms receipt before later OCR or classification.
- Broker brief can improve after customer submit without delaying the customer's receipt page.
- Attachment preview can show `received` while full classification remains pending.

**Anti-patterns**

- Blocking customer submit on non-essential AI summary.
- A bare spinner while the backend warms embeddings or enriches a brief.
- Requiring OCR before broker can see a raw attachment.

**Acceptance Criteria**

- Each async operation is classified as customer-blocking or background.
- Background work failure does not erase customer work.
- Customer-facing copy says what is happening when waiting is unavoidable.

---

### Principle 6 — Immediate Feedback

**Why**

Fast feedback is the difference between confidence and repeated taps. Driver and order apps feel reliable because every tap acknowledges state.

**Rules**

- Every tap, save, upload, retry, and submit produces visible feedback.
- Busy states disable duplicate actions and show progress text.
- Success copy must match the actual operation completed.
- Feedback must not rely only on color.

**Examples**

- Save CTA enters loading, then shows `已保存`.
- Upload shows slot-level progress and `上传成功` after read-back.
- Retry cooldown says `请稍候再试`.

**Anti-patterns**

- Button appears tappable while upload is already running.
- Upload succeeds but the UI still shows a failure state.
- Success toast disappears so quickly that Receipt is the only visible confirmation, unless Receipt clearly carries the confirmation.

**Acceptance Criteria**

- QA checks loading, success, failure, and cooldown states per page.
- Progress state clears on both success and failure.
- No completed upload remains presented as retryable.

---

### Principle 7 — Never Block Customer Unnecessarily

**Why**

Insurance intake is partial by nature. The product should collect what the customer can provide now, explain what remains, and let the broker decide what is sufficient.

**Rules**

- Required fields block formal submit only when truly required for broker review.
- Optional evidence should remain optional and visible as optional.
- Post-submit supplements must be allowed through explicit allowlists where the business flow supports correction.
- Safety or legal escalations route to broker; they do not trap the customer in a broken task.

**Examples**

- Other-party info can be partial when the customer only has a plate or photo.
- Injury = yes routes to broker/manual handling without pretending normal checklist is enough.
- Customer can submit complete minimum intake even if optional scene photos are missing.

**Anti-patterns**

- Blocking all progress because one optional photo is absent.
- Returning `already_submitted` for an allowed post-submit correction.
- Making customer restart because a token or page state is stale.

**Acceptance Criteria**

- Required vs optional is explicit in task contract, UI, and Workbench.
- Formal submit gate matches broker-ready minimums.
- Post-submit supplement routes are tested for persistence and no duplicate submit.

---

### Principle 8 — Fast Perceived Performance

**Why**

Perceived speed matters as much as raw latency on mobile. Customers tolerate work when they know what is happening and can see progress.

**Rules**

- Never show an unexplained spinner.
- Prefer skeleton/status text, slot progress, optimistic local preview with authoritative read-back, and short confirmation loops.
- Keep page transitions direct and avoid unnecessary intermediate pages.
- Slow paths must provide safe escape or contact.

**Examples**

- Entry says `正在打开您的资料...`.
- Photos show local preview while uploading, then server-confirmed received state.
- Receipt loads with a success/status hero, not a blank shell.

**Anti-patterns**

- White screen during task bootstrap.
- Upload appears frozen with no percent, slot status, or toast.
- Customer waits for a broker-only summary before continuing.

**Acceptance Criteria**

- Manual phone QA includes slow network and real upload checks.
- Any loading state has text explaining the wait.
- Long operations have either progress, retry, or contact path.

---

### Principle 9 — Progressive Disclosure

**Why**

Insurance cases are complex, but the customer frontend must stay simple. The customer should see the next small decision, not the entire internal model.

**Rules**

- Start with high-value structured choices, photos, and short text.
- Reveal advanced details only when needed for the current task.
- Broker Workbench may show richer timeline/provenance than the customer UI.
- Safety disclaimers stay visible where they matter, but they must not drown out the task.

**Examples**

- Task Home summarizes received/missing items; detailed timeline belongs in Workbench or overview.
- Basics uses choice chips for injury/police and text only where necessary.
- Review shows summary plus direct edit links instead of every raw event.

**Anti-patterns**

- Showing provenance, confidence, lane, token, or workflow internals to customers.
- Long dense forms before the customer has committed to the task.
- Broker audit details pushed onto the customer receipt.

**Acceptance Criteria**

- Each field is justified as choice/photo/scan/text, with text as last resort.
- Customer screens show only customer-safe labels.
- Broker screens expose enough evidence detail for review without requiring chat scrolling.

---

### Principle 10 — Resume Anywhere

**Why**

Mobile customers close apps, lose signal, switch to WeChat, and return later. Resume is not an edge case; it is a normal case.

**Rules**

- Customer can resume from Entry, Task Home, step pages, Review, and Receipt.
- Resume must restore server truth and, where safe, local drafts.
- Submitted tasks resume to submitted status, not a new claim.
- Resume feedback must reassure the customer when content was restored.

**Examples**

- Relaunch after partial Story shows restored draft/server state.
- Relaunch after submit lands on Receipt or submitted Task Home.
- Task Home toast says `已恢复您上次填写的内容`.

**Anti-patterns**

- Browser/session-only state as the only continuity path.
- Creating a new task after a submitted receipt resume.
- Losing typed text when leaving a step before save failure recovery.

**Acceptance Criteria**

- QA covers kill/reopen mid-task and after submit.
- Resume does not duplicate formal submit, uploads, or case records.
- Resume messages are understandable and not engineer-facing.

---

### Principle 11 — Recover Instead Of Fail

**Why**

Failures are expected on mobile networks and WeChat/Cloud/local test paths. The product should recover, explain, or route to the broker instead of dead-ending.

**Rules**

- Retryable errors show bounded Retry and broker contact.
- Non-retryable errors show contact path and no false retry hope.
- Retry should reuse local photo/text when available.
- Error copy must be customer-safe Chinese for customer-facing surfaces.

**Examples**

- Network failure: `网络暂时不稳定，请重试` plus Retry and `联系陈总`.
- Expired token: contact guidance, no hopeful retry loop.
- Failed upload slot: retry uses existing local image without forcing re-pick.

**Anti-patterns**

- Raw IP, script, stack, token, or API code shown to customer.
- Infinite retry loop or retry with no changed outcome.
- Completed upload still shows Retry.

**Acceptance Criteria**

- Edge QA covers unreachable API, expired token, upload fail, save fail, and submit fail.
- Every blocking error has a recovery or contact path.
- Retry attempts are bounded or cooled down.

---

### Principle 12 — Customer Confidence

**Why**

Customers need to trust that the broker received their materials, that they did not file a carrier claim by accident, and that they can correct or supplement.

**Rules**

- Customer copy must distinguish intake from formal carrier filing.
- Submit confirmation must be explicit.
- Broker-contact expectation must be clear.
- The product must not promise fixed SLAs or coverage/fault outcomes.

**Examples**

- `提交给陈总审核` is acceptable; `正式报案成功` is forbidden.
- Receipt says the broker office will review and may contact for more.
- Safety note explains broker confirmation boundary.

**Anti-patterns**

- Copy implying coverage confirmed, claim filed, liability determined, or guaranteed response time.
- `Success` without saying what succeeded.
- Hidden broker contact path during confusion.

**Acceptance Criteria**

- Forbidden insurance claims are checked in copy review.
- Receipt and Task Home can answer `Did my submit count?`.
- Customer can find help without needing to trigger an error.

---

### Principle 13 — Broker Confidence

**Why**

The broker is the buyer/operator and final authority. The product succeeds only if the broker can understand the case quickly and trust what is shown.

**Rules**

- Workbench must show a concise case brief first, then evidence and timeline detail.
- Customer-visible saved fields and uploaded attachments must be visible to broker review.
- Evidence must show source channel, received time, and slot/status when available.
- Broker actions close, request more, or escalate; AI never closes the case.

**Examples**

- Claim brief includes time, location, story, injury/police, vehicle/opposing-party fields.
- Evidence checklist shows received/missing photos with source.
- Timeline shows H5 field saves, uploads, submit, and post-submit supplements.

**Anti-patterns**

- Broker has to scroll WeChat to find photos after customer uploaded them.
- Workbench list shows a case but drawer lacks attachments.
- AI summary hides the raw evidence chain.

**Acceptance Criteria**

- Release QA includes Workbench readback for every customer input path touched.
- Broker can understand the case in about 10 seconds from the brief.
- Attachments and supplements are audit-visible, not only customer-visible.

---

### Principle 14 — AI Assists Instead Of Interrupts

**Why**

AI creates value by organizing, extracting, and summarizing. It destroys trust when it becomes the customer flow owner or decision maker.

**Rules**

- AI may classify, extract, summarize, suggest next questions, and flag risks.
- AI may not decide coverage, liability, filing, completion, identity, or broker done.
- AI outputs are provisional unless confirmed by customer structured input or broker action.
- AI work should run in the background when possible.

**Examples**

- AI extracts possible location from chat, but H5/customer confirmation or broker correction wins.
- AI suggests missing-info question; workflow state decides whether it is required.
- AI summary appears in broker brief with source references.

**Anti-patterns**

- AI advances workflow phase without state machine rules.
- AI overwrites `customer_confirmed` facts silently.
- Chatbot-style interaction replaces the task UI for core intake.

**Acceptance Criteria**

- Every AI mutation has provenance and does not bypass state machine/broker boundaries.
- Customer screens do not show AI confidence or raw extraction internals.
- Broker can see source evidence behind AI-assisted summaries.

---

### Principle 15 — Production Polish Before Feature Growth

**Why**

Pilot trust comes from smooth completion, not breadth. A narrow task that is polished, recoverable, and broker-visible beats a larger feature set with upload confusion and manual QA gaps.

**Rules**

- Fix known UX ledger issues before adding adjacent features.
- Manual Founder phone QA is required for release confidence when upload, resume, or WeChat real-device behavior changes.
- Do not ship new feature growth over unresolved Critical/High smoothness issues.
- Production config, HTTPS/domain readiness, and experience-version hygiene count as UX.

**Examples**

- Resolve healthy Task Home contact and real-device upload proof before expanding workflow fields.
- Verify Workbench visibility before claiming customer save/upload complete.
- Freeze pilot config before inviting a broker/customer.

**Anti-patterns**

- Adding OCR while photo upload is still slow/confusing.
- Adding more fields while existing fields are tiny or hard to use.
- Calling automated tests alone a pilot pass when DevTools/phone QA is unrun.

**Acceptance Criteria**

- Release readiness references `smoothness_scorecard.md` and `ux_problem_ledger.md`.
- No Critical issue remains open for pilot/customer release.
- High issues require explicit Founder acceptance if not fixed.

---

## 5. Release Review Gates

A release touching task UX, upload, resume, Workbench readback, or evidence must pass these gates:

1. **Constitution check:** no principle violation without explicit Founder-approved exception.
2. **Ledger check:** no new issue unrecorded in `ux_problem_ledger.md`.
3. **Scorecard check:** all categories scored in `smoothness_scorecard.md`.
4. **Customer path check:** Entry -> Task Home -> step pages -> Review -> Receipt has no dead end.
5. **Photo path check:** upload, progress, retry, read-back, duplicate guard, and Workbench visibility tested.
6. **Resume check:** mid-task and post-submit resume tested.
7. **Broker check:** broker sees fields, attachments, supplements, timeline, and missing items.
8. **Founder phone QA check:** real-device path tested or explicitly marked blocked.

---

## 6. Future Cursor Prompt Reference

Future prompts should include:

```text
Before changing task UX, upload/photo flow, resume, retry, evidence, or Workbench review:
- Read docs/product/p20_smooth_task_experience_constitution.md
- Read docs/product/ux_problem_ledger.md
- Score the change with docs/product/smoothness_scorecard.md
- Do not add feature growth over unresolved Critical/High smoothness issues unless Andy explicitly accepts the risk
```

---

## 7. Non-Negotiable Summary

- One task.
- One status.
- One primary action.
- Save customer work.
- Append evidence first.
- Recover visibly.
- Keep customer UI simple.
- Keep broker review trustworthy.
- Let AI help quietly.
- Polish the production task before growing features.
