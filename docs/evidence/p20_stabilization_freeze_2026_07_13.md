# P20 Stabilization & Freeze — 2026-07-13

**Mission:** One clean, reviewable stabilization point for Mini Program, QA, supplement, and Workbench changes.  
**Branch:** `sprint/p16-trust-layer`  
**Type:** Review / cleanup / commit only — no new product features.

---

## 1) Committed scope

### Mini Program — A2b / A2c / A2d-e + Polish P1–P4c

- New components: `task-choice`, `task-photo`, `task-progress`, `task-status-card`
- Page migrations / polish: `entry`, `error`, `basics`, `photos`, `review`, `receipt`, `task-home`, `story`
- Shared: `behaviors/taskPage.ts`, `utils/resolveTaskViewModel.ts`, `utils/taskMapping.ts`, `utils/resumeHint.ts`, `utils/request.ts`, `services/taskApi.ts`
- Component gate validator: `scripts/validate_miniapp_component_gates.mjs` + `npm run test:component-gates`
- Focused miniapp tests (page + component + supplement routing)

### Backend — post-submit customer supplement hotfix

- `services/fiqa_api/inbox_triage/h5_task_intake.py` — allowlisted post-submit field PATCH + provenance/timeline

### Workbench — vehicle-info rendering (code only)

- `ui/src/features/intake/components/ClaimCaseBriefPanel.tsx` — `车辆与对方`
- `ui/src/features/intake/components/BrokerWorkbenchTab.tsx` + `ui/src/api/inboxTriage.ts`

### Tests (Python)

- `tests/test_p20_track_b_backend_foundation.py`
- `tests/test_p19m1_mini_program_logic.py`
- `tests/test_h5_claim_intake_form.py`
- (workbench visibility suite exercised; no new product scope)

### QA / evidence

- `docs/qa/p20_devtools_walkthrough_checklist.md`
- `docs/qa/p20_pilot_blockers.md`
- `docs/qa/p20_experience_version_release_checklist.md`
- `docs/qa/p20_bug_record_template.md`
- Track A2b/A2c/A2d-e + Product Polish P1–P3 + post-submit / review / pilot UX evidence
- `docs/design/p20_product_polish_p1.md`
- This file

### Safety

- `.gitignore` — also ignore `miniapp/project.private.config.json`

---

## 2) Explicitly excluded (left unstaged / deferred)

### Local / private

| Path | Reason |
|------|--------|
| `miniapp/config.local.ts` | Local token + API override (gitignored) |
| `miniapp/project.private.config.json` | Private DevTools settings (now gitignored) |
| `miniapp/project.config.json` | Working tree replaces `touristappid` with real AppID `wxa…`; not safe for shared repo — leave local-only |

### Unrelated / defer

- Older P19 smoke JSON under `docs/evidence/p19h3*` / `p19m2*`
- `docs/design/p20_production_skeleton_repository_audit_2026_07_12.md`
- `docs/design/p20_track_a0_experience_benchmark_and_ui_audit_2026_07_12.md`
- `docs/evidence/p20_track_a0_*`, `docs/evidence/p20_track_c_*`
- `docs/p19e3_*`, `docs/p19e_*`, `docs/p19f0_*`, `docs/p19i2_*`, `docs/policy/p19h3g5_*`

Never reset/stash/discarded.

---

## 3) Component three gates

### Gate 1 — File completeness

New components each have `index.ts` / `index.json` / `index.wxml` / `index.wxss` and `"component": true`:

- `task-choice` — PASS
- `task-photo` — PASS
- `task-progress` — PASS
- `task-status-card` — PASS

### Gate 2 — Path / casing / usingComponents

Command: `cd miniapp && npm run test:component-gates`  
Result: **PASS** (`Component gate validation passed.`)  
Pre-commit warning listed untracked new component dirs; resolved by including them in this freeze. Strict mode expected clean after commit.

### Gate 3 — Real WeChat DevTools compile (Founder)

| Check | Status |
|-------|--------|
| Full compile succeeded (this freeze) | **NOT VERIFIED** |
| No `component not found` | **NOT VERIFIED** |
| No `module ... is not defined` | **NOT VERIFIED** |
| Unified「补充或修改资料」visible | **NOT VERIFIED** |

Prior A2a Founder compile evidence exists for Task Home / shell bindings only — **does not** cover A2b–A2d/e components or P4c unified supplement. **Do not fabricate PASS.**

---

## 4) Tests / counts (this freeze run)

| Suite | Result |
|-------|--------|
| `miniapp` `npm test` | **118 PASS** / 0 fail |
| `miniapp` `npm run test:component-gates` | **PASS** |
| `pytest tests/test_p20_track_b_backend_foundation.py -q` | **8 PASS** |
| `pytest tests/test_p19m1_mini_program_logic.py -q` | **23 PASS** |
| `pytest tests/test_h5_claim_intake_form.py -q` | **20 PASS** |
| `pytest tests/test_p19h3a_claim_workbench_visibility.py -q` | **8 PASS** |

---

## 5) Secret / data scan

| Item | Result |
|------|--------|
| `config.local.ts` committed | **NO** (excluded / gitignored) |
| `project.private.config.json` committed | **NO** |
| Real AppID in committed `project.config.json` | **NO** (file left unstaged) |
| Real task tokens in commit | **NO** (tests use mocks only) |
| Private screenshots | **NONE** included |

---

## 6) Vehicle-display blocker (Medium)

| Layer | Status |
|-------|--------|
| Backend persistence | **PASS** (PG parity tests) |
| Broker API projection | **PASS** (H5/API tests) |
| Workbench rendering code | **Implemented** (`车辆与对方`) |
| Real browser visibility | **Manual verification still unclear — Medium blocker (M4)** |

Do **not** redesign in this sprint. Do **not** mark resolved without a real browser case showing the fields.

---

## 7) Remaining Pilot blockers (summary)

**Critical:** C1 manual walkthrough; C2 HTTPS + 合法域名  
**High:** H1 healthy-hub contact; H2 config freeze; H3 real-device path; H4 operator script; H5–H7 fixed-in-code / manual verify; H9 Gate3 unsigned  
**Medium:** M1/M2 manual edges; M3 Basics multi-PATCH; **M4 vehicle browser visibility**  
**Low:** L1–L3 accepted

Full table: `docs/qa/p20_pilot_blockers.md`

---

## 8) Pilot Readiness Score

**Overall: 77 / 100** (stabilization freeze)

See readiness table in `docs/qa/p20_pilot_blockers.md`.

---

## 9) Push / deploy

- Push: **NO**
- Deploy: **NO**

## 10) Next sprint readiness

Code freeze is reviewable. Next: Founder **Gate 3** + HTTPS QA / Experience Version sprint. Experience upload remains blocked until Gate3 is signed.
