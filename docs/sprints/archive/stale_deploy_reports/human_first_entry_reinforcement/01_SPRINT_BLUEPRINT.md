# Human-First Entry Flow Reinforcement + Redeploy — Sprint Blueprint

**Sprint**: Human-First Entry Flow Reinforcement + Redeploy  
**Created**: 2026-03-15  
**Scope**: Chen Kui Insurance Unified Entry — strengthen, validate, ship

---

## 1. Why Reinforcement Is Needed Now

The previous Human-First Entry Flow sprint introduced:
- Human-first reply logic (answer first, then ask next missing)
- Toyota Corolla quote recognition
- Quick-start buttons that auto-start flows
- Live Case Summary draft
- Startup latency audit docs

**Founder feedback**: One more strengthening pass before checking Vercel again. The product should feel more production-ready, not just feature-complete.

---

## 2. What the Founder Is Dissatisfied With

| Area | Concern |
|------|---------|
| **Answer-first** | Still occasional generic "内容不够完整" when intent is clear |
| **Buttons** | Do they feel like real starters? User should immediately feel "the system is helping me" |
| **Live Summary** | Is it clearer, more useful, more obviously real-time? |
| **Startup** | First-interaction slowness — what remains slow after prior work? |

---

## 3. Why This Sprint Focuses on Strengthening, Not Redesign

- **Scope guardrail**: Do NOT open broad new scope. Do NOT redesign the whole product.
- **Goal**: Make the 4 priorities more solid, retest carefully, redeploy, give founder clear things to inspect.
- **Method**: Blueprint → implement → test → evaluate → refine → redeploy loops.

---

## 4. What "Good Enough to Inspect on Vercel" Means

| Criterion | Definition |
|-----------|------------|
| **Answer-first** | Toyota Corolla quote, payment failed, missing doc chase, claim — all get intent-specific first reply, not generic fallback |
| **Button starters** | Click "获取报价" / "报事故" / "付款问题" / "上传材料" → system immediately returns first reply; user feels flow has started |
| **Live Summary** | Visible, understandable, updates per turn; shows intent + collected + still needed |
| **Startup** | Latency documented; cold vs warm vs LLM distinguished; perceived speed acceptable or cause identified |

---

## 5. Non-Negotiable Rule

Every loop MUST evaluate:
1. What changed
2. What became more intuitive / direct / human / structured
3. What did not improve
4. What still feels slow
5. Whether the loop was worth it
6. Recommended next step

---

*See also: Execution Outline, Acceptance/SLA Criteria, Reinforcement Checklist*
