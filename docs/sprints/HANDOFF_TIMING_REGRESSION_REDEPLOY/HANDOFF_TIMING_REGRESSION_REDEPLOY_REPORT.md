# Handoff Timing Regression + Redeploy Report

**Sprint:** Handoff Timing Regression + Redeploy Sprint  
**Created:** 2026-03-19  
**Scope:** SearchForge → Chen Kui Insurance Unified Entry

---

## 1. Sprint Theme

- **What was tested:** Handoff timing regression pack (HT1–HT10); premium/payment "one more useful question" fix-next from prior audit.
- **Why now:** Prior audit fixed HT8; HT3, HT9, HT10 remained acceptable-for-trial with fix-next. This sprint systematically evaluated whether to implement premium/payment "one more ask" and redeploy.

---

## 2. Document Set Created

| Doc | Purpose |
|-----|---------|
| 01_HANDOFF_TIMING_REGRESSION_BLUEPRINT.md | Why this regression sprint; what we strengthen; what we defer |
| 02_EARLY_HANDOFF_SIMULATION_PACK_SPEC.md | 10 flows; one more question patterns; over-questioning guard |
| 03_EVALUATION_CRITERIA_SPEC.md | Per-simulation judgment; too early/late; case completeness |
| 04_FIX_QUEUE_REDEPLOY_SPEC.md | Fix-now / acceptable / fix-next; deferred fix-next note |
| 05_EXECUTION_OUTLINE.md | Workstreams; loop plan; validation |
| 06_ACCEPTANCE_CRITERIA.md | Regression coverage; disciplined fixes; production readiness |
| 07_FOUNDER_VERIFICATION_NOTES.md | What founder should test on Vercel |

---

## 3. Baseline Audit

### Strongest Timing Areas

| Area | Evidence |
|------|----------|
| Add-car with driver ask | T2 asks driver; T3 adds driver → handoff |
| Talk-to-agent | Immediate handoff T1 |
| Vague | No handoff T1 for "帮我", "在吗" |
| Correction | "不是这个车" used; handoff T3 with correct vehicle |
| Mixed-intent T1 | No handoff; collect both |
| Add-car + doc clarification (HT8) | Answer question; handoff T2 (prior fix) |

### Biggest Remaining Risk

**Premium/Payment T2 handoff when T3 adds more (HT3, HT9, HT10):** User says "账单发你了" or "我付了" at T2; we hand off. T3 "其中一辆去掉会便宜吗" or "截图发你微信了" would append. Broker may act before T3.

### Biggest Incomplete-Case Risk

Same as above — broker receives case at T2; customer sends T3 with remove-vehicle or screenshot; append captures it but timing race if broker acts immediately.

### Biggest Broker-Rework Source

T2 handoff for premium/payment — broker may need to wait for append or re-ask.

---

## 4. 10–20 Point Breakdown

1. **Too early handoff:** Hand off before customer finishes key details (driver, remove-vehicle, screenshot).
2. **Acceptable for trial:** T2 handoff; T3 would append; broker can infer from source.
3. **Flows in scope:** Add-car, premium, payment, missing doc, talk-to-agent, correction, mixed, vague.
4. **Premium late-detail:** T2 bill_sent; T3 "其中一辆去掉会便宜吗" — acceptable; fix-next.
5. **Payment late-proof:** T2 paid; T3 "截图发你微信了" — acceptable; fix-next.
6. **Missing-doc late-question:** T2 handoff; T3 "是什么意思" — append; acceptable.
7. **Add-car late-detail:** T2 ask driver; T3 add driver — strong.
8. **Correction-after-handoff:** "不是这个车" — strong.
9. **One more useful question:** Premium: "是否有一辆想拿掉或调整？"; Payment: "截图发了吗".
10. **Over-questioning:** Asking for bill when sent; endless asks when enough.
11. **Fix-now criteria:** Blocks trial; trust-breaking.
12. **Acceptable-for-trial criteria:** Minor friction; T3 append; document for observation.
13. **Fix-next criteria:** Premium/payment one more ask — scope to 3+ turn only.
14. **Small fixes allowed:** One ask; single threshold; marker.
15. **Intentionally deferred:** Premium/payment ask at T2 — breaks 2-turn scenarios.
16. **Founder manual test:** HT8 (add-car + garaging); premium 3-turn; payment 3-turn.
17. **Broker workload impact:** T2 handoff — may wait for append.
18. **Next sprint feed:** Fix-next with 3+ turn scope; observation log from trial.

---

## 5. Iteration Loop 1

### What Was Tested

- 10 handoff-timing simulations (HT1–HT10)
- Full guardrail (inbox triage, multi-turn, adversarial, complex, simulation assistant, broker stress, handoff timing)

### What Stayed Strong

- HT1: Add-car + driver T3 — handoff at T3 ✓
- HT2: Missing doc — handoff at T2 ✓
- HT4: Talk-to-agent — handoff T1 ✓
- HT5: Correction — handoff T3 ✓
- HT6: Mixed — no handoff T1 ✓
- HT7: Vague — no handoff T1 ✓
- HT8: Add-car + garaging same turn — handoff T2 ✓

### What Failed or Felt Weak

- **HT3, HT9, HT10:** Handoff at T2 when T3 adds remove-vehicle or screenshot. Acceptable-for-trial; fix-next.

### Whether Loop 1 Was Worth It

**Yes.** Confirmed baseline; all 10 pass; guardrail PASS.

---

## 6. Iteration Loop 2

### Root-Cause Patterns Identified

| Pattern | Root Cause | Fix Attempted |
|---------|------------|---------------|
| HT3/HT10: Premium T2 handoff | customer_turn_count >= 2 → handoff; no remove_vehicle ask | Add ask when bill_sent, no remove_vehicle at T2 |
| HT9: Payment T2 handoff | Same | Add ask when paid, no screenshot at T2 |

### What Entered Fix-Now

- None.

### What Was Acceptable for Trial

- HT3, HT9, HT10 — T2 handoff; T3 would append.

### What Entered Fix-Next (Deferred)

- Premium: ask "是否有一辆想拿掉或调整？" when bill_sent but no remove_vehicle at T2 — **reverted:** breaks 2-turn scenarios (SIM6, SIM13, R6).
- Payment: ask "截图发了吗" when paid but no screenshot at T2 — **reverted:** breaks 2-turn scenarios (SIM7, SIM9, R1).

### Small Fixes Applied

- **None.** Implemented premium/payment ask; ran guardrail; found 5 Simulation Assistant scenarios (SIM6, SIM7, SIM9, SIM13, R1, R6) would never hand off. Reverted. Added docstring in triage.py documenting deferred fix-next.

### Whether Loop 2 Was Worth It

**Yes.** Evidence-based decision: fix would improve 3-turn flows but break 2-turn flows. Deferred with clear fix-next (scope to 3+ turn only).

---

## 7. Iteration Loop 3

### What Was Retested

- Full guardrail after revert
- Handoff timing pack

### What Improved

- N/A (no code change kept).

### What Still Remained Weak

- HT3, HT9, HT10: T2 handoff when T3 adds more. Documented acceptable-for-trial; fix-next with 3+ turn scope.

### Whether Redeploy Happened

- **No.** No logic change; only docstring + control docs. Backend already has HT8 fix from prior audit.

### Whether Loop 3 Was Worth It

**Yes.** Confirmed no regressions; guardrail PASS.

---

## 8. Validation Summary

| Check | Result |
|-------|--------|
| `bash scripts/guardrail_inbox_triage.sh` | PASS |
| `run_handoff_timing_simulations.py` | 10/10 pass |
| `run_multi_turn_simulations.py` | 41/41 strong |
| `run_simulation_assistant_scenarios.py` | 27/27 normal |
| `run_broker_trial_stress_simulations.py` | 8/8 pass |

**Limitations:** Premium/payment "one more ask" would require 3+ turn scoping to avoid breaking 2-turn flows.

---

## 9. Deployment / Release Judgment

| Component | Changed | Redeploy needed |
|-----------|---------|-----------------|
| Backend | triage.py (docstring only) | No |
| Config | handoff_timing_simulations.json | No (reverted) |
| Docs | 7 control docs + this report | N/A |

**Founder can inspect now:** Yes — same as prior audit. Run guardrail; run handoff timing pack; test HT8 on Vercel.

---

## 10. Founder Manual Test List

| # | Test Case | What to Expect | What to Watch |
|---|-----------|----------------|---------------|
| 1 | **Add-car + garaging (HT8)** | 加车 2024 X5 → 90210 下周提车 对了 garaging proof 是什么 | Answer garaging + handoff T2; no driver ask |
| 2 | **Premium 3-turn (HT3)** | 续保涨了好多 → 账单发你了 → 其中一辆去掉会便宜吗 | T2 handoff; T3 would append |
| 3 | **Payment 3-turn (HT9)** | payment failed 怎么办 → 我昨天付了 → 截图发你微信了 | T2 handoff; T3 would append |
| 4 | **Add-car + driver T3 (HT1)** | 加车 2024 Tesla Model Y → 90210 下周提车 → 对了 是我老婆开 | Ask driver T2; handoff T3 |
| 5 | **Talk to agent (HT4)** | 联系人工 | Handoff T1 |

**Directly verified in production:** N/A (no redeploy).  
**Verified by local tests:** All 10 handoff timing + guardrail.  
**Still needs founder manual confirmation:** HT8 on Vercel (from prior deploy).

---

## 11. Final Judgment

- **Biggest gain:** Regression pack strengthened; fix-next clearly scoped (3+ turn only); no overcorrection.
- **Biggest remaining weakness:** Premium/payment T2 handoff when T3 adds remove-vehicle or screenshot; fix-next when 3+ turn scope feasible.
- **Whether product is safer for real broker trial:** Yes. HT8 fix from prior audit remains; no regressions; fix-next documented.
- **Best next step:** Run real trial; use observation log; implement premium/payment ask with 3+ turn scope if evidence supports.

---

## 12. 中文宏观总结

**为什么现在做这轮：** 上一轮 handoff timing audit 修了 HT8；HT3/9/10 列为 acceptable-for-trial，fix-next 为 premium/payment 多问一轮。本 sprint 系统评估是否实施该 fix-next。

**主要发现了什么：** Premium/payment 在 T2 多问一轮（"是否有一辆想拿掉" / "截图发了吗"）会改善 HT3/9/10，但会破坏 2-turn 场景（SIM7, SIM9, R1, R6, SIM13）— 这些场景将永远不 hand off。

**修了什么：** 无。实施后复现，确认会破坏 2-turn；回滚；在 fix-next 中注明需限定为 3+ turn 才可实施。

**现在最该继续看什么：** 跑真实 trial；用 observation log；若证据支持，再实施 premium/payment 多问一轮（限定 3+ turn）。

---

## 13. COPY/PASTE FOUNDER BLOCK

```
Handoff Timing Regression + Redeploy Sprint — Founder Summary

Biggest timing finding: Premium/payment "one more ask" (ask remove-vehicle when bill_sent, ask screenshot when paid) would improve 3-turn flows but breaks 2-turn flows. Deferred; fix-next: scope to 3+ turn only.

Biggest remaining weakness: HT3, HT9, HT10 — T2 handoff when T3 adds remove-vehicle or screenshot. Acceptable-for-trial; T3 would append.

Redeploy needed: No. No logic change.

What Andy should test on Vercel: (1) bash scripts/guardrail_inbox_triage.sh — PASS. (2) Add-car + garaging: 加车 2024 X5 → 90210 下周提车 对了 garaging proof 是什么 — verify answer + handoff. (3) Premium 3-turn: 续保涨了 → 账单发你了 → 其中一辆去掉会便宜吗 — observe T2 handoff, T3 append.
```

---

## 14. REQUIRED SHORT OVERVIEW

### 为什么做这件事

Handoff 可能在客户说完之前发生；上一轮修了 HT8；本 sprint 评估 premium/payment fix-next 是否可实施。

### 主要用了什么方法/技术

7 份控制文档；10 条 handoff timing 模拟；baseline audit；Loop 1–3：simulate → classify → implement → revert（因破坏 2-turn）→ document fix-next。

### 这轮最大的发现

Premium/payment 在 T2 多问一轮会改善 3-turn，但破坏 2-turn 场景。需限定 3+ turn 才可实施。

### 现在最该修什么

fix-next：Premium/payment 多问一轮，限定为 3+ turn（即 T2 时已有 ≥1 条 prior customer message）。

---

*End of Report*
