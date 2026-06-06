# Execution Outline

1. **Audit** — Map prospective-send detection vs reply assembly; note echo path and `发你` substring bug in `_get_next_ask_for_add_car`.
2. **Implement** — `_get_prospective_send_materials_lead()`, wire into collecting + handoff + turn-1 draft; extend `_is_prospective_send_offer_message()`; fix `materials_sent` guard; skip echo for prospective in `_get_add_car_acknowledgement`.
3. **Scenarios** — Add ADZM-M05, M06, X05; bump battery description count.
4. **Validate** — Guardrail + three Add-Car runners (rule path, `LLM_GENERATION_ENABLED=false` where applicable).
5. **Report** — Deployment note (backend only), founder copy-paste cases, 中文总结.

## Time budget

Target 30–45 minutes: one implement loop + full validation pass.
