# P20 Evidence — Post-Submit Edit Hub + Vehicle-Info Parity

**Date:** 2026-07-13  
**Scope:** Sprint P4 mission for post-submit customer edit clarity and broker vehicle-info parity.

## Root causes

1. **Post-submit edit discoverability gap (customer side):**
   - Submitted customers could still supplement photos, but there was no explicit, always-visible "text correction/supplement" action from submitted surfaces.
   - Task Home and Receipt did not clearly communicate a post-submit "补充或更正" workflow using existing editable pages.

2. **Vehicle display parity gap (broker side):**
   - Backend projection already carried vehicle fields in `claim_case_brief.key_facts`.
   - Broker Workbench detail rendering did not explicitly show those fields, creating a "saved but not visible" perception.

## Customer edit design implemented

Product behavior kept unchanged where required:
- Formal submit remains one-time.
- No second formal submit path introduced.
- Existing PATCH + provenance/timeline semantics are preserved.

UI additions:
- **Task Home (submitted):**
  - Secondary actions show:
    - `补充或修改资料`
    - `继续补充照片`
  - `补充或修改资料` opens action sheet:
    - `事故经过` -> `/pages/story/story`
    - `基本资料` -> `/pages/basics/basics`
    - `车辆及对方信息` -> `/pages/basics/basics`
- **Receipt (submitted):**
  - Primary submitted state copy now presents `已提交，等待陈总查看`.
  - Adds `补充或修改资料` action sheet (same routing as Task Home).
  - Keeps `继续补充照片` as a separate action.

## Exact vehicle field mapping (E2E)

1. **Customer Basics input (Mini Program)**
   - `miniapp/pages/basics/basics.ts` sends:
     - `own_vehicle_info`
     - `other_party_plate`
     - `other_party_info`
   - via `patchTaskFields(token, "vehicle_other_party", fields)`.

2. **PATCH step and persistence (backend)**
   - `services/fiqa_api/inbox_triage/h5_task_intake.py`
     - step `vehicle_other_party` normalization + validation.
     - post-submit allowlist includes:
       - `own_vehicle_info`
       - `other_party_plate`
       - `other_party_info`
     - post-submit writes preserve submitted status and append `h5_post_submit_supplement` timeline entries with before/after metadata.

3. **Read model / Cloud SQL parity**
   - `case_store` + `case_truth_repository` path already hydrates `known_facts`, `known_fact_provenance`, `h5_intake_state`, and timeline data.
   - Added/updated tests confirm `own_vehicle_info` and related vehicle fields survive PG-backed roundtrip and are present after reload.

4. **Broker API projection**
   - `services/fiqa_api/inbox_triage/claim_workbench_display.py` sets in `claim_case_brief.key_facts`:
     - `own_vehicle_info`
     - `other_party_plate`
     - `other_party_info` (formatted using existing display helper behavior).

5. **Workbench UI rendering**
   - `ui/src/features/intake/components/ClaimCaseBriefPanel.tsx` now renders explicit rows:
     - 我方车辆
     - 对方车牌
     - 对方信息
   - Uses `—` when empty/unknown (no silent inference).
   - `ui/src/features/intake/components/BrokerWorkbenchTab.tsx` now mounts `ClaimCaseBriefPanel` in case detail for claim lane, making these fields visible in the operator surface.

## Persistence / API / rendering results

- **Persistence result:** PASS (vehicle fields saved and rehydrated from PG path).
- **Broker API result:** PASS (`claim_case_brief.key_facts` includes vehicle parity fields).
- **Workbench rendering result:** PASS in code (explicit rows added and panel mounted); manual browser verification still required.

## Files changed (this mission)

- `miniapp/pages/task-home/task-home.ts`
- `miniapp/pages/task-home/task-home.wxml`
- `miniapp/pages/receipt/receipt.ts`
- `miniapp/pages/receipt/receipt.wxml`
- `miniapp/tests/taskHomePage.test.ts`
- `miniapp/tests/receiptPage.test.ts`
- `ui/src/api/inboxTriage.ts`
- `ui/src/features/intake/components/ClaimCaseBriefPanel.tsx`
- `ui/src/features/intake/components/BrokerWorkbenchTab.tsx`
- `tests/test_p20_track_b_backend_foundation.py`
- `tests/test_h5_claim_intake_form.py`
- `docs/qa/p20_devtools_walkthrough_checklist.md`
- `docs/qa/p20_pilot_blockers.md`

## Tests run

Executed in this session:

1. `cd /home/andy/searchforge/miniapp && npm test`  
   - Result: PASS (`115 passed, 0 failed`).

2. `cd /home/andy/searchforge && PYTHONPATH=. python3 -m pytest tests/test_p20_track_b_backend_foundation.py -q`  
   - Result: PASS (`8 passed`).

3. `cd /home/andy/searchforge && PYTHONPATH=. python3 -m pytest tests/test_p19m1_mini_program_logic.py -q`  
   - Result: PASS (`23 passed`).

4. Focused data-path regression:
   - `PYTHONPATH=. python3 -m pytest tests/test_h5_claim_intake_form.py -q`
   - Result: PASS (`20 passed`).

Added/updated assertions cover:
- post-submit edit action routing (Task Home + Receipt),
- submitted-state preservation after post-submit supplement,
- no duplicate formal submit behavior (existing guard tests remain),
- PG roundtrip vehicle persistence,
- claim workbench projection including vehicle fields,
- post-submit vehicle correction before/after timeline delta.

## Schema migration decision

- **Schema migration required:** **NO**
- Reason: persistence fields already exist in current model and survive PG read/write parity without schema changes.

## Manual verification required

Still required in DevTools + Workbench UI:
- Submitted Task Home and Receipt show both secondary actions and correct routes.
- Post-submit text correction saves successfully and claim remains submitted.
- Broker Workbench detail visibly shows vehicle parity rows and timeline context for supplements.
- Empty/unknown values render as placeholders, not fabricated values.
