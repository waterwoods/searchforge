# PAGE / FLOW / STATE / HANDOFF — Spec & acceptance

## Current frontend skeleton assessment

| Lens | What worked | What felt weak |
|------|-------------|----------------|
| **PAGE** | White card shell, service tagline, empty-state path chooser, Add-Car ribbon | Full hero + long copy stayed loud after the user started a case |
| **FLOW** | Quick-start grid, hybrid Add-Car fields, thread + progress card | No single “where am I in the transaction?” control |
| **STATE** | Add-Car status strip + progress card | Other intents relied on tags inside bubbles; less “ticket” feel |
| **HANDOFF** | Closure card, same-case append, Add-Car structured summary | `broker_next_step` boxed mainly for Add-Car; case ID only emphasized for Add-Car |

## Target skeleton (practical)

- **PAGE:** Marketing-grade hero on **first visit**; **compact** service header once `turns.length > 0` so the thread and progress dominate.
- **FLOW:** One horizontal **办理进度** track: **开始报送 → 补充与核对 → 提交办公室**, driven by session phase (empty / in progress / handoff ready).
- **STATE:** **Add-Car:** existing strip. **Other:** `GenericIntakeStatusStrip` with category, optional case status, lifecycle/collection/quote-ready chips.
- **HANDOFF:** **Office next step** block whenever `broker_next_step` is non-empty (any intent). **服务记录编号** whenever `lastCaseId` exists.

## Key gaps addressed (this sprint)

1. Competing surfaces after session start → **compact hero**.
2. Ambiguous progression → **`IntakeFlowStepTrack`**.
3. Unequal status treatment → **`GenericIntakeStatusStrip`**.
4. Handoff parity → **broker_next_step** + **case ID** for non–Add-Car.

## Intended improvements

- **PAGE:** Stripe-like reduction of visual weight after first action.
- **FLOW:** Amazon-like explicit current step (3 beats).
- **STATE:** Zendesk-like chips for generic paths.
- **HANDOFF:** Intercom-like “received + owned” via office next step + record id.

## Acceptance criteria

- [x] With an active session, hero is compact; empty state keeps full hero.
- [x] Flow track shows step 1 (empty), 2 (in progress), or 3 (handoff ready).
- [x] Non–Add-Car in-progress shows generic status strip when triage exists.
- [x] Handoff shows `broker_next_step` for generic when present; shows case ID for any persisted case.
- [x] `cd ui && npm run build` passes.

## Minor copy fix

- Customer-facing tag **需办公室核对要点** replaces English “Human confirmation recommended” on system bubbles.
