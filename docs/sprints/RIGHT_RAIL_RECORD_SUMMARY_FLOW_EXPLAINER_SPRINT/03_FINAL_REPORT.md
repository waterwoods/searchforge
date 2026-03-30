# RIGHT RAIL RECORD SUMMARY + FLOW EXPLAINER — Final report

## What was implemented

- New **`AddCarRecordSummaryRail`** (+ **`AddCarHandoffGroupedSnapshot`**) in `ui/src/components/intake/`, with **`addCarRecordRailLabels.ts`** for grouping and labels.
- **Customer Entry** (pre-handoff Add-Car): progress card now embeds flow explanation (`AddCarFlowExplanation`) plus the rail (steps, why-here, grouped received/missing, correction/new-field banner, next owner, dual-path hints).
- **Post-handoff** Add-Car closure card: quote-ready row kept; flat tag lists replaced by **grouped snapshot** + same correction/update logic where applicable.
- **Scenario replay** right column: reuses rail + keeps case id, collection_stage chip, and `broker_next_step` line above the rail for office-facing clarity.
- **`clientConfig.ts`**: defaults for `record_rail_*` section titles and correction/append copy.

## What remains partial

- **Field-level diffs** (e.g. “年份 2023 → 2024”) are **not** emitted by API; UI only shows correction **class** and **newly appearing** structured field ids.
- **Non–Add-Car** intake still uses the **legacy** flat tag layout in the generic progress card (intentional scope boundary).
- **Office workbench** detail column was not refactored in this sprint (still useful follow-up for parity).

## Blocked by backend / state quality

- Richer “what changed” without inferring from free text requires **explicit change events** or normalized before/after values in triage output.

## Recommended next sprint

- **Workbench record panel parity**: same grouped rail on opened case detail for broker scan.
- **Optional**: API `field_updates[]` for honest correction lines (year, pickup, driver, materials).
