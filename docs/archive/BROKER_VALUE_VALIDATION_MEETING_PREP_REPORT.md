# Broker Value-Validation Meeting Prep Report

**Sprint**: Broker Value-Validation Meeting Prep Sprint  
**Date**: 2026-03-06  
**Duration**: ~25 min

---

## 1. Issue targeted

**Primary gap**: No success criteria or next-step decision logic. Andy could run the demo but had no clear rubric for "value confirmed" vs "value partial" vs "value weak," and no guidance on what to do after the meeting.

**Secondary gap**: Inconsistent documentation — BROKER_DEMO_CHECKLIST said "Questions 4–5 require Live mode; in Offline use only 1–3," contradicting the validated state (all 5 work offline). Multiple docs (8+) required jumping between BROKER_MEETING_PACKAGE, BROKER_DEMO_SCRIPT_15MIN, runbook, fallback script, feedback form, etc.) with no single entry point.

**Why it mattered most**: A value-validation meeting is only useful if Andy knows what "success" looks like and what to do next. Without that, the session risks ending in ambiguity and no clear follow-up.

---

## 2. Changes made

| File | Change |
|------|--------|
| `docs/BROKER_VALUE_VALIDATION_MEETING_PACK.md` | **New.** Single runbook: agenda, question order (5 core + 3 optional long-tail), opening script, fallback transition, closing/feedback questions, success criteria, next-step decision logic, pre-meeting checklist. |
| `docs/BROKER_DEMO_CHECKLIST.md` | Fixed "3 questions" → "5 questions" in Offline mode; clarified all 5 work in Live and Offline. |
| `docs/BROKER_MEETING_PACKAGE.md` | Added pointer to meeting pack as primary runbook; added §6–7 reference for success criteria and next-step logic. |
| `docs/BROKER_DEMO_FALLBACK_SCRIPT.md` | Fixed "3 个推荐问题" → "5 个推荐问题" in banner text; "three questions" → "five questions" in optional say. |
| `docs/broker_value_feedback_form.md` | Added success-rubric link to meeting pack §6–7. |
| `docs/BROKER_DEMO_OPERATOR_RUNBOOK.md` | Added pointer to meeting pack as primary runbook for value-validation. |
| `docs/ANDY_2MIN_BEFORE_DEMO.md` | Updated "Open the demo script" → "Open BROKER_VALUE_VALIDATION_MEETING_PACK.md". |

**Why it helps**: Andy now has one entry point (`BROKER_VALUE_VALIDATION_MEETING_PACK.md`) with everything needed to run the session and decide next steps. Success criteria and decision logic remove post-meeting ambiguity.

---

## 3. Meeting package

| Item | Location |
|------|----------|
| **Recommended agenda** | Meeting pack §1 |
| **Recommended question order** | Meeting pack §2 (5 core + 3 optional long-tail) |
| **Opening script** | Meeting pack §3 |
| **Fallback transition** | Meeting pack §4 |
| **Closing / feedback questions** | Meeting pack §5 |
| **Success criteria** | Meeting pack §6 |
| **Next-step decision logic** | Meeting pack §7 |

**Success criteria (summary):**

- **Saves time**: 明显节省 or 有一点节省 = pass
- **Usable answer**: 可以直接发 or 需要小改 = pass
- **Would use again**: 会经常用 or 偶尔会用 = pass

**Value confirmed** = all 3 pass → propose pilot.  
**Value partial** = 2 of 3 pass → address gaps, second session.  
**Value weak** = 1 or 0 pass → document gaps, no pilot push.

---

## 4. Operator impact

| Before | After |
|--------|-------|
| Jump between 8+ docs | One primary runbook: `BROKER_VALUE_VALIDATION_MEETING_PACK.md` |
| No success rubric | Clear pass/fail per criterion + outcome (confirmed/partial/weak) |
| No post-meeting logic | Decision table: value confirmed → pilot; partial → gaps + second session; weak → document, no push |
| Wrong "3 questions offline" | Correct "5 questions" everywhere |

**New default meeting-prep path:**

1. Run `bash scripts/demo_prep_one_command.sh`
2. Open `docs/BROKER_VALUE_VALIDATION_MEETING_PACK.md`
3. Follow agenda, scripts, feedback questions
4. Apply success criteria and next-step logic
5. Send follow-up (BROKER_FOLLOWUP_MESSAGE.md)

**What Andy no longer needs to manually prepare:** Agenda, question order, opening/closing scripts, fallback transition, feedback question list, success rubric, or next-step logic — all in the pack.

**What Cursor can now handle:** Meeting pack creation, doc consistency (5 vs 3), success criteria, decision logic.

**What OpenClaw can support:** Snapshot refresh (`snapshot_demo_answers.py`), demo validation (`demo_quick_validate.sh`), pre-checklist (`demo_pre_checklist.sh`).

---

## 5. Future extraction note

| Reusable | California/broker-specific |
|----------|----------------------------|
| Meeting pack structure (agenda, scripts, success criteria, decision logic) | CA agencies (DMV, insurance.ca.gov), 15/30/5, $14 fee |
| Success rubric pattern (saves time / usable / would use) | Chinese question wording, WeChat copy |
| Next-step decision logic (confirmed / partial / weak) | Broker scenarios, 陈魁 context |
| Feedback question flow | — |

**Template candidates (later):**

- `docs/broker_value_validation_meeting_pack_TEMPLATE.md` — swap questions, scripts, region
- `docs/vertical_validation_meeting_pack_TEMPLATE.md` — same structure for other verticals
- `configs/regions/ca_auto_insurance.json` — questions, fallbacks, URLs per region

---

## 6. Remaining blocker(s)

- None for running the meeting. If Live fails, Offline works with 5 questions.
- Optional: Add 3 long-tail questions (SR-22, why suspended, collision/comprehensive) to the demo UI as "optional" if not already surfaced — currently in LONGTAIL_MEETING_SUBSET; operator can type them when Live.

---

## 7. Recommended next sprint

**Target**: Feedback capture integration.

**Why**: The feedback form exists but is separate from the meeting flow. A one-page "during meeting" capture sheet (or a simple checklist Andy fills while the broker answers) would reduce post-meeting recall effort and ensure all 5 criteria + top gaps are recorded. Small change: add a printable one-pager derived from the feedback form, keyed to the 5 closing questions, with checkboxes for 明显节省/有一点节省/etc.

---

*End of report*
