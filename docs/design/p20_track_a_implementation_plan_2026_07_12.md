# P20 Track A — Implementation Plan (Mini Program Task UI Framework)

| Field | Value |
|-------|-------|
| **Status** | A1 IMPLEMENTED — A2/A3 pending. |
| **Date** | 2026-07-12 |
| **Branch** | `sprint/p16-trust-layer` |
| **Authority** | Subordinate to `docs/design/p20_production_constitution_master_design_2026_07_12.md` (§23 Track A) + `docs/design/p20_task_ui_kit_v0_2026_07_12.md`. |
| **Duration** | 3–5 working days (A1–A5). |
| **Concurrency rule** | Track A owns **only** the files below. Multiple Agents must not edit overlapping Mini Program files concurrently. Cross-track changes require STOP + coordination. |

> Enforces non-overlapping file ownership so Track A (UI) and Track B (backend) / Track C (integration) never collide. **A1 is now implemented as a foundation slice**; A2/A3 remain intentionally deferred.

---

## 0. Track A file ownership (exclusive)

**Track A MAY create/modify only:**

```text
miniapp/behaviors/**          (new)
miniapp/components/**          (new)
miniapp/pages/**              (refactor to consume kit; no page deletion)
miniapp/types/task.ts         (extend additively for TaskContract)
miniapp/utils/taskMapping.ts  (evolve: keep as fallback; add contract adapters)
miniapp/app.wxss              (token additions only; no meaning changes)
miniapp/app.json              (register components / usingComponents)
miniapp/package.json          (new — MP test runner)
miniapp/utils/*               (only if a shared util is needed by the kit)
docs/design/p20_track_a*.md, docs/evidence/p20_track_a*.md  (Track A docs)
```

**Track A MUST NOT modify (STOP + report if needed):**

```text
services/**   routes/**   tests/** (backend)   db/**   security/**
services/fiqa_api/**   ui/** (workbench H5)
docs/design/p20_task_contract_v0.md   (Track B owns the contract)
miniapp/project.config.json  miniapp/project.private.config.json  (local DevTools; already dirty — preserve)
```

**Concurrency with B/C:** Track B owns backend `task_contract` emission + section-save endpoint + photo dedup. Track A **consumes** these read-only. If Track A needs a contract field that B hasn't emitted, **STOP and coordinate** — do not invent it server-side.

---

## 1. Slice A1 — Shared foundations

| | |
|-|-|
| **Goal** | `taskPage` behavior + core chrome components + MP test runner. No page behavior change yet. |
| **Model** | Capable coding model (Codex 5.3 Medium / GPT-5.6 Terra Medium / Auto). |
| **Owns** | `miniapp/behaviors/taskPage.ts`, `miniapp/behaviors/analytics.ts`, `miniapp/components/{task-shell,task-header,task-cta,task-secondary,task-loading,task-error}/**`, `miniapp/package.json`, `miniapp/types/task.ts` (TaskContract types, additive). |
| **Forbidden** | Any `services/**`, `routes/**`, backend tests, `pages/**` behavior changes (only wire components in A3). |
| **Depends on** | Nothing (foundation). |
| **STOP gates** | If `taskPage` needs a contract field not in v0 → STOP. If behavior would require a backend change → STOP. |
| **Acceptance** | Components render all states with mock props in DevTools; `taskPage` unit tests green; existing journey untouched. |
| **Tests** | New `miniapp/package.json` node test runner; unit tests for `taskPage` (token guard, load+cached fallback, error mapping, bounded retry, save-and-return, field draft, stale-request drop). |
| **API intensity** | **Low** (mock-driven). |

### A1 execution note (implemented 2026-07-13)

- Delivered in `miniapp/**` only: Task Contract/ViewModel types, `resolveTaskViewModel()`, four base components (`TaskLoading`, `TaskError`, `TaskCTA`, `TaskShell`), `taskPage` behavior, and focused Node-based TypeScript unit tests.
- `resolveTaskViewModel()` is now the contract-first normalization seam for A-series page consumption.
- Contract fallback remains active only for migration safety; retirement criterion is unchanged: once contract parity is validated, legacy client inference ceases to be authoritative.
- No page migration and no backend change were performed in A1.

## 2. Slice A2 — Structured interaction components

| | |
|-|-|
| **Goal** | `TaskStatusCard, TaskProgress, TaskSection, TaskField (incl. native date picker), TaskChoice, TaskPhoto, TaskMissingList, TaskReview, TaskReceipt`. |
| **Model** | Capable coding model. |
| **Owns** | `miniapp/components/{task-status-card,task-progress,task-section,task-field,task-choice,task-photo,task-missing-list,task-review,task-receipt}/**`; may extend `app.wxss` tokens additively. |
| **Forbidden** | Backend, page migration (A3), contract file. |
| **Depends on** | A1 (`taskPage`, `TaskShell/TaskCTA`). |
| **STOP gates** | If a component needs a new `component_type` not in contract v0 → STOP + propose to Track B. No generic form engine. |
| **Acceptance** | Each component renders all states with mock props; `TaskField` date picker works in DevTools; a11y (text labels, ≥88rpx targets) verified. |
| **Tests** | Component-logic unit tests where logic exists (e.g., `TaskPhoto` slot state, `TaskField` validation); DevTools visual check. |
| **API intensity** | **Low**. |

## 3. Slice A3 — Claim page migration

| | |
|-|-|
| **Goal** | Refactor `entry, task-home, story, basics, photos, review, receipt` to consume the behavior + components. Fix 3-PATCH → single-section-save UX, datetime picker, field draft, unified error/retry. No page deletion; DevTools journey unchanged. |
| **Model** | Capable coding model; careful with the full journey. |
| **Owns** | `miniapp/pages/**`, `miniapp/utils/taskMapping.ts` (keep as fallback + add adapters), `miniapp/app.json`. |
| **Forbidden** | Backend, contract file. Do not change the API endpoints (still `/api/h5/tasks/*` until B publishes facade). |
| **Depends on** | A1 + A2. Interim: 3-PATCH wrapped with all-or-nothing UX until B ships single section-save. |
| **STOP gates** | If migration reveals a needed backend behavior change → STOP + report to B. "Does it feel native, not an H5 re-skin?" (Constitution Lock 1). |
| **Acceptance** | Full DevTools journey (Task Home → Story → Basics → Photos → Review → Submit → Receipt → Resume) unchanged in outcome; per-page duplication removed; MP unit tests green. |
| **Tests** | Re-run `test_p19m1_mini_program_logic.py` (backend mirror) unchanged; MP node tests; DevTools 9-step journey. |
| **API intensity** | **Medium** (live journey against local 8001). |

## 4. Slice A4 — Task Contract consumption

| | |
|-|-|
| **Goal** | Render `next_action`/`task_status`/`progress`/`review_ready`/`submit_ready`/`sections`/`evidence_requirements` from `task_contract` when present; keep `taskMapping` inference as fallback. Retire client workflow guessing as authoritative. |
| **Model** | Capable coding model **+ Track B coordination**. |
| **Owns** | `miniapp/behaviors/taskPage.ts`, `miniapp/utils/taskMapping.ts` (contract adapter), affected `components/**`, `types/task.ts`. |
| **Forbidden** | Editing `docs/design/p20_task_contract_v0.md` or any backend emission code (that is Track B). |
| **Depends on** | **Track B emitting `task_contract` additively** from `intake_info_for_token`. If not yet emitted, A4 ships behind a `contract-present?` check (no-op until B lands it). |
| **STOP gates** | If the emitted contract diverges from v0 → STOP + reconcile with B before consuming. Never make the client authoritative. |
| **Acceptance** | With contract present, next-action/status/submit-readiness come from server; client inference no longer decisive; parity test (client fallback vs contract) passes. |
| **Tests** | Contract-render unit tests; parity test comparing legacy inference vs contract for the Claim flow. |
| **API intensity** | **Medium/High** (needs B's contract live). |

## 5. Slice A5 — Acceptance

| | |
|-|-|
| **Goal** | DevTools full journey, real device (when available), family usability test, a11y pass, failure/retry/resume matrix. |
| **Model** | Fast capable model for fixes + **manual human verification** (never auto-PASS). |
| **Owns** | Test/evidence docs under `docs/evidence/p20_track_a*`; small fixes in `miniapp/**`. |
| **Forbidden** | Marking manual/real-device/family items PASS without the real session. |
| **Depends on** | A1–A4. |
| **STOP gates** | Any manual item that cannot be honestly verified → report as pending, not PASS. |
| **Acceptance** | Journey green; family-test findings recorded verbatim (§11.1 of benchmark doc); a11y checklist done; error/retry/resume matrix exercised. |
| **Tests** | DevTools journey; device/LAN preview if feasible; family session notes. |
| **API intensity** | **Medium**. |

---

## 6. Cross-track coordination (bounded, additive — no contract change)

| Need | Owner | Nature | Blocks which A slice |
|------|-------|--------|----------------------|
| Emit `task_contract` additively from intake API | **Track B** | Additive response field | A4 (A1–A3 ship with fallback) |
| Single section-group save (retire 3-PATCH) | **Track B** | Additive endpoint / accept multi-field patch | A3 UX (interim: all-or-nothing wrapper) |
| Photo content-hash dedup (R11) | **Track B** | Backend hardening | A-real-production (kit tolerant now) |
| Analytics event sink | **Track C** | Observability | Post-A (hook stub exists) |
| Workbench auth / tenant scoping (R1/R3) | **Track C/B** | Security | Not Track A |

**Rule:** Track A never edits backend or the contract file. When a cross-track change is required, STOP and report: (a) why, (b) exact files, (c) owner, (d) proposed sequence — proceed only after coordination (Constitution §24.7).

---

## 7. Milestone gate mapping

| Milestone | Track A requirement |
|-----------|---------------------|
| **Family demo** | A1–A3 complete; datetime picker, field draft, unified error/retry; DevTools journey green. Contract consumption (A4) **not required** (fallback ok). |
| **Chen Kui pilot** | A4 contract consumption; single section-save (no partial-save); unified errors. (Plus B/C blockers R1/R2/R6 + 5-test hardening — not Track A.) |
| **WeChat submission** | Real-device pass; identity is Gate C (not Track A code). |
| **Real production** | Photo dedup consumed; per-tenant branding from config (Track B/C); a11y hardened. |

---

## 8. Risks & mitigations

| Risk | Mitigation |
|------|------------|
| Migration (A3) regresses the working journey | Keep pages, migrate incrementally; re-run DevTools 9-step after each page; keep `taskMapping` fallback. |
| Contract not ready when A4 starts | A4 ships behind `contract-present?`; A1–A3 fully functional with inference fallback. |
| 3-PATCH partial-save persists until B ships section-save | Interim all-or-nothing UX + clear partial-failure messaging in `taskPage`. |
| Scope creep (voice/OCR/scan/TDesign) | Out of scope per Constitution §2.6 and benchmark §9/§13; STOP if requested. |
| Concurrent Agents editing `miniapp/pages/**` | Single Agent owns Track A at a time; A2 (components) and A3 (pages) are sequential, not parallel. |

---

*P20 Track A implementation plan — no code changed in this task. File ownership is exclusive; cross-track changes are additive and coordinated. Awaiting Founder approval to begin A1.*
