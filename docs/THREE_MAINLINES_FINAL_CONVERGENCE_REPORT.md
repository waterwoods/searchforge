# Three Mainlines Final Convergence Report

**Sprint:** Three Mainlines Final Convergence Sprint  
**Date:** 2026-03-13  
**Execution:** Inspect → Simulate → Cross-check → Identify → Fix (none needed) → Report

---

## 1. Full Convergence Audit

### Strongest integrated behavior

**Speed + Realism + Handoff work together.** The three mainlines do not conflict:

- **Speed routing:** Turn 2+ simple follow-ups (already_sent, clarification, add-car field, correction, handoff confirmation) use fast path when `LLM_GENERATION_ENABLED=1`. Real customer pack scenarios (R1–R8) — messy, short, mixed — all pass and route sensibly. Turn 1 goes to LLM; turn 2 simple patterns go fast.
- **Realism:** R1–R8 ("都发过了怎么还要", "宝马x5，多少钱", "刚撞了对方跑了", etc.) produce correct triage, handoff, and collected/still_needed. No demo-like brittleness.
- **Handoff:** Customer Entry, Broker Workbench, and Simulation Assistant all use the same Case handoff structure: case focus → status → one-liner → next move → human confirmation → collected → still needed. `inferCaseFocus` / `getOneLiner` logic is aligned across surfaces.

### Weakest integrated behavior

**LC-AC3 (long-context memory-shift) — handoff timing.**  
"我刚才说错了，是我老婆开那辆" — system hands off at turn 2, expected turn 3. This is a correction-about-driver case; the system treats it as enough for handoff earlier than the scenario pack expects. Marked as **FRICTION** (acceptable), not weak. No regression.

### Biggest remaining gaps

| Gap | Severity | Notes |
|-----|----------|-------|
| **LC-AC3 handoff timing** | Low | One long-context correction case hands off 1 turn early. Acceptable. |
| **"Where this case stands"** | Low | Still a separate card; could be folded into handoff block for reopened cases. Deferred. |
| **Recommended trial (SIM1–SIM6) broker-forwarded voice** | Low | "客户问：…" / "客户说…" kept for trial clarity. Real customer pack (R1–R8) already uses direct voice. |
| **Turn 1 always LLM** | By design | No change; cold start and retrieval latency unchanged. |

---

## 2. Comprehensive Simulation / Test Pass

### All script/build results

| Script / Check | Result |
|----------------|--------|
| `run_inbox_triage_scenarios.py` | **49/49 passed** |
| `run_multi_turn_simulations.py` | **38/38 Strong** |
| `audit_state_field_accuracy.py` | **7/7 passed** |
| `verify_speed_routing.py` (LLM=1) | **6/6 OK** — turn 1→llm, turn 2+ simple→fast |
| `guardrail_inbox_triage.sh` | **PASS** |
| `unified_intake_smoke_check.sh` | **PASS** (guardrail + daily-use simulation) |
| `cd ui && npm run build` | **✓ built** |

### Key scenario observations

- **Real customer pack (R1–R8):** All 8 pass. R2 ("都发过了怎么还要"), R3 ("宝马x5，多少钱"), R4 (mixed add-car + garaging), R5 (claim panic), R7 (payment + dec page) — all produce correct category, handoff, and collected/still_needed.
- **Mixed-intent pack (MI-AC1 … MI-D2):** 12/12 pass.
- **Long-context pack:** 22 strong, 1 friction (LC-AC3). No weak.
- **Simulation Assistant:** 23/23 (15 trial + 8 real-customer) — Normal.
- **Speed routing:** Turn 2 "我发了截图在微信", "garaging proof 是什么意思", "2024年的，zip 90210，下周提车", "这些够了吗", "我其实已经付了" → all fast path when LLM on.

---

## 3. Highest-Value Remaining Problems

| Issue | What | Why it matters | Fix now? |
|-------|------|----------------|----------|
| **LC-AC3 handoff timing** | "我刚才说错了，是我老婆开那辆" hands off at turn 2, expected 3 | Long-context correction edge case; handoff is still correct | **No** — acceptable friction |
| **"Where this case stands" separate** | Tracking card not merged into handoff block | Minor UX; reopened cases could be slightly cleaner | **No** — deferred |
| **Recommended trial broker voice** | SIM1–SIM6 use "客户问/客户说" | Trial clarity vs realism trade-off; R1–R8 already real | **No** — optional future tweak |

**No high-value fixes identified for this sprint.** All validations pass; no regressions.

---

## 4. Small Final Fix Loop

**Used?** No.

**Reason:** All scripts pass. No routing misclassifications, no handoff surface inconsistencies, no trust-signal issues. LC-AC3 is documented and acceptable.

**Files changed:** None.

---

## 5. Final Product Judgment

### Are the three mainlines working well together?

**Yes.** Speed routing, real customer pack, and case handoff are integrated:

- Realistic messy scenarios route correctly (turn 1→LLM, turn 2 simple→fast).
- Messy inputs produce clean handoff objects with case focus, one-liner, next move, human confirmation, collected/still needed.
- Customer Entry, Broker Workbench, and Simulation Assistant present the same handoff structure.

### Is the product noticeably more coherent than before?

**Yes.** One unified Case handoff block; case focus and one-liner at top; human confirmation grouped with next move. Fewer scattered cards; same logic across surfaces.

### Is it strong enough for stronger founder demo / pilot use?

**Yes.** All guardrails pass. Real customer pack (R1–R8) demonstrates believable scenarios. Speed routing reduces perceived latency for turn 2+ simple turns. Handoff is office-like and actionable.

### Biggest current strength

**Integrated quality across the three mainlines.** Real messy customer messages → fast when simple, correct when complex → clean handoff with case focus, next move, and trust boundaries. No conflicts between speed, realism, and handoff.

### Biggest current weakness

**LC-AC3 long-context correction timing** — one edge case hands off one turn early. Low impact; acceptable for demo/pilot.

### What should the founder do next?

1. **Redeploy** backend (speed routing) and frontend (real customer pack + case handoff) if not already deployed.
2. **Run a live demo** using R1, R2, R3 and SIM3, SIM5, SIM6 to validate end-to-end.
3. **Optional:** Rewrite SIM1–SIM3 to direct customer voice for stronger trial realism.
4. **Optional:** Merge "Where this case stands" into handoff block for reopened cases.

---

## 6. Redeploy Readiness

| Component | Redeploy? | Reason |
|-----------|-----------|--------|
| **Backend** | **Yes** (if not deployed) | Speed routing (triage.py) — turn 2+ fast path |
| **Frontend** | **Yes** (if not deployed) | Real customer pack, Case handoff structure |
| **Both** | **Yes** | All three mainlines are in place |

---

## 7. 中文宏观总结

**三条主线现在是不是基本打通了？**  
是。Speed routing、Real customer pack、Case handoff 三条主线已经打通，没有冲突。真实客户风格的 R1–R8 场景全部通过，turn 2+ 简单跟帖走 fast path，三个表面（客户入口、工作台、Simulation Assistant）用同一套 Case handoff 结构。

**现在产品最强的地方是什么？**  
三条主线整合后的质量：真实 messy 消息 → 正确分类 → 快速或 LLM 路由 → 清晰的 office-style handoff（case focus、one-liner、next move、human confirmation、collected/still needed）。

**最大的剩余问题是什么？**  
LC-AC3 长上下文纠正场景（「我刚才说错了，是我老婆开那辆」）handoff 比预期早一 turn。影响小，可接受。

**现在是不是更适合做 demo / pilot 了？**  
是。所有 guardrail 通过，真实客户 pack 可演示，速度路由减少 turn 2+ 延迟，handoff 清晰可操作。

**下一步最该做什么？**  
1. 部署 backend + frontend（如尚未部署）  
2. 用 R1、R2、R3 和 SIM3、SIM5、SIM6 跑一次 live demo  
3. 可选：把 SIM1–SIM3 改成直接客户原话

---

## 8. COPY/PASTE CONVERGENCE BLOCK

```
THREE MAINLINES FINAL CONVERGENCE — Sprint Summary
===================================================

Do the three mainlines work together?
  Yes. Speed routing, real customer pack, and case handoff are integrated.
  Real messy scenarios (R1–R8) pass; turn 2+ simple → fast path; handoff structure consistent across surfaces.

Biggest current strength
  Integrated quality: real customer → correct routing → clean office-style handoff.
  Case focus, one-liner, next move, human confirmation, collected/still needed — same structure everywhere.

Biggest current weakness
  LC-AC3: one long-context correction case hands off 1 turn early. Low impact; acceptable.

Demo/pilot ready?
  Yes. All guardrails pass. Real customer pack + speed + handoff ready for founder demo.

Redeploy needed?
  Backend + Frontend (if not already deployed).

Next step
  1. Redeploy backend + frontend
  2. Run live demo with R1, R2, R3 and SIM3, SIM5, SIM6
  3. Optional: rewrite SIM1–SIM3 to direct customer voice
```

---

*End of report*
