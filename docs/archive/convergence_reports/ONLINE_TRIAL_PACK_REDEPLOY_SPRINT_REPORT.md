# Online Trial Pack Redeploy + Simulation Assistant Trial Report

**Sprint:** Online Trial Pack Redeploy + Simulation Assistant Trial Sprint  
**Date:** 2026-03-12  
**Mode:** Execution + trial verification

---

## 1. Redeploy result

| Item | Value |
|------|-------|
| **Production URL** | https://ui-smoky-beta.vercel.app |
| **Unified Intake route** | https://ui-smoky-beta.vercel.app/workbench/unified-intake |
| **Deployment URL** | https://ui-or6nxpgbn-andys-projects-1f411b73.vercel.app |
| **Status** | Success |
| **Build** | Vite build completed in ~40s |
| **Warnings** | Chunk size > 500 kB (expected; no action) |

Vercel project `ui` is linked. Production alias `ui-smoky-beta.vercel.app` points to the latest deploy. `VITE_API_BASE_URL` is configured in Vercel for production (Cloud Run backend).

---

## 2. Online feature presence

| Feature | Status | Notes |
|---------|--------|-------|
| Unified Intake page loads | Yes | Route `/workbench/unified-intake` |
| Customer Entry tab | Yes | Default tab, 客户入口 |
| Broker Workbench tab | Yes | Second tab |
| Simulation Assistant button | Yes | Top-right on Customer Entry |
| 15 scenarios in drawer | Yes | Notice/Cancellation, Missing document, Add car, Claim, Renewal, etc. |
| Trial tip in Simulation Assistant | Yes | "Trial tip: Start with Notice/Cancellation, Missing document, Add car, then Claim or Renewal." |
| Chen Kui trial hint (Broker Workbench) | Yes | "Chen Kui trial: Load this queue to see cancellation risk → missing document → add-car..." |
| Load founder demo queue | Yes | Button visible on Broker Workbench |
| No obvious UI breakage | Yes | Page renders correctly |

---

## 3. Online trial scenario results

All 5 trial scenarios were run against the production backend (`https://fiqa-api-g7zatxrycq-uw.a.run.app/api/inbox/triage`):

| Scenario | SIM ID | Handoff at turn | Expected | Result |
|----------|--------|-----------------|----------|--------|
| Cancellation risk | SIM1 | 2 | 2 | Pass |
| Missing document | SIM2 | 2 | 2 | Pass |
| Add-car quote | SIM3 | 2 | 2 | Pass |
| Premium review | SIM4 (SIM6) | 2 | 2 | Pass |
| Claim intake | SIM5 | 2 | 2 | Pass |

Backend triage API responds correctly. Handoff timing matches expectations for all 5 scenarios.

---

## 4. Trial readiness review

**Verdict: Ready for online trial**

- **Easy to understand:** Customer Entry is clear; Simulation Assistant is one click away.
- **Trial order sensible:** Best 3 (cancellation → missing doc → add-car) and best 5 (add premium, claim) are documented.
- **Product looks trustworthy:** Structured case output, urgency, next step, Collected/Still needed chips.
- **Workbench useful:** Case focus, Your next move, Human confirmation badge when applicable.

**Minor concerns:**
- Simulation Assistant drawer can obscure Broker Workbench tab on small viewports; close drawer before switching tabs.
- Backend `/readyz` reports `not_ready` (Qdrant/embedding); triage API still works (rule/LLM path).

---

## 5. Small fix made (if any)

None. No trial-blocking issues found. Docs updated with production URL.

---

## 6. Final founder instructions

1. Open: **https://ui-smoky-beta.vercel.app/workbench/unified-intake**
2. **Option A — Simulation Assistant (fastest):** Click **Simulation Assistant** → select **Notice / Cancellation** → **Run simulation** → **Next turn** (or Auto-play). Repeat for Missing document, Add car (Chinese), Claim intake, Renewal / Premium.
3. **Option B — Broker Workbench:** Click **Broker Workbench** → **Load founder demo queue** → cancellation-risk case opens first. Reopen Missing document, Add-car from Recent cases.
4. Watch for: Case focus, Your next move, Collected/Still needed, Human confirmation recommended.
5. After trial: Ask Chen Kui the 5 value validation questions (see §12).

---

## 7. Validation summary

| Check | Result |
|------|--------|
| Frontend redeploy succeeded | Yes |
| Online Simulation Assistant present | Yes |
| Online trial scenarios usable | Yes (API verified) |
| Backend reachable from production frontend | Yes |
| CORS / production env | No issues observed |

---

## 8. Recommended next step

**Ready for online trial.** Founder can share https://ui-smoky-beta.vercel.app/workbench/unified-intake with Chen Kui. Use Simulation Assistant for quick scenario runs; use Broker Workbench + Load founder demo queue for full walkthrough.

---

## 9. 中文或中英混合宏观总结

- **前端这次重新发出去了没有？** 发出去了。Vercel `vercel --prod` 部署成功，生产 URL：https://ui-smoky-beta.vercel.app/workbench/unified-intake
- **Trial pack 线上现在是否真的能用了？** 能用了。5 个核心场景（cancellation、missing doc、add-car、premium、claim）线上 API 全部通过，handoff 时机正确。
- **Simulation Assistant 在线上能不能直接跑？** 能。点击 Simulation Assistant → 选场景 → Run simulation → Next turn / Auto-play，系统回复来自真实 triage API。
- **现在给陈奎试是否合适？** 合适。产品路径清晰，trial hint 和 Chen Kui trial 文案都在线，无阻塞问题。
- **如果还有问题，最可能是什么？** 后端 `/readyz` 显示 not_ready（Qdrant/embedding），但不影响 triage；若将来需要 retrieval 辅助流程，需确认 Qdrant 配置。

---

## 10. Practical online trial checklist

- [ ] Open: https://ui-smoky-beta.vercel.app/workbench/unified-intake
- [ ] Click **Simulation Assistant** (Customer Entry tab)
- [ ] Run **3 scenarios first:** Notice/Cancellation → Missing document → Add car (Chinese)
- [ ] If time allows, run **5 scenarios:** + Renewal/Premium, Claim intake
- [ ] Notice: Case focus, Your next move, Collected/Still needed, evaluation tag
- [ ] Ask after trial: 5 value validation questions (§12)

---

## 11. Trial readiness summary

| Area | Status |
|------|--------|
| Strongest online trial paths | Cancellation → Missing doc → Add-car (3); + Premium, Claim (5) |
| Minor concerns | Drawer viewport; readyz not_ready (non-blocking) |
| What not to overclaim | Inbox sync, OCR, CRM, auto-send |

---

## 12. COPY/PASTE ONLINE TRIAL BLOCK

```
Production URL
https://ui-smoky-beta.vercel.app/workbench/unified-intake

Best 3-scenario order
1. Cancellation risk (urgency, same-day)
2. Missing document (operational, "already sent")
3. Add-car quote (revenue, multi-turn, Collected)

Best 5-scenario order
1. Cancellation risk
2. Missing document
3. Add-car quote
4. Premium review
5. Claim intake

What each proves
• Cancellation: prioritizes urgent follow-up; same-day action
• Missing document: structured follow-up; verify receipt
• Add-car: collects year/model/zip; broker sees Collected chips
• Premium review: retention-style; repetitive office work
• Claim intake: first-response guidance; accident + hit-and-run

5 post-trial questions
1. Which scenario felt most useful to your office?
2. Which part still feels risky or not trustworthy?
3. Would this save you or your assistant time?
4. What would you want it to do next?
5. What would you be willing to try first in a pilot?
```

---

*See also: `docs/CHEN_KUI_TRIAL_PACK.md`, `docs/UNIFIED_INTAKE_DEMO_READINESS.md`, `docs/runbooks/UNIFIED_INTAKE_MVP_RUNBOOK.md`*
