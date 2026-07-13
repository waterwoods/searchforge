# P20 Evidence — Pilot UX Consolidation + Vehicle Visibility Gate

**Date:** 2026-07-13  
**Scope:** Sprint P4c bounded slice:
- A) submitted customer action simplification
- B) broker vehicle visibility end-to-end verification
- C) Mini Program component three-gate policy + automation

---

## 1) Customer actions (before/after)

### Before (submitted state)

Observed overlapping actions across Task Home / Receipt:
- `继续补充资料`
- `补充或修改资料`
- `继续补充照片`
- `查看全部资料` / `查看提交结果`

Result: repetitive CTA surface and unclear primary path.

### After (submitted state)

Unified CTA model:
- **Primary (one only):** `补充或修改资料`
- **Secondary (one only):**
  - Task Home: `查看提交结果`
  - Receipt: `查看全部资料`

Unified supplement action sheet (Task Home + Receipt wording aligned):
- `修改事故经过` -> `/pages/story/story`
- `修改基本资料` -> `/pages/basics/basics`
- `修改车辆及对方信息` -> `/pages/basics/basics`
- `补充照片` -> `/pages/photos/photos`

Guardrails preserved:
- one-time formal submit unchanged
- no second submit entry added
- post-submit supplement provenance/timeline behavior unchanged

---

## 2) Real vehicle path verification (current code path)

Checked path:

Customer Mini Program  
-> PATCH payload  
-> `known_facts` / `h5_intake_state`  
-> Cloud SQL/read-facade parity  
-> Broker API payload  
-> Workbench component props  
-> detail panel rendering

### Field mapping

- `own_vehicle_info`
- `other_party_plate`
- `other_party_info`

### Findings

1. **Does current test case contain these fields?**  
   **YES** (`vehicle_other_party` PATCH in focused tests includes all three)

2. **Does Cloud SQL/read-facade reload preserve them?**  
   **YES** (PG parity assertions in `test_p20_track_b_backend_foundation.py`)

3. **Does Broker API return them?**  
   **YES** (single-case API assertion added in `test_h5_claim_intake_form.py`)

4. **Is `ClaimCaseBriefPanel` mounted in live detail path?**  
   **YES in code** — mounted in `BrokerWorkbenchTab` when `service_lane === 'claim'`.

5. **Hidden/collapsed/wrong object/mismatched keys?**  
   Root issue was visibility/layout clarity, not persistence key mismatch.

6. **Filtered as unknown/empty?**  
   Empty values now explicitly render as `暂未提供` (no inference).

7. **Above fold vs buried?**  
   Added compact explicit section `车辆与对方` in claim brief panel to keep fields scannable.

---

## 3) Root cause of missing broker display

Backend projection already carried vehicle fields in `claim_case_brief.key_facts`, but broker detail presentation was not explicit enough for 10-second scan reliability.  
Fix: explicit `车辆与对方` section + stable placeholder `暂未提供`.

---

## 4) Three-gate QA/release rule

Added permanent gate policy:

- **Gate 1 (completeness):** component dir must have `index.ts/json/wxml/wxss`, and `index.json` has `"component": true`.
- **Gate 2 (path validation):** validate `usingComponents` existence + casing + required files + untracked component risk reporting.
- **Gate 3 (real compile):** manual WeChat DevTools full compile required; no `component not found` / `module ... is not defined`.

Automation added:
- `scripts/validate_miniapp_component_gates.mjs`
- `miniapp/package.json` script: `npm run test:component-gates`

Docs added/updated:
- `docs/qa/p20_experience_version_release_checklist.md` (new)
- `docs/qa/p20_devtools_walkthrough_checklist.md` (updated with G1/G2/G3 rows)
- `docs/qa/p20_pilot_blockers.md` (updated with H9)

---

## 5) Manual status (pending by design)

Not auto-marked PASS:
- Customer DevTools submitted-state CTA consolidation and no-duplicate checks
- Broker browser visual verification for 我方车辆/对方车牌/对方信息 on real case
- DevTools compile Gate 3

---

## 6) Tests

Run in this slice:

1. `cd /home/andy/searchforge/miniapp && npm test`
2. `cd /home/andy/searchforge/miniapp && npm run test:component-gates`
3. `cd /home/andy/searchforge && PYTHONPATH=. python3 -m pytest tests/test_p20_track_b_backend_foundation.py -q`
4. `cd /home/andy/searchforge && PYTHONPATH=. python3 -m pytest tests/test_p19m1_mini_program_logic.py -q`
5. `cd /home/andy/searchforge && PYTHONPATH=. python3 -m pytest tests/test_h5_claim_intake_form.py -q`

---

## 7) Remaining pilot blockers (summary)

Still open:
- C1 manual walkthrough not signed
- C2 HTTPS + 合法域名 real-device path
- H1 healthy hub always-visible contact entry
- H2/H3/H4 experience freeze, device path, operator script
- H9 manual execution/sign-off of new component gate flow

Updated pilot readiness score is maintained in `docs/qa/p20_pilot_blockers.md`.
