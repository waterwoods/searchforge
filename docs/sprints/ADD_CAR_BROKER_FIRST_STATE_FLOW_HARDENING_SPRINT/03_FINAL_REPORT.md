# ADD-CAR BROKER-FIRST STATE + FLOW HARDENING — Final report

## What changed

- **Customer (pre-handoff, Add-Car):** Introduced `preHandoffProgressCard` and render it **before** `threadBlock` when `addCarActiveHere`; generic intake unchanged (progress still below thread).
- **Customer (post-handoff):** Moved **服务记录编号** block to immediately follow status strip(s), before result eyebrow/headline.
- **Office queue (Add-Car):** Duplicate **服务记录编号** line placed under `AddCarCaseStatusStrip`; hidden in the old position for Add-Car only (non–Add-Car unchanged).
- **Status strip:** Caption typography **11px → 12px**, **fontWeight 700** (both Add-Car strip and generic strip for consistency).
- **Defaults:** `DEFAULT_UI_COPY.add_car_result_card_eyebrow_hint` updated to describe **编号 under status strip** and workbench alignment.

## What improved

- **STATE / record-first scanning** on the flagship path without new components.
- **FLOW:** Progress and “who acts next” surface **before** chat bubbles for Add-Car.
- **Workbench parity:** Queue row top reads **state → same record ID** as customer closure.

## What remains

- **FLOW** still fundamentally chat-backed; this sprint only **re-orders** surfaces.
- **HANDOFF** engine reply length/tone and `already_sent` edge behavior untouched.
- **STATE** backend population gaps on rare paths still possible (scorecard note).

## Estimated score movement (conservative)

| Dimension | Before | After | Note |
|-----------|--------|-------|------|
| **STATE** | 3 / 5 | **3.25 / 5** | Clearer scan order + workbench ID alignment; not a data-model fix. |
| **FLOW** | 3 / 5 | **3.25 / 5** | Add-Car pre-handoff feels more “task-first”; chat metaphor still present. |

## Recommendation for next move

Bias to **pilot validation** and/or **handoff reply polish** per scorecard; further **STATE** gains likely need **engine consistency** or **operator dry-runs**, not more layout tweaks.
