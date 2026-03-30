# Submitted time + queue scan — Spec

## Current weakness (pre-sprint)

- Customer post-handoff showed **“送达办公室时间”** paired with **`created_at`**, which can misread as “submit instant” and can predate formal handoff.
- Backend does **not** expose a dedicated `submitted_at` event; JSON cases use **`created_at`** / **`updated_at`** only.
- Add-Car queue cards had a strong **status strip** but **timing + phase** were easier to see only after opening the record or reading long preview text.

## Target submitted-time model

| Signal | Meaning |
|--------|---------|
| **Primary (post-handoff)** | **办公室侧最近活动时间（系统更新时间）** → maps to API **`updated_at`** (last write to the service record). |
| **Secondary** | **服务记录首次建立** → **`created_at`** when it differs from `updated_at`. |
| **Truth note** | Short copy: no separate millisecond “click submit” timestamp; append/follow-up bumps `updated_at`. |
| **Office detail `报送与送达`** | Same: after formal submission, **lead with `updated_at`**; footnote **proxy**; optional created line. |

## Target queue-card scan model

For Add-Car rows, a **single scan line** under record id:

- Phase: **已正式送达办公室** | **待客户正式提交** | **信息收集中**
- **最近活动** + `updated_at` (local formatted)

`getCompactQueuePreview` for Add-Car **prefixes** the same phase vocabulary and appends **最近活动** when helpful.

## Acceptance criteria

- [x] No UI claims a precision “submit click” time without backend support.
- [x] Customer closure and office snapshot both explain **updated_at**-first semantics where shown.
- [x] Add-Car queue cards show **phase + recent activity** without opening the case.
- [x] Copy is client-pack overridable (`ui_copy` / `UiCopy` defaults).
