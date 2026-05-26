# Structured Case Convergence + Case Report Sprint Report

**Sprint:** Structured Case Convergence + Case Report  
**Date:** 2026-03-12  
**Mode:** Long-running structured execution (inspect → design → implement → simulate → verify)

---

## 1. Initial audit

### Strongest current surface
- **Broker Workbench case card** — Already had Case focus, Your next move, Collected/Still needed chips, human confirmation, urgency badges. Structure aligned with `BROKER_HANDOFF_CLARITY_GUIDE.md`. Queue cards show case focus first, attention label, readiness, compact preview, last update.

### Weakest current surface
- **Customer Entry handoff** — When handoffReady, showed only last reply + "查看工作台" button. No consolidated case summary before switching.
- **Simulation Assistant** — Per-turn tags (collected, still needed, human confirmation) but no final consolidated case summary. Outcome felt like replay bubbles, not a case.

### Biggest clarity gap
1. **No explicit "Case Report"** — Case info existed but was not labeled as a single "this is the case" block. Founder/broker had to scan multiple sections.
2. **collection_stage not in case card** — "Collecting" vs "Ready for handoff" appeared only in turn bubbles, not in the main case display.
3. **Simulation Assistant outcome** — No case summary at completion; felt like debug replay rather than office outcome.
4. **"What changed" after append** — "Just updated" badge existed but no explicit line describing what was refreshed.

### Classification
**Usable but fragmented** — Strong signals existed; they were not converged into one clear "Case Report" surface.

---

## 2. Chosen case-convergence changes

| Change | Why |
|--------|-----|
| **Case Report block** | Make "this is the case" explicit with a titled card: Case focus, Status, Your next move, Collected, Still needed, Human confirmation. |
| **collection_stage in case card** | Show "Collecting info" vs "Ready for handoff" in the main case display when API provides it. |
| **Case Report in Simulation Assistant** | When simulation completes, show a compact case summary so the outcome feels like a case, not only replay. |
| **"What changed" line after append** | When case_activity is follow_up_added, show "What changed: Next move, collected/still needed refreshed from new customer message." |

---

## 3. Implementation changes made

### Files changed

| File | What changed |
|------|--------------|
| `ui/src/pages/UnifiedIntakePage.tsx` | (1) Renamed action card to "Case Report" with subtitle "— what this case is, what we collected, what to do next"; (2) Added collection_stage tag (Collecting info / Ready for handoff) when available; (3) Added "What changed" line when case_activity is follow_up_added. |
| `ui/src/components/simulation/SimulationAssistant.tsx` | (1) Added Case Report card when simulation completes (last system turn has triageResult); shows Status, Your next move, Collected, Still needed, Human confirmation in one block; (2) Exported humanizeStructuredField for consistency. |
| `scripts/unified_intake_smoke_check.sh` | Added step 15d: Verify Case Report card shows Case focus, Status, Your next move, Collected, Still needed, Human confirmation. |

---

## 4. Before vs after

### What became clearer
- **Case Report** — One titled block: "Case Report — what this case is, what we collected, what to do next." Founder and broker see the case at a glance.
- **Status** — "Collecting info" vs "Ready for handoff" now visible in the main case card when API returns collection_stage.
- **Simulation Assistant outcome** — When a run completes, a Case Report card appears above the Replay, summarizing the outcome.
- **What changed** — After append, an explicit line: "What changed: Next move, collected/still needed refreshed from new customer message."

### What still remains scattered
- **Customer Entry handoff** — Still no Case Report before switching to Broker Workbench. User must click "查看工作台" to see the full case. Could add a compact summary in a future pass.
- **Field values** — Collected/Still needed show field names (Year, Make/Model) not extracted values (2025, Honda CR-V). Values live in conversation_summary; future enhancement.
- **"What changed in latest turn" for multi-turn** — No per-turn diff (e.g. "This turn added: year, zip"). Would require backend support.

---

## 5. Simulation / trial check

| Scenario set | Result |
|--------------|--------|
| Inbox triage scenarios | 49/49 passed |
| State field accuracy audit | 7/7 passed |
| Multi-turn simulations | 38/38 passed |
| Adversarial real-user | 27 strong, 0 weak |
| Complex adversarial | 22 strong, 1 acceptable friction |
| Simulation Assistant (SIM1–SIM15) | 15 Normal, 0 Needs review, 0 Off-flow |
| Guardrail inbox triage | PASS |

Case Report structure was reviewed against: Cancellation risk, Missing document, Add-car quote, SIM15 (strongest multi-turn proof). Case summary usefulness, collected/still needed readability, and human confirmation clarity all improved.

---

## 6. Validation summary

| Check | Result |
|-------|--------|
| `run_inbox_triage_scenarios.py` | 49/49 passed |
| `audit_state_field_accuracy.py` | 7/7 passed |
| `guardrail_inbox_triage.sh` | PASS |
| `cd ui && npm run build` | Success |

---

## 7. Redeploy readiness

**Frontend only** — All changes are in `ui/`. No backend changes. Redeploy Vercel/frontend when convenient.

---

## 8. Final judgment

**Good improvement with some remaining clutter.**

- Case is now more clearly packaged in a single "Case Report" block.
- More useful for Chen Kui / assistants: one place to see focus, status, next move, collected, still needed, human confirmation.
- More useful for founder debugging: explicit Case Report in both Workbench and Simulation Assistant.
- More office-like: titled "Case Report" and "outcome of this run" (Simulation Assistant).
- Remaining weakness: Customer Entry handoff still lacks a Case Report before switching; no per-turn "what changed" for multi-turn.

---

## 9. 中文宏观总结

- **现在 case 有没有更像一个正式 case 了？** 有。Broker Workbench 和 Simulation Assistant 都有明确的 "Case Report" 区块，把 Case focus、Status、Your next move、Collected、Still needed、Human confirmation 集中在一起。
- **哪些信息现在更容易看懂了？** Case Report 标题和结构让「这是什么 case、收集了什么、还缺什么、下一步做什么、哪些要人工确认」一目了然。append 后有 "What changed" 说明。
- **陈奎和助手以后会不会更容易接手？** 会。一个区块就能理解 case，不用在多个卡片间跳转。
- **我们开发时会不会更容易检查了？** 会。Simulation Assistant 跑完会显示 Case Report，方便验证提取是否正确。
- **还剩下最大的缺点是什么？** Customer Entry 交接时还没有 Case Report，用户要点「查看工作台」才能看到完整 case；多轮对话没有「本轮新增了什么」的展示。

---

## 10. COPY/PASTE CASE SUMMARY BLOCK

```
STRUCTURED CASE CONVERGENCE — CASE REPORT SPRINT

New case display structure
-------------------------
1. Case Report (titled block)
   - Case focus: Add car quote / Premium review / Missing document / etc.
   - Status: Collecting info | Ready for handoff (when API provides collection_stage)
   - Your next move: One operational sentence
   - Collected: Green chips (year, make_model, zip, delivery_date, etc.)
   - Still needed: Orange chips (primary_driver, etc.)
   - Human confirmation recommended: When VIN, customer_says_sent, payment status, etc.

2. What changed (when append)
   - "What changed: Next move, collected/still needed refreshed from new customer message."

3. Simulation Assistant
   - When run completes: Case Report card above Replay with same structure.

What is shown first
-------------------
Case focus, Status (if available), Your next move, Collected, Still needed, Human confirmation — in one compact Case Report card.

What is most useful now
-----------------------
- One "Case Report" block instead of scattered signals
- collection_stage visible in main case card
- Simulation Assistant outcome = case summary, not only replay
- "What changed" after append

What still needs human confirmation
-----------------------------------
Same as before: VIN, primary_driver, customer_says_sent_*, payment status, cancellation risk. Shown in "Human confirmation recommended" with optional field list (请人工确认：...).

Redeploy needed
---------------
Frontend only. No backend changes.
```

---

*End of sprint report*
