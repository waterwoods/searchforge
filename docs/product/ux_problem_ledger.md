# UX Problem Ledger

**Sprint:** P20-RC1.3
**Status:** Living UX risk ledger for Insurance Unified Intake
**Date:** 2026-07-14
**Issue count at creation:** 24
**Companion docs:** `p20_smooth_task_experience_constitution.md`, `smoothness_scorecard.md`

---

## 1. Purpose

This ledger records known smoothness problems discovered through Founder testing, P19/P20 design work, evidence reports, DevTools checklist preparation, pilot blocker review, and current product audits.

It is not a backlog of feature ideas. It is a production UX risk ledger. Future sprints must update this file when they discover, fix, verify, reopen, or accept a task-experience issue.

---

## 2. Priority Definitions

| Priority | Meaning | Release Guidance |
|----------|---------|------------------|
| Critical | Can block pilot/customer completion, cause data/evidence loss, or make real-device use impossible. | Must fix or explicitly block release. |
| High | Creates serious confusion, duplicated work, broker distrust, or high-risk manual workaround. | Fix before release unless Andy explicitly accepts the risk. |
| Medium | Noticeable smoothness or confidence issue with workaround or automation coverage but incomplete manual proof. | Track and verify before broad release. |
| Low | Polish inconsistency or minor wording/perception issue. | Acceptable for pilot if documented. |

---

## 3. Critical Issues

| ID | Problem | Customer Impact | Root Cause | Fix | Verification Status | Regression Risk |
|----|---------|-----------------|------------|-----|---------------------|-----------------|
| C1 | Full manual DevTools walkthrough not yet signed off. | Unknown page, navigation, toast, component, and edge-state failures can block Chen Kui dry-run. | Automated tests exist, but human WeChat DevTools journey rows remain unchecked. | Execute `docs/qa/p20_devtools_walkthrough_checklist.md`; record PASS/FAIL with screenshots; update this ledger. | Open. Checklist exists; no full manual PASS. | High. Any page migration or component registration can regress runtime behavior despite tests. |
| C2 | Real-phone HTTPS / WeChat合法域名 path not ready. | Phone preview or pilot customer cannot reliably call API or upload photos. | Localhost/WSL2 path and DevTools domain bypass do not represent real device. | Stand up HTTPS pilot API, whitelist request/upload domains, set pilot `apiBaseUrl`, verify one full real-device upload. | Verified on iPhone for the current QA Preview photo path on 2026-07-14: real iPhone WeChat Preview worked, photo add-more PASS, Photos first render PASS, no indefinite full-page loading, observed upload experience approximately 2-3 seconds. No deploy performed; broader launch/domain policy remains outside this freeze. | High. Config drift can silently break customer devices. |
| C3 | Upload success can be perceived or shown as failure. | Customer repeats upload, loses confidence, or contacts broker unnecessarily after a successful upload. | UI state can race local upload status, server read-back, and slot state; slow network increases ambiguity. | Confirm success only after read-back; clear error/retry state when slot is received; add manual test for success-after-failure. | Verified on iPhone on 2026-07-14 for the current photo path: upload completed without white screen or indefinite full-page loading; observed upload experience approximately 2-3 seconds. Timing was observed, not precisely measured. | High. Upload refactors, retries, and read-back timing can reintroduce stale error state. |
| C4 | Broker cannot always see what customer believes was saved/uploaded. | Broker distrust; customer says "I already sent it" while Workbench lacks visible evidence. | Historical gaps in Workbench filters, attachment panel visibility, vehicle field rendering, or source projection. | Workbench readback must verify fields, attachments, source, and supplement timeline for every customer path touched. | Verified on iPhone / Workbench readback on 2026-07-14 for this photo path: Broker Workbench displayed the new photo; no duplicate attachment was observed. | High. Customer surface and broker surface can drift independently. |

---

## 4. High Issues

| ID | Problem | Customer Impact | Root Cause | Fix | Verification Status | Regression Risk |
|----|---------|-----------------|------------|-----|---------------------|-----------------|
| H1 | Tiny or hard-to-use text fields. | Customer struggles to type accident story, vehicle info, or location on phone; may abandon or provide low-quality data. | Prototype-era forms leaned on text input before TaskField/mobile sizing standard was fully applied. | Use large labeled fields, persistent labels, adequate tap targets, short prompts, and choice/photo alternatives where possible. | Open for Founder phone QA. | Medium. New fields can copy old dense form patterns. |
| H2 | Slow photo upload feels stuck. | Customer taps repeatedly, exits, or assumes upload failed. | Real-device/network path not proven; upload progress and perceived performance need phone validation. | Slot-level progress, busy guard, local preview, read-back success, and real-device slow-network QA. | Verified on iPhone on 2026-07-14 for current photo path: no indefinite full-page loading; upload experience observed at approximately 2-3 seconds. Not a precise latency measurement. | High. Network and WeChat upload behavior vary by device/environment. |
| H3 | Three-photo limitation / fixed photo count can be too rigid. | Customer may have more than the required evidence or cannot represent required/optional photos naturally. | Earlier evidence pack thinking used fixed count/slots instead of expandable slot identity and supplement model. | Keep required slots clear, allow optional/additional supplements where supported, and show received vs still needed by slot. | Verified on iPhone on 2026-07-14: confirmed category still allowed Add More; adding another photo PASS. | Medium. Future photo UI can accidentally reintroduce count-first logic. |
| H4 | Duplicate uploads. | Broker sees duplicate evidence; customer wastes time and storage; timeline becomes noisy. | Repeated taps, retry races, and missing content-hash/slot dedup can create duplicate logical attachments. | Busy guard client-side; content-hash or slot+hash idempotency server-side; duplicate upload regression tests. | Verified on iPhone / Workbench observation on 2026-07-14 for this path: no duplicate attachment was observed after adding another photo. | High. Retry and upload progress changes often affect dedup. |
| H5 | Confusing retry flow. | Customer retries when retry cannot help, or does not know when to contact broker. | Retryable and non-retryable errors were historically inconsistent across pages. | Use `TaskError` pattern: bounded retry for network/transient failures; contact-only for expired/missing token; shared broker contact modal. | Code/tests support mapped paths; live DevTools edge verification open. | High. Error mapping and page-specific handlers can drift. |
| H6 | Completed upload still retryable. | Customer may retry an already received photo and create confusion or duplicates. | Slot state can fail to clear old local error/retry affordance after read-back confirms received. | Received state must suppress retry and show clear `uploaded/received` status; add success-after-retry test. | Verified on iPhone on 2026-07-14 for the current add-more path by absence of duplicate attachment after completion; focused regression coverage still required for completed-upload retry suppression. | Medium. State-race regression risk on upload refactor. |
| H7 | Insufficient progress feedback. | Customer cannot tell whether save/upload/submit worked or what remains. | Earlier surfaces used sparse toasts or counts without received/missing/next-action clarity. | Task Home status card, progress text, missing list, per-slot upload progress, read-back confirmation. | Improved in P20 Task UI Kit and A2b/A2c work; full journey manual QA open. | Medium. New pages can omit progress text. |
| H9 | Healthy Task Home lacks always-visible `联系陈总`. | Customer who is confused but not in an error state may not find help. | Contact broker action was wired mainly into error chrome and recovery states. | Add a demoted healthy-hub contact action bound to existing contact modal. | Open in pilot blocker list. | Medium. Easy to regress if secondary actions are consolidated without contact rule. |
| H10 | Review missing items lacked direct edit path. | Customer sees missing fields but cannot fix them directly; Review becomes a dead end. | Missing labels were informational rows without navigation/recovery CTA. | Tappable missing rows plus shared recovery CTA to Basics/appropriate page. | Fixed in code; manual DevTools verification required. | Medium. New missing item types may lack route mapping. |
| H11 | Submitted customer actions were repetitive/overlapping. | Customer uncertainty after formal submit; risk of wrong tap path or perceived duplicate submit. | Submitted Task Home/Receipt exposed multiple supplement/photo/view variants. | One submitted primary `补充或修改资料` action sheet plus one secondary status/overview action. | Fixed in code per evidence; manual verification required. | Medium. Future supplement entry points can sprawl again. |

---

## 5. Medium Issues

| ID | Problem | Customer Impact | Root Cause | Fix | Verification Status | Regression Risk |
|----|---------|-----------------|------------|-----|---------------------|-----------------|
| M1 | Network failure path not manually proven. | Customer could see raw technical error, dead end, or stale loading state offline. | Automation covers mapping; DevTools/phone edge scenario not executed. | Force unreachable `apiBaseUrl`; verify Chinese copy, Retry, cooldown, and `联系陈总`. | Open. | Medium. Error copy and fallback routing can drift. |
| M2 | Expired or invalid token path not manually proven. | Customer may loop on Retry instead of contacting broker. | Code maps non-retryable errors, but live fixture run remains TODO. | DevTools expired-token fixture; verify contact-only path and no hopeful retry. | Open. | Medium. Entry/error handling changes can regress. |
| M3 | Basics multi-PATCH partial-save risk. | Hub/workbench can show partial data after mid-save failure, confusing customer and broker. | Sequential field patches rather than single section-group save in legacy path. | Move to single section-group save when contract allows; until then preserve values and show recoverable failure. | Accepted risk for first DevTools gate; watch during walkthrough. | Medium. Field additions increase partial-save surface. |
| M4 | Post-submit supplement backend/frontend mismatch risk. | Customer reaches edit page but save fails or submitted state becomes inconsistent. | Formal submit is one-time, while supplements need explicit post-submit allowlist and timeline semantics. | Keep submit idempotent; allow strict supplement fields; append before/after timeline; test no duplicate submit. | Fixed in code/tests; manual DevTools still required. | Medium. New supplement fields can miss allowlist/timeline rules. |
| M5 | Vehicle / other-party Workbench browser visibility unclear. | Broker may fail 10-second scan even when data was saved. | Persistence/API/render tests pass, but real browser case visibility was not manually signed. | Open real claim with vehicle fields; verify rows above the fold or placeholder `—`. | Open manual verification. | Medium. Workbench layout changes can hide important fields. |
| M6 | Attachment preview may fail for some WeCom objects. | Broker sees attachment row but cannot preview image, forcing chat fallback. | Preview/signed-link/object compatibility for some WeCom media remains uneven. | Track preview failures separately; verify thumbnail/full preview for H5 and WeCom sources. | Known residual risk from Workbench smoke evidence. | Medium. Storage/signing/display changes can break preview. |
| M7 | Source/provenance not scannable enough in broker view. | Broker cannot quickly distinguish H5 official submit, WeCom supplement, AI draft, or broker correction. | Evidence chain exists, but UI prominence of source badges/timeline can lag. | Show source channel, actor, received time, and confidence/provisional status where broker needs it. | Partially implemented; ongoing Workbench UX debt. | Medium. New evidence types can arrive without source clarity. |
| M8 | HEIC / HEIF end-to-end format verification remains open. | iPhone customers may upload photos that fail preview, conversion, MIME validation, or broker display if the actual prepared/uploaded file is HEIC/HEIF. | The 2026-07-14 iPhone success does not prove HEIC: WeChat may have produced a JPEG temporary/compressed file. Actual source/prepared MIME and extension evidence was not captured. | Separate focused sprint: capture actual source and prepared MIME/extension; if HEIC/HEIF is confirmed, durable policy remains canonical JPEG conversion rather than relying on raw HEIC browser preview. | Separate Medium follow-up; not a blocker for freezing the currently verified photo path. Open until MIME/extension evidence proves the end-to-end format. | Medium. iPhone source format assumptions can hide preview/conversion failures. |

---

## 6. Low Issues

| ID | Problem | Customer Impact | Root Cause | Fix | Verification Status | Regression Risk |
|----|---------|-----------------|------------|-----|---------------------|-----------------|
| L1 | Photos defer wording differs from Story/Basics. | Minor wording inconsistency may confuse careful reviewers. | Photos uses hub escape wording while text pages use postpone wording. | Keep if intentional; unify later if Founder/customer notices confusion. | Accepted for first pilot. | Low. |
| L2 | Entry and Task Home share nav title `事故资料`. | Customer may not distinguish opening/loading page from hub. | Both pages use same nav title while card title distinguishes hub. | Optional Entry title polish after higher-priority items clear. | Accepted. | Low. |

---

## 7. Regression Watchlist

### Founder iPhone Verification — 2026-07-14

- Real iPhone WeChat Preview tested successfully.
- Photo add-more behavior: PASS.
- Photos page first render: PASS; no white-screen observed.
- Full-page loading closure: PASS; no indefinite full-page loading observed.
- Observed upload experience: approximately 2-3 seconds; not a precise measurement.
- Broker photo visibility: PASS; Broker Workbench displayed the new photo.
- Duplicate attachment observation: no duplicate attachment was observed.
- HEIC / HEIF status: open separately as M8. Do not assume HEIC from iPhone source alone because WeChat may produce JPEG temporary/compressed files.

These areas require repeat checks whenever touched:

- Photo upload slot state: empty, local preview, uploading, uploaded, failed, retry.
- Upload success after retry.
- Duplicate upload guard during rapid taps.
- Server read-back after upload/save/submit.
- Post-submit supplement save and timeline append.
- Review missing item route mapping.
- Task Home submitted primary/secondary action count.
- Workbench attachment and vehicle field visibility.
- Expired token and network error behavior.
- Real-device HEIC / HEIF MIME, extension, conversion, upload, and preview.

---

## 8. Update Rules

When a future sprint touches a ledger issue:

1. Update the issue row in this file.
2. Preserve the original problem statement unless it was wrong.
3. Change `Verification Status` only with evidence: automated test, DevTools manual check, phone QA, or Workbench browser verification.
4. Add new issues rather than burying them in evidence docs.
5. Do not mark a customer-facing issue PASS from automation alone when the issue depends on WeChat DevTools or real-device behavior.
