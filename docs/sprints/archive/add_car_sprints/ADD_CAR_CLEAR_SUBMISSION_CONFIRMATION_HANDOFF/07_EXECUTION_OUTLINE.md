# Execution Outline

## Phase A — Control docs

1. Blueprint, specs (customer confirmation, office follow-up, UX options, broker clarity).
2. Founder scenario pack (markdown + JSON).
3. This outline, acceptance criteria, inspection notes.
4. Final sprint report (populated after loops).

## Phase B — Roles (conceptual)

- **Planner:** Blueprint + options doc.
- **UX/copy:** `ui_copy.json`, `handoff_phrases.json`, UI labels.
- **Rule/state:** Validate triage still returns `collected_fields` / `quote_ready_status` at handoff (no logic change required).
- **UI:** Closure card confirmation panel + office banner + submit CTA.
- **QA:** Guardrail + `npm run build` + sprint scenario runner.

## Phase C — Loops

1. **Audit** — Baseline weaknesses documented.
2. **Design** — Options A/B/C; choose B.
3. **Implement** — Config + UI + config_loader whitelist.
4. **Test** — Guardrail, build, sprint scenarios.
5. **Optional loop 4** — Only if a single obvious low-risk tweak remains (deferred: none identified post-test).

## Files touched (expected)

- `configs/clients/chen_kui/ui_copy.json`
- `configs/clients/chen_kui/handoff_phrases.json`
- `services/fiqa_api/inbox_triage/config_loader.py`
- `ui/src/api/clientConfig.ts`
- `ui/src/pages/UnifiedIntakePage.tsx`
- `docs/sprints/ADD_CAR_CLEAR_SUBMISSION_CONFIRMATION_HANDOFF/*`
- `scripts/run_add_car_submission_confirmation_sprint_scenarios.py`
