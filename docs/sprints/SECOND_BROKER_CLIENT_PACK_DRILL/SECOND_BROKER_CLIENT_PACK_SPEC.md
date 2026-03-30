# Second Broker Persona / Client Pack Spec

## Identity

| Field | Value |
|-------|--------|
| **client_id** | `socal_precision` |
| **Display (fictional)** | 南加精算车险服务台 — “SoCal Precision Auto Desk” |
| **Market** | Chinese-speaking customers, California personal auto |
| **Tone** | Short, professional; emphasizes **营业日** queueing; avoids overly chatty warmth |

## Config surfaces (all under `configs/clients/socal_precision/`)

| File | Role |
|------|------|
| `ui_copy.json` | App title, office labels, Add-Car closure / timing strings, quick-start button labels and starter messages, “submit new issue” hints |
| `handoff_phrases.json` | `customer_requested_human`, `add_car`, `remove_car`, `other*`, etc. — ZH/EN lines at handoff |
| `reply_overrides.json` | Shallow merge over `configs/industries/insurance/reply_templates.json` for keys present (e.g. `add_car`, `missing_document`) |

## How this differs from Chen Kui (same structure, different words)

- **Office noun:** 本所 / 本事务所 vs 办公室 / 陈奎办公室.
- **Timing:** Explicit “一至两个**营业日**” and holiday deferral vs warmer “尽快”.
- **Quick start:** “加车**核价**” vs “获取报价”; talk-to-agent starter names the fictional desk.
- **Closure card copy:** Shorter panels and more “queue / 记录” language.

## What is intentionally *not* different

- Intent taxonomy, add-car field extraction, handoff readiness rules, industry markers (except shared `转接人工`), `add_car_rules.json` (still **industry**-level).

## UI wiring (existing product behavior)

- `?client=socal_precision` → `ClientConfigProvider` fetches `/api/inbox/client-config?client=...` and `triageMessage(..., clientId)` passes `client_id` to the API.
