# State / Workflow Phase 2.5 — Acceptance / Operational Criteria

---

## Operational Criteria

| Criterion | How to Verify |
|-----------|---------------|
| **Session continuity** | session_id in request; conversation_id in response when no case |
| **workflow_state complete** | next_best_question, lifecycle_status in triage result |
| **UI next_best_question** | "下一步建议" visible when collecting |
| **UI lifecycle** | "Collecting" / "Ready to save" in Customer Entry; "Handed off" / "Office follow-up" in case detail |
| **Backend deploy** | Cloud Run URL returns 200 on /healthz |
| **Frontend deploy** | Vercel production URL loads; no CORS errors |
| **Add-car flow** | Turn 1 partial → collecting; Turn 2 complete → handoff_pending |
| **Case persist** | lifecycle_status = handed_off on new case |

---

## Acceptance Gate

- [ ] run_inbox_triage_scenarios: PASS
- [ ] run_multi_turn_simulations: PASS (if exists)
- [ ] audit_state_field_accuracy: PASS
- [ ] verify_speed_routing: OK
- [ ] guardrail_inbox_triage.sh: PASS
- [ ] unified_intake_smoke_check.sh: PASS
- [ ] test_state_workflow_backbone: PASS
- [ ] UI build: success

---

## Founder Inspection Checklist

1. Customer Entry: paste "我买了台宝马X5" → see "下一步建议" when collecting
2. Add zip → see "Ready to save"
3. Persist case → see "Handed off" in Broker Workbench
4. Case detail: lifecycle_status tag visible
5. Network tab: session_id in triage request
