# Human-First Entry Flow — Execution Outline

**Sprint**: Human-First Entry Flow + Startup Latency Audit  
**Created**: 2026-03-15

---

## 1. Workstreams

| Workstream | Owner | Scope |
|------------|-------|-------|
| **Answer-first logic** | Backend / triage | Ensure add-car, claim, payment, missing-doc, remove-car get intent-specific first reply; avoid generic "内容不够完整" when intent is clear |
| **Button starters** | Frontend | On button click with empty input, auto-submit starter message and fetch first reply |
| **Live case summary** | Frontend | Show collapsible summary card during intake: intent, collected, still needed |
| **Latency audit** | Performance | Inspect cold vs warm flow; frontend vs backend vs LLM; document findings |

---

## 2. Role Assignment

| Role | Responsibility |
|------|----------------|
| Planner / architect | Document stack, design decisions |
| UX / conversation design | Reply templates, starter messages |
| Frontend worker | Button behavior, live summary UI |
| Backend / routing worker | Triage logic, soft_route handling, Toyota Corolla / 花冠 markers |
| Performance auditor | Latency diagnosis |
| QA / simulation worker | Run scenarios, guardrail, smoke check |

---

## 3. Implementation Order

1. **Phase A** — Document stack (Blueprint, UX Spec, Execution, SLA, Latency Audit)
2. **Loop 1** — Answer-first + real button starters
   - Backend: Add 花冠, 保费是多少, 才买 to markers; fix add-car detection for Toyota Corolla
   - Backend: When soft_route present and text is starter-only, return intent-specific first reply
   - Frontend: Button click with empty input → submit starter message, get first reply
3. **Loop 2** — Live case summary + latency audit
   - Frontend: Add live summary card during intake
   - Audit: Document cold vs warm, frontend vs backend vs LLM
4. **Optional Loop 3** — One high-value refinement if clear
5. **Validation** — Run scenarios, guardrail, smoke check, build
6. **Frontend redeploy** — Vercel prod
7. **Post-deploy inspection** — Founder judgment

---

## 4. Likely Loop Count

- **Minimum**: 2 loops (Loop 1: human-first + buttons; Loop 2: summary + latency)
- **Optional**: Loop 3 if one clear refinement remains

---

## 5. What Success Will Be Judged On

- Buttons feel like true starters (click → flow begins)
- First response acknowledges real ask, asks only next missing field
- Toyota Corolla example returns quote flow, not "内容不够完整"
- Live summary visible and useful
- Latency diagnosis documented with clear next-step recommendation

---

*See also: Acceptance/SLA Criteria, Startup Latency Audit Notes*
