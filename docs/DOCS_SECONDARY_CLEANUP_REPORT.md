# Docs Secondary Cleanup + Root Noise Reduction Report

**Sprint:** Docs Secondary Cleanup + Root Noise Reduction  
**Date:** 2026-03-07  
**Scope:** California Auto Insurance Broker Assistant only

---

## 1. Root-level docs inspected

**Types of docs causing the most confusion:**

| Type | Count (before) | Examples | Issue |
|------|----------------|----------|-------|
| **PROMPT*** | 11 | PROMPT1_PATCH_SUMMARY, PROMPT3_ACCEPTANCE_CHECKLIST, PROMPT5_TRANSLATION_PLAN | Look like primary; actually translation/pipeline working docs |
| **OPERATOR*** | 4 | OPERATOR_PROMPT4, OPERATOR_STEP5A_QUALITY_GATE, OPERATOR_STEP5B_* | Operator guides for automation; not broker daily use |
| **STEP*** | 14 | STEP3_*, STEP4_DAILY_AUTOMATION, STEP5A*, STEP5B* | Step-specific reports, fix summaries; historical |
| **CHECKLIST/CURSOR** | 2 | CHECKLIST_PROMPT1, CURSOR_PROMPT_STEP5B_REVIEW | One-off checklists and reviews |
| **Duplicate** | 1 | BROKER_VALUE_VALIDATION_MEETING_PACK (root) | Identical to runbooks/ copy |

**Total moved/removed:** 31 files (30 to supporting/, 1 duplicate removed)

---

## 2. Changes made

| Change | Files | Why |
|--------|------|-----|
| **Created** | `docs/supporting/` | New folder for secondary/working docs |
| **Moved** | PROMPT1–5_*, OPERATOR_*, STEP3–5*, CHECKLIST_PROMPT1, CURSOR_PROMPT_STEP5B_REVIEW | Reduce root noise; make primary vs secondary obvious |
| **Created** | `docs/supporting/INDEX.md` | Explains purpose; lists contents by type |
| **Updated** | `docs/PROJECT_DOC_SYSTEM_MAP.md` | Added supporting/ to Doc Categories and Index Files |
| **Updated** | `docs/BROKER_REPORTS_INDEX.md` | Added this report to Current |
| **Updated** | `docs/DEMO_SCRIPT.md`, `ui/README.md` | Fixed links to moved PROMPT docs |
| **Updated** | Internal refs in supporting/ | docs/XXX → docs/supporting/XXX for cross-refs |
| **Updated** | `docs/ANDY_2MIN_BEFORE_DEMO.md`, `BROKER_DEMO_OPERATOR_RUNBOOK.md`, `broker_value_feedback_form.md`, `BROKER_MEETING_PACKAGE.md` | BROKER_VALUE_VALIDATION_MEETING_PACK → runbooks/ path |
| **Removed** | `docs/BROKER_VALUE_VALIDATION_MEETING_PACK.md` | Duplicate of runbooks/ copy; all refs updated |
| **Updated** | `docs/supporting/STEP4_DAILY_AUTOMATION.md` | OPENCLAW refs → archive/ paths |

---

## 3. Secondary/supporting docs boundary

**What is now considered secondary/supporting:**

| Location | Contents |
|---------|----------|
| `docs/supporting/` | PROMPT*, OPERATOR*, STEP*, CHECKLIST_PROMPT1, CURSOR_PROMPT_STEP5B_REVIEW |

**Purpose:** Translation/pipeline prompt summaries, operator guides, step-specific reports. **Not** source of truth for broker demo. Use goals/, standards/, runbooks/, guardrails/ for current procedures.

**Discoverability:** `docs/supporting/INDEX.md` lists all; `docs/PROJECT_DOC_SYSTEM_MAP.md` includes supporting/ in Doc Categories.

---

## 4. Deletion candidates

**Do NOT delete yet.** Mark as candidates for future review:

| Doc | Why candidate |
|-----|---------------|
| `docs/langsmith_implementation_summary.md` | Possible duplicate of LANGSMITH_IMPLEMENTATION_SUMMARY.md (case); unreferenced |
| `docs/DEMO_FOR_CHENKUI_ACCEPTANCE.md` | One-off acceptance doc; could move to archive if superseded |
| `docs/INDEX.md` | AutoTuner index; out of scope for broker; creates root noise |
| `docs/QUICKSTART.md` | AutoTuner quick start; out of scope for broker |

**Out of scope (not broker):** AutoTuner_*, jobhunter_*, vitals_*, ops_*, k8s_*, langsmith_*, crowdstrike_*, etc. — left as-is per sprint rules.

---

## 5. Clarity result

| Aspect | Before | After |
|--------|--------|-------|
| Root .md count | ~106 | ~76 |
| PROMPT/OPERATOR/STEP at root | 31 | 0 |
| Primary vs secondary | Mixed | PRIMARY in map; supporting/ holds secondary |
| BROKER_VALUE_VALIDATION_MEETING_PACK | Duplicate at root | Single canonical in runbooks/ |

**Result:** Better. A human or agent can now:
- See PRIMARY table in PROJECT_DOC_SYSTEM_MAP
- Find secondary docs in docs/supporting/ with clear INDEX
- Avoid confusion from PROMPT*/OPERATOR*/STEP* at root

---

## 6. Remaining confusion

- **Out-of-scope docs** — AutoTuner, JobHunter, vitals, ops, k8s, langsmith, etc. still at root. Low priority; not touched this sprint.
- **Multiple meeting/demo docs** — BROKER_MEETING_PACKAGE, BROKER_DEMO_OPERATOR_RUNBOOK, BROKER_DEMO_SCRIPT_15MIN, BROKER_DEMO_CHECKLIST overlap. Map says runbooks/BROKER_VALUE_VALIDATION_MEETING_PACK is primary; others are lighter. Could consolidate in future.
- **docs/standards vs docs/ root** — PROJECT_DOC_SYSTEM_MAP "Primary for Daily Use" says docs/standards/BROKER_DEMO_QUALITY_STANDARD.md but standards/INDEX links to ../ (root). Minor path inconsistency.

---

## 7. Recommended next step

**One clear next step:** Before the next broker demo, run `bash scripts/demo_pre_checklist.sh` and open `docs/ANDY_2MIN_BEFORE_DEMO.md`. Verify the doc path feels clear and that agents/humans can find primary vs supporting without scanning PROMPT/OPERATOR/STEP noise.

---

*End of report*
