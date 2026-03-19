# Turn 1 Lightweight + Cold-Start — Acceptance / SLA Criteria

---

## Turn 1 Speed

| Criterion | Target |
|----------|--------|
| Lightweight Turn 1 (rule path) | ~50–200 ms |
| LLM Turn 1 (warm) | 2–4 s acceptable |
| Cold Turn 1 | Pre-warm or min_instances reduces 5–15 s surprise |

---

## Quality Retention

| Criterion | Target |
|----------|--------|
| Guardrail | `guardrail_inbox_triage.sh` PASS |
| Inbox scenarios | `run_inbox_triage_scenarios.py` all pass |
| Multi-turn | `run_multi_turn_simulations.py` all strong |
| State audit | `audit_state_field_accuracy.py` all pass |
| Speed routing | `verify_speed_routing.py` OK |

---

## Cost

| Criterion | Target |
|----------|--------|
| Lightweight path | No LLM cost for eligible Turn 1 |
| Cold-start | Warmup = free; min_instances = documented approximate cost |

---

## Operational Complexity

| Criterion | Target |
|----------|--------|
| Warmup | Single script; clear runbook |
| Demo day | Run warmup 2–3 min before; or use min_instances |

---

## Not Worth It

- Lightweight path causes quality regression
- Cold-start mitigation adds >30 min setup
- Complexity outweighs speed gain
