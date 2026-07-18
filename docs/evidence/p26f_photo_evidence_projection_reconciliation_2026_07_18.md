# P26F — Photo Evidence Projection Reconciliation

**Date:** 2026-07-18  
**Mode:** Production Loop (One Truth only — no P26B/P26C)  
**Verdict:** **CONDITIONAL GO** — code + automated gates PASS; requires QA deploy + Founder refresh/re-entry on Camry Case

## One objective

After confirmed Accident Photo uploads, Photos Page, Task Home, Constitution, Broker Projection, and Timeline agree — photos are not left `pending 0/1`.

## Explicitly out of scope

- P26B Voice Story  
- P26C GEICO Guided Photos  
- UI redesign / new features  
- Slice1 write-contract changes  

## 1. Root Cause

Live Golden QA Case (`case_79445c40a4a2`) after Founder uploads:

| Signal | Value |
|--------|--------|
| `photo_count` | **4** |
| `task_contract.evidence_requirements` | vehicle_damage:2, other_vehicle_scene:1, other_evidence:1 |
| Constitution `accident_photos` | **pending · 0/1 · actionable** |
| Customer Today / Why | 先不用操作 / 资料已齐… |

Upload path for `claim_evidence_pack` remapped slots to **gallery categories** (`vehicle_damage`) and persisted those as `slot_assignment` / `claim_attachment_slots` keys.

Constitution / `build_claim_evidence_summary` only counted **canonical** slots (`customer_damage_photo`, …).

Additionally, `_resolve_evidence` preferred a **stale** `claim_evidence_summary` cache on the Case over rebuilding from live attachments — so Task Home never saw the uploads.

Photos Page used `photo_count` (attachments) → looked done. Task Home used Constitution → still pending. **Not a client thumbnail bug** (P26E); a Projection reconciliation bug.

Odd copy `已上传 4/2 张`: optional extras beyond `photoTarget=2` (prototype min). Not duplicate counting. Wording fixed to “已上传 N 张，已满足 M 张要求”.

## 2. Architecture Impact

```
Uploaded attachment (canonical slot + gallery category)
  ↓
claim_attachment_slots / case_attachments
  ↓
build_claim_evidence_summary  (category → canonical)
  ↓
constitution_projection.customer.tasks  (live rebuild when attachments exist)
  ↓
resolveCustomerTaskCards → Task Home
```

- Projection remains SSOT.  
- Client does not infer completion from thumbnails.  
- No parallel photo state model.  
- No Slice1 write-contract change.

## 3. Files Changed

| File | Change |
|------|--------|
| `services/fiqa_api/inbox_triage/claim_workbench_display.py` | `canonical_claim_evidence_slot`; normalize attachment/slot map aliases |
| `services/fiqa_api/inbox_triage/constitution_projection.py` | Rebuild evidence when live photo attachments/slots exist |
| `services/fiqa_api/inbox_triage/h5_task_upload.py` | Persist canonical `slot_assignment`; keep `evidence_category` for gallery |
| `miniapp/pages/photos/photos.ts` / `.wxml` | Progress copy: N 张 / 已满足 M 张要求 |
| `tests/test_constitution_projection_customer_tasks.py` | Live category reconcile + seeded-summary regression |
| this evidence file | |

## 4. Verification

| Check | Result |
|-------|--------|
| `cd miniapp && npm run build:gate` | **PASS** |
| Constitution customer task tests | **PASS** |
| Claim H5 evidence foundation upload (canonical slot) | **PASS** |
| Claim evidence summary backend | **PASS** |
| `photosPage` + `resolveCustomerTaskCards` | **PASS** (46) |
| Local sim of live Founder attachment shape | photos → **completed 2/2**, not actionable |
| Broker next-action / Timeline write path | unchanged by design |
| QA Cloud Run (production API) | **not yet deployed** — Founder phone still hits old projection until deploy |

## 5. Before / After State Truth

### Before (live QA intake)

| Surface | Truth |
|---------|--------|
| Photos Page | Upload complete · 4 photos |
| Task Home · 事故照片 | pending · **0/1** · actionable |
| Constitution Why | 资料已齐… |
| Broker | waiting / review insurance (Slice1) |

### After (fixed projection; post-deploy)

| Surface | Truth |
|---------|--------|
| Photos Page | 已上传 4 张，已满足 2 张要求 |
| Task Home · 事故照片 | **completed** · not pending · not actionable |
| Constitution | same completed photo task |
| Insurance Card | waiting_broker unchanged |
| Refresh / re-entry | same truth (server rebuild) |

## 6. Remaining Work

1. **Deploy** this loop to QA API (required for Founder device truth).  
2. Founder: refresh Task Home / re-enter Camry Case — confirm 事故照片 completed.  
3. **P26B** — Voice Story  
4. **P26C** — GEICO Guided Photos  

**STOP after P26F.** Do not start P26B/P26C here.

## 7. GO / CONDITIONAL GO / NO GO

**CONDITIONAL GO**

- Code + automated One Truth tests: PASS  
- Capability Done blocked on: QA deploy + Founder refresh/re-entry confirmation  

### Scorecard

- Reliability: PASS (live attachments beat stale summary)  
- Simplicity: PASS (canonical slot + one rebuild rule)  
- Smoothness: PASS (Task Home matches Photos)  
- Business Value: PASS (closes Founder pending-photos lie)  
- Scope Control: PASS (no P26B/C, no Slice1 contract change)  
