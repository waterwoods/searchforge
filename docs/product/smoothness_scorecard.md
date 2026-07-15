# Smoothness Scorecard

**Sprint:** P20-RC1.3
**Status:** Production release review checklist for Insurance Unified Intake
**Date:** 2026-07-14
**Companion docs:** `p20_smooth_task_experience_constitution.md`, `ux_problem_ledger.md`

---

## 1. Purpose

Use this scorecard before any release, experience-version upload, broker pilot, PR review, or Release Readiness Audit that touches customer task UX, uploads/photos, resume, retry, evidence, or Broker Workbench review.

The score is not a vanity grade. It is a release decision aid. A narrow release with low feature scope can still fail if the task experience is confusing, lossy, or unverified on phone.

---

## 2. Scoring Scale

| Score | Meaning | Release Guidance |
|-------|---------|------------------|
| 1 | Broken or unverified on the target path. | Block release. |
| 2 | Works in some paths but has serious confusion, dead ends, or missing proof. | Do not release to customer; fix or explicitly downgrade scope. |
| 3 | Usable with known issues and documented workaround. | Accept only for internal/founder QA or tightly controlled pilot. |
| 4 | Good production candidate with minor known risks. | Release candidate if Critical issues are closed and High issues accepted/fixed. |
| 5 | Smooth, verified, resilient, and broker/customer confidence is high. | Release-ready for the intended audience. |

---

## 3. Release Gates

| Gate | Rule |
|------|------|
| Critical issue gate | Any open Critical issue in `ux_problem_ledger.md` blocks customer/broker release unless Andy explicitly changes scope to internal-only. |
| High issue gate | Any open High issue needs a named acceptance decision or fix before release. |
| Minimum category gate | No category may score below 3 for pilot; no category may score below 4 for production release. |
| Founder phone gate | If upload, resume, or WeChat real-device behavior changed, Founder phone QA must be scored. |
| Broker confidence gate | Customer-visible saved/uploaded data must be visible in Workbench before claiming release readiness. |

---

## 4. P20 Photo Flow Freeze Scorecard — 2026-07-14 Founder Evidence

This score update is limited to the Founder iPhone evidence captured for the Mini Program photo path. It does not claim a full release audit, deployment, precise latency measurement, failure-edge phone QA, or HEIC / HEIF end-to-end proof.

| Category | Score (1-5) | Founder Evidence | Release Guidance |
|----------|-------------|-------------------|------------------|
| Upload Experience | 4 | Real iPhone WeChat Preview upload worked; adding another photo PASS; observed upload experience approximately 2-3 seconds; no duplicate attachment observed. Timing was observed, not precisely measured. | Good candidate for freezing the verified photo path; keep regression tests for upload intent, retry, read-back, and duplicate guard. |
| Photo Workflow | 4 | Photos page no longer white-screens; confirmed category still allows Add More; completed/current photo path did not show duplicate attachment in Founder test. HEIC / HEIF source format not proven. | Freeze current verified photo path; keep HEIC / HEIF as separate Medium follow-up. |
| Broker Workflow | 4 | Broker Workbench displayed the new photo from the iPhone test. | Broker photo visibility PASS for this path; broader Workbench layout/source clarity remains normal watchlist. |
| Performance Perception | 4 | No indefinite full-page loading observed; upload completed in approximately 2-3 seconds from Founder observation. | Good for this freeze; do not convert the approximate observation into a precise performance SLA. |
| Production Polish | 3 | Founder evidence supports the phone photo path; focused release checks and component/preflight gates remain the commit-time proof. | Freeze only after focused checks pass; no deploy or broad audit implied. |
| Founder Phone QA | 4 | Real iPhone WeChat Preview path tested successfully for adding another photo, first render, loading closure, Workbench visibility, and duplicate observation. | Phone photo path PASS for this freeze; failure-edge phone QA and HEIC / HEIF proof remain outside this evidence. |

---

## 5. Scorecard Template

Copy this table into release notes or readiness audits.

| Category | Score (1-5) | Evidence Required | Release Guidance |
|----------|-------------|-------------------|------------------|
| Navigation | | Entry -> Task Home -> Story/Basics/Photos -> Review -> Receipt has no dead end; back/return paths work. | 1-2 blocks; 3 internal QA only; 4-5 pilot/production candidate. |
| Clarity | | Every screen shows current status, instruction, and next action in customer-safe language. | Score below 4 means more copy/state polish before customer pilot. |
| Input Effort | | Text fields are minimized, labels persistent, tap targets usable, choices/photos used where better than typing. | Score below 4 means phone friction likely. |
| Upload Experience | | Photo upload progress, busy guard, success read-back, failure state, retry, and duplicate guard verified. | Score below 4 blocks photo-heavy pilot. |
| Error Recovery | | Network fail, expired token, save fail, upload fail, submit fail show retry/contact behavior correctly. | Score below 4 blocks customer release. |
| Resume Experience | | Kill/reopen mid-task and post-submit resume restore correct state without duplicate case/submit. | Score below 4 requires controlled pilot only. |
| Broker Workflow | | Workbench shows case brief, fields, attachments, supplements, missing items, source/timeline. | Score below 4 blocks broker-facing pilot claims. |
| Photo Workflow | | Required/optional slots clear; HEIC/phone compatibility tested; completed photos not retryable; additional evidence path understood. | Score below 4 blocks accident-photo pilot. |
| Customer Confidence | | Customer can tell submit counted, broker will review, and this is not formal carrier filing. | Score below 4 risks support calls/confusion. |
| Performance Perception | | No blank/unknown waits; loading has text; slow upload/save paths provide progress or recovery. | Score below 4 requires visible progress polish. |
| Production Polish | | Config frozen, no prototype/local leaks, component gates pass, copy consistent, ledger updated. | Score below 4 means not release-ready even if code tests pass. |
| Founder Phone QA | | Real phone or target-device path run, including upload, resume, and failure edge if applicable. | Score below 4 blocks external pilot unless explicitly waived. |

---

## 6. Category Rubrics

### Navigation

**1:** Page crashes, white screens, or customer cannot reach the next required step.
**2:** Main path works only with manual workaround; Review/Receipt/return paths contain dead ends.
**3:** Main path works, but some recovery or post-submit routes remain unclear.
**4:** Main and recovery paths work; minor wording or route polish remains.
**5:** Customer always has a clear route forward, back, resume, or contact broker.

### Clarity

**1:** Customer sees internal jargon or cannot tell what the page is for.
**2:** Basic labels exist but status/next action is ambiguous.
**3:** Most screens are clear; edge states or submitted states need polish.
**4:** Current status, received/missing, and next action are clear.
**5:** A first-time customer can complete the journey without explanation.

### Input Effort

**1:** Long forms, tiny fields, placeholder-only labels, or excessive typing.
**2:** Text-heavy flow with limited mobile affordances.
**3:** Acceptable typing load, but some fields should become choice/photo/scan.
**4:** Low typing; choices/photos used appropriately; fields are phone-friendly.
**5:** Inputs feel native, short, obvious, and hard to misuse.

### Upload Experience

**1:** Upload fails, loses files, duplicates, or cannot be verified.
**2:** Upload works sometimes but progress/retry/success state is confusing.
**3:** Automated upload path works; real-device or edge proof incomplete.
**4:** Upload, retry, read-back, duplicate guard, and failure recovery verified.
**5:** Upload feels fast, reliable, and broker-visible across target phone/file types.

### Error Recovery

**1:** Errors dead-end, expose technical details, or lose work.
**2:** Retry exists but is misleading or inconsistent.
**3:** Common errors recover; some edge states unverified.
**4:** Retryable/non-retryable paths are clear, bounded, and customer-safe.
**5:** Customer always knows whether to retry, wait, resume, or contact broker.

### Resume Experience

**1:** Closing/reopening loses work or creates duplicate cases.
**2:** Resume works only from one page or creates stale state.
**3:** Main resume path works; post-submit or draft restore needs proof.
**4:** Mid-task and post-submit resume are verified.
**5:** Resume feels intentional, reassuring, and exactly continues the task.

### Broker Workflow

**1:** Broker cannot find the case or evidence.
**2:** Case appears but fields/photos/supplements are missing or hidden.
**3:** Broker can review with some manual scanning or incomplete source clarity.
**4:** Broker brief, attachments, missing items, and timeline are visible.
**5:** Broker understands the case in about 10 seconds and can trust sources.

### Photo Workflow

**1:** Required photos cannot be captured, uploaded, or reviewed.
**2:** Photos upload but slot count, retry, or preview is confusing.
**3:** Basic slots work; HEIC/additional evidence/phone QA incomplete.
**4:** Slot identity, optional evidence, retry, preview, and broker visibility are verified.
**5:** Photo capture feels like a polished mobile task, not a form attachment.

### Customer Confidence

**1:** Customer cannot tell whether submit counted or what happens next.
**2:** Copy risks implying carrier filing, coverage/fault decision, or false SLA.
**3:** Submit/result copy is acceptable but help/status is hard to find.
**4:** Customer sees submit status, next step, broker role, and supplement path.
**5:** Customer feels calm: saved, submitted, broker will review, can return.

### Performance Perception

**1:** Blank screen, frozen upload, or unexplained wait.
**2:** Loading exists but lacks useful progress/copy.
**3:** Most waits are explained; slow upload/device path still uncertain.
**4:** Loading, progress, busy, and success states are consistently visible.
**5:** The journey feels responsive even when network/backend work is slow.

### Production Polish

**1:** Prototype config, local URLs, broken component gates, or inconsistent copy.
**2:** Tests pass but release packaging/config/readiness unclear.
**3:** Internal demo candidate with documented rough edges.
**4:** Config frozen, gates pass, copy consistent, ledger updated.
**5:** Release package is boring: predictable, documented, reversible, and polished.

### Founder Phone QA

**1:** Not run and target path depends on phone behavior.
**2:** DevTools only; no phone/LAN/HTTPS validation.
**3:** Phone path run partially; upload or resume proof incomplete.
**4:** Full phone path run with screenshots/notes and known issues logged.
**5:** Phone path run under realistic network/file conditions, including recovery edges.

---

## 7. Score Interpretation

| Overall Result | Meaning | Action |
|----------------|---------|--------|
| Any Critical open | Release blocked. | Fix or change scope to internal-only with explicit note. |
| Any category 1-2 | Not smooth enough for pilot. | Fix before external exposure. |
| Average below 3.5 | Internal QA only. | Continue stabilization. |
| Average 3.5-4.2 | Controlled pilot candidate if no Critical open and High risks accepted. | Run Founder phone QA and Workbench readback. |
| Average above 4.2 | Strong release candidate. | Proceed if config/deploy/runbook gates also pass. |

---

## 8. Required Evidence Checklist

Before marking a release smooth, attach or reference evidence for:

- Full customer journey: Entry -> Task Home -> Story -> Basics -> Photos -> Review -> Receipt.
- One failed network path.
- One expired/missing token path.
- One save failure with text preserved.
- One photo upload success with read-back.
- One photo upload failure and retry.
- One duplicate upload tap attempt.
- One mid-task resume.
- One post-submit resume.
- One post-submit supplement save.
- One Workbench readback showing fields, attachments, timeline/supplement, and missing items.
- One Founder phone QA path when target release includes phone/customer usage.

---

## 9. Review Prompt

Future Cursor prompts may paste this block:

```text
Use docs/product/p20_smooth_task_experience_constitution.md as the UX authority.
Update docs/product/ux_problem_ledger.md for any new/fixed UX issue.
Score the release/change with docs/product/smoothness_scorecard.md.
Do not mark release-ready if upload, resume, broker visibility, or Founder phone QA is below 4 unless Andy explicitly accepts the risk.
```
