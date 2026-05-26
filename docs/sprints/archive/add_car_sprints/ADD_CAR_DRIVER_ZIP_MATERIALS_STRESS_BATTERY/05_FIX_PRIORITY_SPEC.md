# Fix Priority Spec

Use this to route findings from the stress battery into engineering work.

## P0 — Fix now (trust / safety)

- Any **wrong primary driver** or spouse encoded as self due to substring matching.
- Any **materials question** misclassified as **already_sent** (false “您说发过了”).
- Any **ZIP** false negative on common `邮编` / `zip` / bare digit patterns in this battery.

## P1 — Fix next (broker efficiency)

- **Broker next step** drops make/model when year+model were present (e.g. “Run quote for 2024” only).
- **Customer reply** on quote-ready handoff that **ignores** an explicit “要不要发你…” in the **same** bubble or immediate follow-up.

## P2 — Acceptable / defer

- Generic but correct handoff line when all slots are present and no open question.
- **Name/phone** still missing — expected `still_needed_fields` for this product stage.
- Occasional redundant echo of customer phrase on Turn 1 minimal messages (cosmetic).

## How to verify a fix

1. `PYTHONPATH=. LLM_GENERATION_ENABLED=false python3 scripts/run_add_car_driver_zip_materials_stress_battery.py --json`
2. Re-classify affected scenarios; target **Strong** or **Acceptable** with no P0 regressions.
