# Human Front Door + Talk-to-Agent — Execution Outline

**Sprint:** Human Front Door + Talk-to-Agent Sprint  
**Created:** 2026-03-15

---

## 1. Workstreams

| ID | Workstream | Owner | Scope |
|----|------------|-------|-------|
| W1 | Welcome / Reassurance Copy | Frontend | UnifiedIntakePage.tsx |
| W2 | Talk-to-Agent Button + Backend | Frontend + Backend | Button, triage routing |
| W3 | Business-Readable Case Summary | Frontend | humanizeStructuredField |
| W4 | Trust Boundary Wording | Frontend | Handoff card, reassurance lines |

---

## 2. Implementation Order

1. **Loop 1 — Human Front Door**
   - W1: Welcome card copy, secondary reassurance line, examples label
   - W4 (partial): Handoff card wording, "办公室会尽快处理"
   - **Do NOT** add Talk-to-Agent yet; focus on making existing flow feel more human

2. **Loop 2 — Talk-to-Agent + Business Summary**
   - W2: Add "联系人工" button, backend support for customer_requested_human
   - W3: humanizeStructuredField for Case Summary labels
   - W4 (remainder): Trust boundary in handoff

3. **Loop 3 — Optional Refinement**
   - One wording improvement OR one placement tweak
   - Only if clearly valuable, low-risk

---

## 3. What Will Be Tested

| Test | Command | Purpose |
|------|---------|---------|
| Inbox triage scenarios | `PYTHONPATH=. python3 scripts/run_inbox_triage_scenarios.py` | Routing, categories |
| Multi-turn simulations | `PYTHONPATH=. python3 scripts/run_multi_turn_simulations.py` | Conversation flow |
| State field accuracy | `PYTHONPATH=. python3 scripts/audit_state_field_accuracy.py` | Structured fields |
| Speed routing | `PYTHONPATH=. python3 scripts/verify_speed_routing.py` | Fast path |
| Guardrail | `bash scripts/guardrail_inbox_triage.sh` | Drift check |
| Smoke check | `bash scripts/unified_intake_smoke_check.sh` | End-to-end |
| Build | `cd ui && npm run build` | Frontend compiles |

---

## 4. Likely Loop Count

- **Loop 1:** Required — Human Front Door
- **Loop 2:** Required — Talk-to-Agent + Business Summary
- **Loop 3:** Optional — only if one clear refinement remains

---

## 5. Files to Modify

| File | Changes |
|------|---------|
| `ui/src/pages/UnifiedIntakePage.tsx` | Welcome copy, buttons, Case Summary humanize, handoff copy |
| `ui/src/api/inboxTriage.ts` | Add `talk_to_agent` to SoftRouteIntent (if needed) |
| `services/fiqa_api/inbox_triage/triage.py` | customer_requested_human detection, handoff |
| `services/fiqa_api/routes/inbox_triage.py` | Handle talk_to_agent soft_route (if needed) |

---

*See also: Acceptance Criteria, Talk-to-Agent Policy*
