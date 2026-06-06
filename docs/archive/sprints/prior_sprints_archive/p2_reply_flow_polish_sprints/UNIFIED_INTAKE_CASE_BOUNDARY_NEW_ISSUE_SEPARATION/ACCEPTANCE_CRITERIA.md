# Acceptance Criteria

1. **Append API** produces `case_boundary` when rules fire; omits it for clear same-case continuations.
2. **new_issue** appends always include broker prefix `Case boundary: possible new issue…` and ZH/EN continuity copy as spec’d.
3. **borderline** sets `human_confirmation_required` and `case_topic_boundary`, and broker prefix `Case boundary unclear…`.
4. **Persistence:** follow-up save stores `case_boundary` on the case JSON when present.
5. **UI:** workbench shows volcano/gold tags for new_issue/borderline when viewing a case.
6. **Regression:** `LLM_GENERATION_ENABLED=0` full guardrail passes, including new case boundary battery (18/18).
7. **No change** to `WORKFLOW_STATE_KEYS` contract (optional fields only).
