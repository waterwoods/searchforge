# P19H-3h — Add Car H5 Task State Machine

**Date:** 2026-07-10  
**Sprint:** P19H-3h Design  
**Lane:** Add Car (`service_lane: add_car`)  
**Flow token:** `FLOW_ADD_CAR_INTAKE_FORM` (new, Phase 3)  
**Route:** `/task/add-car/:taskToken`  
**Priority:** Phase 3 — after Claim H5 MVP validates task framework

---

## Overview

Add Car reuses the **same H5 Task Trip framework** as Claim with lane-specific steps. Today Add Car has:

- Photo flow via H5 (`add_vehicle_photo_flow`) ✅
- Standalone wizard at `/add-car` ✅
- Phase 2 text fields partially in WeCom chat

**Target:** WeCom Start Card → H5 primary intake (text + photos) → Workbench review — same Spark pattern as Claim.

```text
Start → Vehicle Basic → Driver → Effective Date → Coverage → Documents → Review → Submit → Done
```

---

## Framework reuse (shared with Claim)

| Primitive | Claim | Add Car |
|-----------|-------|---------|
| Token format | `h5t1.*` | Same |
| Token mint | `mint_h5_claim_intake_form_link()` | `mint_h5_add_car_intake_form_link()` |
| Intake APIs | `/intake`, `/fields`, `/submit` | Same endpoints; lane dispatched from token |
| Step wizard UI | `H5StepWizard` component | Shared component, different step config |
| Submit UX | disable + spinner + idempotency | Identical |
| Timeline pattern | `claim_timeline` | Add Car activity timeline (existing) |
| Persistence | `known_facts` on case JSON | Same |
| Workbench | ClaimCaseBriefPanel | Existing Add Car brief / CustomerEntryTab patterns |

**Extract after Claim MVP:** `H5StepWizard`, `useH5TaskIntake`, `h5ClaimIntake.ts` → shared `h5TaskIntake.ts` with lane config.

---

## How Add Car differs from Claim

| Dimension | Claim | Add Car |
|-----------|-------|---------|
| Entry phrase | `我要理赔` | `我要加车` / add-car intent |
| Safety-first step | Injury | None — vehicle identity first |
| Photo slots | Damage / other party / scene | VIN / registration / insurance card |
| Phase machine | `claim_state.py` | `add_vehicle_phase2.py` / add-car policy |
| Collision handling | Collision Resolver | Lane-switch Confirm (Add Car → Claim) |
| Disclaimer | 不代表报案 | 不代表保单已生效 / 不代表报价完成 |
| Broker done | `broker_done` → End Card | Add Car completion ceremony (existing) |
| Urgency flags | Injury yes | Delivery date imminent |

---

## Step 0 — Entry (WeCom)

| Attribute | Value |
|-----------|-------|
| **Trigger** | Customer expresses add-car intent (existing intent routing) |
| **WeCom output** | Add Car Start Card (framed, parallel to Claim Start) |
| **Primary CTA** | `打开加车资料页面` → signed H5 link |
| **Secondary** | Chat supplement for photos/text |

**Single Active Task:** One implicit active Add Car draft per customer. Ordinary supplements append to newest open Add Car case (same policy as Claim P19H-3f-5).

---

## Step 1 — Start (H5 landing)

| Screen goal | Orient; show「加车资料收集」|
| Header | `加车资料收集` |
| Subcopy | 请按步骤填写车辆信息，陈总会人工确认后处理。 |
| Primary button | `开始填写` |
| Resume | Skip to first incomplete step via `/intake` |

---

## Step 2 — Vehicle Basic Info

| Fields | `vehicle_year`, `vehicle_make`, `vehicle_model` (or combined `vehicle_description`); `vin` (optional but encouraged) |
| Validation | Year/make/model required OR single description min 5 chars. VIN: 17 chars if provided |
| known_facts | `vehicle_year`, `vehicle_make`, `vehicle_model`, `vin` |
| Broker impact | Core row identity in Workbench |

**Align with:** `add_car_field_contract.py` existing field names.

---

## Step 3 — Driver Info

| Fields | `primary_driver` (who drives this car); `driver_license_status` (optional: valid / permit / excluded) |
| Validation | `primary_driver` required |
| known_facts | `primary_driver`, related driver fields |
| Broker impact | Underwriting-relevant; highlight if missing |

---

## Step 4 — Effective Date

| Fields | `coverage_effective_date` (date picker) |
| Validation | Required; not more than 90 days future (configurable) |
| known_facts | `coverage_effective_date` |
| Broker impact | Urgency highlight if within 7 days |

---

## Step 5 — Coverage Preference

| Fields | `coverage_preference`: radio `与现有保单相同` / `我需要调整` / `不确定，请陈总建议` |
| Validation | Required |
| Conditional | If「调整」→ optional textarea `coverage_notes` |
| known_facts | `coverage_preference`, `coverage_notes` |
| Broker impact | Drives broker next question |

---

## Step 6 — Upload Documents / Photos

| Fields | Reuse `add_vehicle_photo_flow` slots: `vin_photo`, `registration_photo`, `insurance_card_photo` |
| Validation | At least 1 of 3 required; others soft-required |
| APIs | Existing `POST /upload`, `POST /skip` |
| Timeline | `customer_uploaded_photo` per slot |
| Broker impact | Evidence checklist (mirror Claim pattern) |

---

## Step 7 — Review

| Display | 已填写 / 还缺 / 已上传 |
| Edit links | Back to steps 2–6 |
| Primary button | `提交给陈总确认` (when ready) |

---

## Step 8 — Submit to Broker

| Action | `POST /api/h5/tasks/{token}/submit` |
| Phase | Add Car ready-for-broker state (existing add-car phase helpers) |
| UX | Identical idempotent submit pattern as Claim |
| Timeline | `customer_submitted_intake` |

---

## Step 9 — Done

| Display | `已提交给陈总` |
| Sections | 已收到 · 还缺 · 下一步（陈总确认后会联系您）|
| Disclaimer | 不代表保单已生效或保费已确定 |

---

## WeCom integration

### Start Card copy (draft)

```text
【加车资料收集已开始 ✅】

我是陈总办公室的值班助手。请点击下面页面填写车辆信息（推荐）：
{H5_ADD_CAR_INTAKE_LINK}

您也可以继续在微信发照片或文字，我会一并记录。

说明：此收集用于陈总办公室整理加车资料，不代表保单已生效。
```

### Status Card

Mirror Claim Status Card structure for Add Car lane:
- 状态 / 已收到 / 还缺 / 下一步
- Footer: `继续补充资料：{H5_LINK}`

### Lane switch (Add Car → Claim)

**Unchanged** — existing Confirm Card (`【请确认】`). Customer must confirm before Claim Start Card. Add Car H5 token remains on paused Add Car case.

---

## Workbench reception

| Panel | Content |
|-------|---------|
| Case Summary | Vehicle line, driver, effective date, coverage preference |
| Received | Fields + photo slots with status |
| Missing | From add-car `missing_info` derivation |
| Photos | 3-slot checklist |
| Timeline | H5 step events + WeCom supplements |
| Done | Broker completion action (existing) |

Structured H5 submits eliminate re-parsing chat for Phase 2 fields (`delivery_date`, `zip`, `phone` may migrate from chat to H5 steps in Phase 3).

---

## Avoiding multiple active Add Car confusion

| Policy | Behavior |
|--------|----------|
| Single Active Task per lane | One implicit active Add Car draft; supplements append to newest |
| Strong restart signal | `再加一辆车` / explicit new vehicle → **Confirm Card** (deferred in P19H-3f-5; implement in Phase 3) |
| No customer picker | Never ask「哪辆车？」|
| Multi-open flag | `possible_multi_add_car_context` (mirror Claim risk flag) |
| Broker visibility | Workbench warning when multiple open Add Car cases |

### Confirm Card (Phase 3 — implement with Add Car H5)

```text
【请确认】
您有一份进行中的加车资料。

1. 继续当前加车
2. 开始加另一辆车
3. 联系陈总
```

Choice 2 → new Add Car case + new Start Card + new H5 token.

---

## Exception:「another car」

| Signal strength | Behavior |
|-----------------|----------|
| Weak (photo/text only) | Append to active Add Car |
| Strong (`再加一辆车`, new VIN stated) | Confirm Card — do not silently create or merge |
| Mid-H5 abandon + new Start | New token binds to new case only after Confirm choice 2 |

H5 does not auto-split vehicles. Exception routing stays in WeCom state machine.

---

## Implementation order (Add Car)

1. Claim H5 MVP ships and validates `H5StepWizard` + intake APIs
2. Add `FLOW_ADD_CAR_INTAKE_FORM` token flow constant
3. Port step config from `/add-car` wizard to H5 trip
4. Update Add Car Start Card → H5 link primary CTA
5. Add Car Confirm Card for「another car」
6. Smoke: `p19h3h_deploy_add_car_h5_intake_smoke.py`

**Estimate:** 2–3 days after Claim MVP stable.

---

## Test matrix (design-level)

| Test | Expected |
|------|----------|
| Happy path 9-step | Workbench shows structured Add Car brief |
| Resume token | Lands on correct step |
| Add Car → Claim switch | Confirm Card; no silent lane merge |
| `再加一辆车` | Confirm Card (Phase 3) |
| Dual chat + H5 write | Same `known_facts`; H5 wins on conflict |
| Submit idempotency | One handoff event |

---

*Reuses Add Car field contract from `add_car_field_contract.py`; timeline pattern from existing add-car activity logs.*
