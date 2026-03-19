# Human-First Entry Flow Reinforcement — Execution Outline

**Sprint**: Human-First Entry Flow Reinforcement + Redeploy  
**Created**: 2026-03-15

---

## 1. Workstreams

| Workstream | Owner | Scope |
|------------|-------|-------|
| **Answer-first** | Backend / triage | Strengthen intent-specific first reply; reduce generic fallback when soft_route or clear intent |
| **Button starters** | Frontend + Backend | Ensure click → first reply feels like real flow start; intent-specific starter replies |
| **Live Summary** | Frontend | Improve visibility, labels, real-time feel |
| **Startup latency** | Audit | Document cold vs warm vs LLM; identify remaining slowness |

---

## 2. Order of Implementation

1. **Phase A** — Control docs (Blueprint, Outline, SLA, Checklist)
2. **Phase B** — Baseline recheck (inspect current state of 4 priorities)
3. **Loop 1** — Strengthen human-first reply + button starters
   - Backend: soft_route override for minimal starter text; intent-specific first reply
   - Backend: Toyota Corolla / add-car acknowledgement strengthening
   - Frontend: Starter message wording if needed
4. **Loop 2** — Strengthen live summary + startup latency
   - Frontend: Case Summary labels (主题 / 已收集 / 还需); "实时更新" note
   - Audit: Latency diagnosis doc update
5. **Optional Loop 3** — One high-value, low-risk refinement
6. **Redeploy** — Frontend build + Vercel prod
7. **Post-deploy** — Inspection + founder showcase

---

## 3. What Will Be Re-tested

- `PYTHONPATH=. python3 scripts/run_inbox_triage_scenarios.py`
- `PYTHONPATH=. python3 scripts/run_multi_turn_simulations.py` (if exists)
- `PYTHONPATH=. python3 scripts/audit_state_field_accuracy.py` (if exists)
- `PYTHONPATH=. python3 scripts/verify_speed_routing.py`
- `bash scripts/guardrail_inbox_triage.sh`
- `bash scripts/unified_intake_smoke_check.sh` (if exists)
- `cd ui && npm run build`

---

## 4. Likely Loop Count

- **Minimum**: 2 loops (Loop 1: human-first + buttons; Loop 2: summary + latency)
- **Maximum**: 3 loops (only if one clearly valuable, low-risk refinement remains)

---

## 5. Success Signals

- Toyota Corolla example returns quote flow, not "内容不够完整"
- Button click with empty input → first system reply immediately
- Live summary visible and useful during intake
- Latency cause documented

---

*See also: Product Blueprint, Acceptance/SLA Criteria, Reinforcement Checklist*
