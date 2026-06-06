# Execution Outline — Unified Intake Container Alignment + Left Edge Consistency

## Time box

~20–30 minutes, document-driven, one implementation pass + build verify.

## Loop 1 — Audit

- Read `UnifiedIntakePage.tsx` main return: shell padding, chrome stack, `Tabs`.
- Read `CustomerEntryTab` root wrapper and inner white shell padding.
- Skim `App.tsx` unified-intake route (theme + gray background only; no layout conflict).

**Finding:** Customer tab used a centered 920px column; chrome did not — primary misalignment.

## Loop 2 — Implement

- Customer tab root: `width: 100%`, remove centered max-width and extra horizontal padding.
- Inner customer white shell: horizontal padding `18px` to match title strip.
- Tabs: `tabBarStyle.paddingLeft` from `2` → `0`.
- Remove unused `CUSTOMER_PORTAL_MAX` constant.

## Loop 3 — Verify

- `cd ui && npm run build` — must pass with no new lint issues.

## Deliverables

- This sprint folder (blueprint, spec, outline, acceptance, founder notes, final report).
- Code: `ui/src/pages/UnifiedIntakePage.tsx` only.
