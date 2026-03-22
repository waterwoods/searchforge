# Founder Inspection Notes

## What to skim first

1. `FINAL_REPORT.md` — sections 8–10 (confidence + 中文 + copy-paste block).
2. This file — two findings that matter for a broker demo.

## Finding A (trust): spouse phrased as 主要驾驶人是我老婆

Scenario **ADZM-D04** exposed a **substring trap**: the marker `主要驾驶人是我` matches inside `主要驾驶人是我老婆`, so `driver` was True while **additional_drivers** did not fire.

- **Mitigation applied in this sprint:** `主要驾驶人是我老婆` / `主要驾驶人是我老公` were added to the `additional_drivers` marker list in `_extract_add_car_fields`, so `collected_fields` now includes **`additional_drivers_yes`** for that phrasing.
- **Residual nuance:** The list still says `primary_driver` (we have *a* driver context); brokers should read the thread for “who is principal operator” until a richer slot model exists.

## Finding B (polish): quote-ready handoff ignores “要不要发你…”

Scenarios **ADZM-M01**, **ADZM-M02**, and turn 2 of **ADZM-X04**: `follow_up_type` stays **`new_info`** (good — not falsely “already sent”), but the **client reply** is the generic “资料已整理好” line and does **not** answer “要不要发你行驶证/截图”.

- **Why it matters:** Customers notice; broker still gets the case, but trust in “assistant understands me” drops slightly.
- **Fix shape:** Add-car branch: if prospective-send detected, append one short sentence (“可以，发微信就行” / office preference) before handoff.

## What looked solid in this run

- All **ZIP** variants in the battery (including `zip95131` and bare `95131`) landed in **`zip`** collection.
- **要不要…发** cases did **not** flip to `already_sent`.
- **材料发你微信了** / **registration 发你微信了** correctly hit **`already_sent`**, broker line asks to **verify WeChat**.

## Suggested demo narrative

“We stress-tested ZIP, driver wording, and ‘should I send docs’ vs ‘I already sent’ in 18 realistic Chinese messages. ZIP and materials **classification** look solid; we found one **driver phrase** edge case to fix before you rely on structured driver fields without reading the thread.”
