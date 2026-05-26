# Add-Car Founder Trial + Hybrid Intake Hardening — Final Report

**Date:** 2026-03-20  
**Outcome:** Hybrid intake **Mode C** chosen; **optional structured add-car card** implemented on Customer Entry; backend unchanged.

## Tested

- Baseline Add-Car flow via code review + scenario pack + automated scripts (see main sprint report in chat / `00_SPRINT_REPORT.md`).

## Intake mode chosen

- **Hybrid (C)** — optional short fields + same triage pipeline.

## Improved

- `ui/src/pages/UnifiedIntakePage.tsx`: composed first message + `softRoute: add_car`.

## Remains

- Post-“获取报价” structured assist (fix-next), bilingual composed template, deploy to production hosting.

## Next step

- Founder runs manual scenario pack; redeploy frontend; optional NX items from fix-next spec.
