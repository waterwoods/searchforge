# P20 Bug Record Template — Mini Program DevTools QA

**Sprint:** P4a — DevTools QA Gate Preparation  
**Use with:** [`p20_devtools_walkthrough_checklist.md`](./p20_devtools_walkthrough_checklist.md)  
**Rule:** One row per bug. Do not mark checklist PASS for a step that has an open Critical/High bug.

---

## How to use

1. Run the walkthrough checklist in WeChat DevTools.
2. On FAIL, add a new row below (copy blank row from **Template**).
3. Fill every column. Attach or link a screenshot path/filename.
4. Set **Severity** to exactly one of: Critical / High / Medium / Low.
5. Set **Status** to one of: Open / Investigating / Fixed / Won’t fix / Duplicate.
6. Mirror confirmed Critical/High into [`p20_pilot_blockers.md`](./p20_pilot_blockers.md).

**ID scheme:** `P4A-###` (sequential starting at `P4A-001`).

**Page values:** Entry | Task Home | Story | Basics | Photos | Review | Receipt | Error | Cross-page | DevTools Env

---

## Severity guide

| Severity | Meaning |
|----------|---------|
| **Critical** | Blocks complete journey or pilot dry-run (crash, cannot open task, cannot submit, data loss, blank hang) |
| **High** | Major recovery/trust break (wrong contact behavior, expired link loops, resume to wrong page, HTTPS/device block for intended pilot) |
| **Medium** | Journey works with workaround (awkward copy, missing healthy-hub contact, flaky toast timing) |
| **Low** | Polish only (title nuance, defer wording variance, cosmetic) |

---

## Template (copy for each bug)

| Column | Value |
|--------|-------|
| **ID** | P4A-___ |
| **Page** | |
| **Description** | |
| **Screenshot** | (path or filename) |
| **Severity** | Critical / High / Medium / Low |
| **Critical** | □ (mark exactly one severity column) |
| **High** | □ |
| **Medium** | □ |
| **Low** | □ |
| **Repro Steps** | 1. … 2. … 3. … |
| **Expected** | |
| **Actual** | |
| **Owner** | |
| **Status** | Open |

**Severity rule:** Fill **Severity** with the label, and mark exactly one of the checkbox columns (**Critical** / **High** / **Medium** / **Low**) with `☑`. Leave the other three as `□`.

---

## Bug log

| ID | Page | Description | Screenshot | Severity | Critical | High | Medium | Low | Repro Steps | Expected | Actual | Owner | Status |
|----|------|-------------|------------|----------|----------|------|--------|-----|-------------|----------|--------|-------|--------|
| | | | | | □ | □ | □ | □ | | | | | |

*(Add rows below.)*

---

## Blank rows (ready to fill)

| ID | Page | Description | Screenshot | Severity | Critical | High | Medium | Low | Repro Steps | Expected | Actual | Owner | Status |
|----|------|-------------|------------|----------|----------|------|--------|-----|-------------|----------|--------|-------|--------|
| P4A-001 | | | | | □ | □ | □ | □ | | | | | |
| P4A-002 | | | | | □ | □ | □ | □ | | | | | |
| P4A-003 | | | | | □ | □ | □ | □ | | | | | |
| P4A-004 | | | | | □ | □ | □ | □ | | | | | |
| P4A-005 | | | | | □ | □ | □ | □ | | | | | |
| P4A-006 | | | | | □ | □ | □ | □ | | | | | |
| P4A-007 | | | | | □ | □ | □ | □ | | | | | |
| P4A-008 | | | | | □ | □ | □ | □ | | | | | |
| P4A-009 | | | | | □ | □ | □ | □ | | | | | |
| P4A-010 | | | | | □ | □ | □ | □ | | | | | |

---

## Example (do not treat as live bug)

| ID | Page | Description | Screenshot | Severity | Critical | High | Medium | Low | Repro Steps | Expected | Actual | Owner | Status |
|----|------|-------------|------------|----------|----------|------|--------|-----|-------------|----------|--------|-------|--------|
| P4A-EX | Review | Example only — submit with missing story still enabled | `shots/ex-review.png` | High | □ | ☑ | □ | □ | 1. Open Review with empty story 2. Tap 提交给陈总审核 | CTA disabled with reason | CTA enabled and errors after tap | QA | Duplicate |
