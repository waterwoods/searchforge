# P26E — Unified Upload State Machine

**Date:** 2026-07-18  
**Mode:** Production Loop (state consistency only — no P26B/P26C)  
**Verdict:** PASS (code + automated gates); Founder device Preview still required for Capability Done

## One objective

Every upload-capable task reuses one production upload lifecycle so Insurance Card and Accident Photos keep identical visible state after upload/reconcile.

## Explicitly out of scope

- P26B Voice Story  
- P26C GEICO Guided Photos  
- UI redesign / new features  
- Slice1 contract changes  
- Broker projection / timeline changes  

## 1. Root Cause

Accident Photos lost visual state **after successful upload** because `photoTaskUiPatch` → `preserveDraftState` cleared `localPath` on every Projection reconcile unless an **error** draft existed:

```ts
// committed behavior (bug)
localPath: keepDraft ? prev?.localPath || "" : ""
```

`keepPendingConfirm` retained `uploadIntentId` / progress, but **not** the thumbnail path. So after read-back/`applyTaskToPhotoState`, the slot showed confirmed copy without preview/badges.

Insurance Card PASS for a different reason: `request-item` restores `local_file_path` from draft and never ran this wipe path.

This was a **client state-consistency** bug, not an upload transport failure.

Secondary hardening: uploads now prefer the customer-selected slot key so guided `current_step` cannot remap the UI slot away from the category being confirmed.

## 2. Architecture Impact

| Before | After |
|--------|--------|
| Insurance Upload State (request-item local) | Shared `uploadStateMachine` |
| Photos Upload State (`preserveDraftState` / ad-hoc status) | Same machine |
| Confirmed invented or wiped by page logic | Projection owns Confirmed; client renders Projection + local transient |

```
Task
  ↓
Unified Upload State Machine
  ↓
Constitution / Projection (SSOT)
  ↓
Local transient (path, progress, transport)
  ↓
Task Card / Slot UI
```

Required lifecycle (exact names):

`Selected → Uploading → Uploaded → Confirmed` (+ `Failed` / Retry)

## 3. Files Changed

### New

- `miniapp/utils/uploadStateMachine.ts` — shared phases, resolve, reconcile merge  
- `miniapp/tests/uploadStateMachine.test.ts`  
- `docs/evidence/p26e_unified_upload_state_preview.html`  
- this evidence file  

### Updated

- `miniapp/pages/photos/photos.ts` — use shared machine; keep session thumbnail after reconcile; prefer selected slot  
- `miniapp/pages/request-item/request-item.ts` — use shared `resolveUploadPhase`  
- `miniapp/components/task-photo/*` — phase badges (from prior P26D polish; still valid)  
- `miniapp/tests/photosPage.test.ts` — assert thumbnail + 已确认 after background reconcile  

No Slice1 write-path, broker projection, or timeline edits in this loop.

## 4. Verification

| Check | Result |
|-------|--------|
| `cd miniapp && npm run build:gate` | **PASS** |
| `uploadStateMachine.test.ts` | **PASS** |
| `photosPage.test.ts` + `slice1RequestItem.test.ts` | **PASS** (58) |
| Insurance Card lifecycle | same machine; draft restore unchanged |
| Photos lifecycle | thumbnail + 已确认 after reconcile |
| Broker Projection / Timeline / Slice1 contract | unchanged by design |

### Golden QA (Founder device still required)

| Surface | Expected | Automated | Device |
|---------|----------|-----------|--------|
| Insurance Card | Selected → Uploading → Uploaded → Confirmed; thumbnail visible | covered via shared machine + request-item wiring | ☐ Founder Preview |
| Accident Photos | same; thumbnail remains after reconcile | **PASS** unit | ☐ Founder Preview |
| Broker Projection | unchanged | n/a (no server write edits) | ☐ |
| Timeline | unchanged | n/a | ☐ |

## 5. Screenshots

Static state board (open in browser):  
`docs/evidence/p26e_unified_upload_state_preview.html`

## 6. Remaining Work

1. **P26B** — Voice Story  
2. **P26C** — GEICO Guided Photos  

**STOP after P26E.** Do not start P26B/P26C in this loop.

## Production Loop worksheet

- **Loop:** 1  
- **One objective:** Unified upload state machine; Photos visual state survives reconcile  
- **Explicitly out of scope:** P26B, P26C, redesign, Slice1 changes  
- **Minimum change:** shared util + photos reconcile fix + request-item wiring  
- **Focused tests:** uploadStateMachine + photosPage + slice1RequestItem + build:gate  
- **Commit authorized:** NO (not requested)  
- **QA deploy authorized:** NO  
- **Founder/manual QA evidence:** device Preview checklist above still open for Capability Done  

### Scorecard

- Reliability: PASS — reconcile no longer wipes session preview  
- Simplicity: PASS — one machine, no parallel Insurance/Photos state models  
- Smoothness: PASS — identical phase ladder on both surfaces  
- Business Value: PASS — Founder Photos FAIL closed at state layer  
- Scope Control: PASS — no P26B/C, no Slice1/broker edits  
