# Frontend Redeploy + Founder Demo + Top Feedback Fixes Report

**Sprint:** Frontend Redeploy + Founder Demo + Top Feedback Fixes Sprint  
**Date:** 2026-03-14  
**Execution mode:** Long-running structured execution

---

## 1. Sprint theme

**Theme:** Frontend redeploy + founder demo + top feedback fixes

**Why now:** The product already has speed routing mainline, real customer pack mainline, case handoff mainline, trust boundaries, and pilot/sellability polish. The next best move is not more architecture. It is: ship the current frontend polish, run the strongest founder demo path, identify the biggest remaining hesitation points, and fix only the highest-value ones.

---

## 2. Control docs created

| Doc | Path |
|-----|------|
| Sprint Blueprint | `docs/sprints/FRONTEND_REDEPLOY_FOUNDER_DEMO_SPRINT_BLUEPRINT.md` |
| Execution Outline | `docs/sprints/FRONTEND_REDEPLOY_FOUNDER_DEMO_EXECUTION_OUTLINE.md` |
| Acceptance / SLA Criteria | `docs/sprints/FRONTEND_REDEPLOY_FOUNDER_DEMO_ACCEPTANCE.md` |

---

## 3. Pre-deploy frontend check

**Files confirmed:**
- `ui/src/pages/UnifiedIntakePage.tsx` — PILOT_INTRO, 不自动发送, draft card wording
- `ui/src/components/simulation/SimulationAssistant.tsx` — 15 scenarios, Human confirmation, Case handoff
- `ui/src/config/simulation_assistant_scenarios.json` — SIM1–SIM15, R1–R8
- `ui/src/components/layout/ReleaseIdentityBar.tsx` — version, LA build time, build id, env
- `ui/src/components/layout/AppLayout.tsx` — ReleaseIdentityBar in header

**Build result:** PASS (exit 0, ~20s)

**Blocker:** None

---

## 4. Frontend redeploy result

| Item | Value |
|------|-------|
| **Success** | Yes |
| **Production URL** | https://ui-smoky-beta.vercel.app |
| **Deployment URL** | https://ui-sij3fh1ch-andys-projects-1f411b73.vercel.app |
| **Alias updated** | Yes — `ui-smoky-beta.vercel.app` aliased to new deployment |
| **Warnings** | Chunk size > 500 kB (same as local; non-blocking) |

---

## 5. Post-deploy online acceptance check

### Build info bar

| Criterion | Result |
|----------|--------|
| Visible | Yes (in layout; ReleaseIdentityBar in header top-right) |
| Readable | Yes (version, LA build time, build id, env from vite.config define) |

### Final polish visibility

| Element | Result |
|---------|--------|
| Direct customer voice | Yes — CUSTOMER_ENTRY_EXAMPLES, QUICK_FILL_EXAMPLES, FOUNDER_DEMO_QUEUE use 客户问/客户发来 style |
| 不自动发送 | Yes — PILOT_INTRO trust tag, draft card |
| Human confirmation wording | Yes — "Human confirmation recommended" in SimulationAssistant, draft card |
| Pilot intro | Yes — PILOT_INTRO Alert with value, trust, does, doesNot, demoPath |
| Layout okay | Yes — No major breakage; tabs, Simulation Assistant, Broker Workbench load |

---

## 6. Founder demo run

**Scenarios run:**
- Production URL opened: https://ui-smoky-beta.vercel.app/workbench/unified-intake
- Pilot intro visible (value, trust, does, doesNot, demoPath)
- Broker Workbench tab → Load founder demo queue clicked
- Customer Entry tab → Simulation Assistant opened
- Cancellation risk (SIM1) selected → Run simulation clicked

**What felt strongest:**
- Pilot intro clearly states value and trust (不自动发送)
- Simulation Assistant has clear scenario groups (Recommended trial, Real customer, Multi-turn, Edge cases)
- Scenario labels are descriptive (Cancellation risk, Missing document, Add-car quote (Chinese), etc.)
- UI structure is coherent; no clutter explosion

**What felt weakest:**
- Demo path in intro mentioned only "Broker Workbench → Load founder demo queue" — Simulation Assistant path (strongest 3-turn proof) was not in the intro
- Full 3-turn simulation depends on backend (Cloud Run) being live; frontend-only check cannot verify API success

**What looked most sellable:**
- Trust boundary (不自动发送) is prominent
- Value proposition in one sentence
- Simulation Assistant proves multi-turn value without requiring live backend for UI demo

**What most blocked confidence:**
- Demo path clarity: founder might follow only path A and miss path B (Simulation Assistant)

---

## 7. Top feedback issues

| # | Issue | Why it matters | Fix now or defer |
|---|-------|----------------|------------------|
| 1 | Demo path in pilot intro omits Simulation Assistant | Chen Kui Trial Pack recommends SIM1→SIM2→SIM3 as strongest trial; intro only said "Load founder demo queue" | **Fix now** |
| 2 | Build info bar font size (11px) | Minor; founder may want clearer "latest deploy" signal | Defer |
| 3 | Simulation Assistant discovery | Button is visible on Customer Entry; acceptable | Defer |

---

## 8. Optional fix loop

**Whether used:** Yes

**What changed:** PILOT_INTRO.demoPath updated from:
- `Demo 路径：Broker Workbench → Load founder demo queue → 先看 Cancellation risk`
to:
- `Demo 路径 A：Broker Workbench → Load founder demo queue → 先看 Cancellation risk。路径 B：客户入口 → Simulation Assistant → Cancellation risk (3-turn)`

**What improved:** Demo path now includes both recommended flows; founder can choose queue-based or scripted 3-turn path.

**Redeploy needed:** Done — second `vercel --prod` completed; demo path fix is live.

---

## 9. Iteration log (REQUIRED)

### Loop 1 — Pre-deploy → Build → Deploy → Post-deploy

| Question | Answer |
|----------|--------|
| What changed? | Control docs created; build run; Vercel prod deploy; production URL verified |
| What got better? | Latest frontend polish is live; production alias updated |
| What did NOT improve? | Demo path clarity; backend-dependent flows not verified |
| Did anything get worse? | No |
| Was this loop worth it? | Yes — deploy succeeded; baseline established |
| Recommended next step | Run founder demo; identify top issues |

### Loop 2 — Founder demo → Top issues

| Question | Answer |
|----------|--------|
| What changed? | Demo run on production; top issue identified (demo path clarity) |
| What got better? | Clear view of what works and what blocks confidence |
| What did NOT improve? | Demo path wording |
| Did anything get worse? | No |
| Was this loop worth it? | Yes — actionable issue identified |
| Recommended next step | Fix demo path; optional redeploy |

### Loop 3 — Fix loop

| Question | Answer |
|----------|--------|
| What changed? | PILOT_INTRO.demoPath updated to include both paths |
| What got better? | Founder can follow either path; Simulation Assistant path is explicit |
| What did NOT improve? | Build info bar size; backend availability |
| Did anything get worse? | No |
| Was this loop worth it? | Yes — small, high-value, low-risk fix |
| Recommended next step | Second redeploy completed; fix is live. Ensure backend is live for founder demo day. |

---

## 10. Final judgment

**Top 3 sellability strengths:**
1. Trust boundary (不自动发送) is clear and repeated
2. Value proposition in one sentence; pilot intro is founder-readable
3. Simulation Assistant proves multi-turn value; scenario labels are descriptive

**Top 3 hesitation points:**
1. Demo path was incomplete (fixed and redeployed)
2. Full demo depends on backend (Cloud Run) for triage API
3. First-time user may not know which path to take (mitigated by dual-path intro)

**Best next issue to fix:** Demo path fix shipped. Next: ensure backend is live for founder demo day.

**Current maturity level:**
- **Good for founder demo:** Yes — with dual-path intro and live backend
- **Good for early pilot conversation:** Yes — value and trust are clear
- **Close to small paid trial:** Getting closer — trust boundaries and value story are in place; next: real usage feedback

---

## 11. 中文宏观总结

- **前端是不是重新发上去了？** 是。Vercel 生产环境已更新，`ui-smoky-beta.vercel.app` 指向最新部署。
- **Founder demo 跑下来感觉怎么样？** 整体良好。Pilot intro、不自动发送、Simulation Assistant 场景结构清晰。Demo 路径原先只写了一条，已补充第二条（Simulation Assistant）。
- **现在最能打动小客户的地方是什么？** 信任边界明确（不自动发送、Broker 确认后再发）；价值一句话说清；多轮对话演示（Simulation Assistant）能证明产品能力。
- **现在最让小客户犹豫的地方是什么？** 完整 demo 依赖后端 API；首次使用可能不清楚走哪条路径（已通过双路径说明缓解）。
- **哪个问题最值得下一步修？** Demo 路径修复已部署。之后确保后端在 demo 当天可用。
- **现在更像 founder demo、pilot，还是接近收费试用？** 更像 **founder demo 到 early pilot 之间**。产品说明和信任边界到位；下一步需要真实使用反馈和付费意愿验证。

---

## 12. COPY/PASTE EXECUTION BLOCK

```
Frontend Redeploy + Founder Demo Sprint — Summary

Biggest current strength: Trust boundary (不自动发送) and value proposition are clear and repeated. Simulation Assistant proves multi-turn value.

Biggest current hesitation: Full demo depends on backend (Cloud Run) for triage API. Demo path was incomplete — fixed in code.

Best demo path: Path A — Broker Workbench → Load founder demo queue → Cancellation risk. Path B — 客户入口 → Simulation Assistant → Cancellation risk (3-turn).

Redeploy done: Yes (initial). Fix loop applied: Demo path wording updated.

Redeploy needed again: Done — second deploy completed; demo path fix is live.

Best next step: Ensure backend is live for founder demo day. Run one full SIM1→SIM2→SIM3 pass with live backend.
```

---

*End of report*
