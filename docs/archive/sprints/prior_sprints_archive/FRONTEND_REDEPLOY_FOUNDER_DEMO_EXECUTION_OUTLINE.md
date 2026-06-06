# Execution Outline — Frontend Redeploy + Founder Demo Sprint

**Sprint:** Frontend Redeploy + Founder Demo + Top Feedback Fixes  
**Created:** 2026-03-14

---

## Workstreams

| # | Workstream | Owner | Deliverable |
|---|------------|-------|-------------|
| 1 | Control docs | Planner | Blueprint, Outline, Acceptance |
| 2 | Pre-deploy check | Frontend release | Build pass, polish confirmed |
| 3 | Frontend redeploy | Frontend release | Vercel prod deploy |
| 4 | Post-deploy acceptance | Acceptance reviewer | Online check results |
| 5 | Founder demo run | Demo worker | Demo pass, notes |
| 6 | Top issues + fix loop | Product critic | 1–3 issues, optional fixes |
| 7 | Final judgment | All | Report, iteration log |

---

## Execution sequence

1. **Phase A — Control docs** (done first)
   - Sprint Blueprint
   - Execution Outline
   - Acceptance / SLA Criteria

2. **Phase B — Pre-deploy**
   - Inspect: UnifiedIntakePage, SimulationAssistant, scenarios, ReleaseIdentityBar
   - Confirm: 不自动发送, direct customer voice, human confirmation, pilot intro
   - Run: `cd ui && npm run build`
   - Stop if build fails

3. **Phase C — Deploy**
   - `cd ui && vercel --prod`
   - Capture: success/failure, URLs, alias status

4. **Phase D — Post-deploy**
   - Open production URL
   - Check: build info bar, polish visibility
   - Document: directly observed vs inferred

5. **Phase E — Founder demo**
   - Path: R1 → R2 → R3 or SIM1 → SIM2 → SIM3
   - Evaluate: first impression, believability, handoff, trust, value, hesitation

6. **Phase F — Top issues**
   - Identify 1–3 only
   - For each: what, why, fix now or defer

7. **Phase G — Optional fix loop**
   - If small, high-value, low-risk: fix
   - Rerun build, state if redeploy needed

8. **Phase H — Final judgment**
   - Top 3 sellability strengths
   - Top 3 hesitation points
   - Best next issue
   - Maturity level

---

## Role assignment

| Role | Responsibility |
|------|----------------|
| Planner | Control docs, sequence, scope |
| Frontend release | Build, deploy, verify |
| Demo worker | Run demo, capture notes |
| Product critic | Top issues, fix vs defer |
| Acceptance reviewer | Post-deploy check, iteration log |

---

## Demo plan

**Preferred order (Chen Kui Trial Pack):**

- **Real customer pack:** R1, R2, R3
- **Recommended trial:** SIM1, SIM2, SIM3

**Minimum if time limited:** R1, R2, SIM3

**Production URL:** https://ui-smoky-beta.vercel.app/workbench/unified-intake

---

## Likely loop count

- **Loop 1:** Pre-deploy → build → deploy → post-deploy check
- **Loop 2:** Founder demo → top issues
- **Loop 3 (optional):** Fix loop → retest → redeploy if needed

**Expected:** 2–3 loops.
