# P20 Daily Task Prompt Template

> Use with `docs/prompts/p20_cursor_master_prompt_2026_07_12.md`. Paste the master prompt first, then fill and append this template. Keep the daily task short and specific.

---

```text
# DAILY TASK — <short title>

## RECOMMENDED MODEL
<category, not a permanent name>
- Architecture/whole-repo → strongest long-context model, high thinking
- Backend/workflow core → strong reasoning + code model
- Implementation (UI kit/pages) → capable coding model
- Tests/bug fixes → fast capable coding model
- Fast simple edits → fast model
(Model availability changes; pick current best in category. Do not use Auto for
architecture-critical work.)

## REPOSITORY / BRANCH
Repository: /home/andy/searchforge
Branch: sprint/p16-trust-layer   (confirm; do not switch without reason)

## TRACK
<A = Mini Program UI | B = Backend Core | C = Integration/Security/Testing>

## MISSION (1–3 sentences)
<what to accomplish today, tied to a P20 skeleton component or risk R1–R12>

## PRODUCT PRINCIPLE REFERENCES
<list the specific P20 Constitution sections/principles this touches,
 e.g. §4.14 provenance guard, §6 Task Contract, §11 tenant boundary>

## ALLOWED FILES (exclusive)
<explicit paths this task may modify — within the Track's ownership>

## PROHIBITED FILES / ACTIONS
<explicit out-of-bounds paths; plus: no schema migration, no deploy,
 no push, no secret commit, no SILENT cross-track edits. If a cross-track
 interface change is genuinely necessary, STOP and report (why / exact files /
 owner coordination / proposed sequence) — proceed only after approval.
 Never edit files another Agent is editing concurrently.>

## INSPECT STEP
- git status --short ; git branch --show-current
- read: <target files + relevant SSOT>
- classify findings (KEEP/HARDEN/EXTRACT/DEFER/BLOCKER)

## IMPLEMENTATION STEP
- smallest durable change; additive contract fields only (no version bump
  without approval)
- respect frozen boundaries (Constitution §21)

## TESTS
- add/extend: <test module>
- keep green: <existing suites, e.g. the 181 focused claim tests>
- evidence: <smoke script / pytest command + expected result>

## STOP GATES
- Frozen boundary change? schema migration? deploy/push? weakened tenant
  isolation? AI made authoritative? unverifiable manual item? → STOP + report.

## DELIVERABLES
<files/artifacts expected; e.g. Task Contract v0 doc, provenance-guard fix +
 test, UI kit behavior + refactored pages>

## ACCEPTANCE CRITERIA
<objective pass conditions; map to a P20 gate where relevant>

## COMMIT POLICY
- Do not commit automatically. Return findings for Founder review.
- Commit only after explicit approval. Do not push unless asked.

## FINAL RESPONSE (return concisely)
1. What changed (summary)
2. Findings classified
3. Tests + evidence
4. Checklist answers (docs/design/p20_design_review_checklist_2026_07_12.md)
5. Code changed: YES/NO
6. Commit created: YES/NO
7. Risks requiring Founder decision
```

---

*Reusable. Append one short daily task at a time; do not repeat the full Constitution.*
