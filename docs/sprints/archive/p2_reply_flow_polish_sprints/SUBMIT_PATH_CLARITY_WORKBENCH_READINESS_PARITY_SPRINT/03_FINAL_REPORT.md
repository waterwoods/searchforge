# SUBMIT PATH CLARITY + WORKBENCH READINESS PARITY — Final report

## Implemented

- **Customer CTA:** `lifecycle_status === 'handoff_pending'` on Add-Car now drives **「正式提交办公室」** (configurable via `portal_submit_handoff_pending`) instead of reusing **「提交补充」**; right-rail `submitLabel` matches.
- **Flow explainer:** `AddCarFlowExplanation` gains a **`handoffPending`** branch (amber card) with copy that contrasts **正式提交办公室** vs **继续补充**.
- **Inline alert:** Warning `Alert` above the input when `handoff_pending`, plus dedicated placeholder (`portal_input_placeholder_handoff_pending`).
- **Workbench mirror:** `getOfficeAddCarReadinessMirror()` renders a titled panel under the Add-Car status strip—states: 待客户正式提交 / 已报送 · 可接手处理 / 信息收集中 (+ missing fields appended in code).
- **Queue:** `getQueueReadinessLabel` returns **待客户提交** (gold) for Add-Car + `handoff_pending`.
- **Copy pack:** `configs/clients/chen_kui/ui_copy.json` + `DEFAULT_UI_COPY` extended with all new keys; `record_rail_completion_hint_handoff_pending` aligned with the new CTA name.

## Partial / depends on triage

- **Readiness accuracy** still depends on the engine emitting correct `lifecycle_status`, `collection_stage`, and `still_needed_fields`. UI only mirrors what the API returns.
- **Browser UX** of a live `handoff_pending` turn was not exercised in this session (build + guardrail only).

## Recommended next sprint

- **Operational closure:** optional toast/activity when customer completes **正式提交办公室** from the office queue perspective, or a clearer “customer submitted at” timestamp if/when persisted.
- **Triage quality:** tighten when `handoff_pending` is set vs `collecting` to reduce customer confusion if the model flaps between states.
