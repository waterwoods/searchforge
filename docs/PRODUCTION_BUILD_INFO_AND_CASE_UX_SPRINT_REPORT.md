# Production Build-Info Check + Final Case UX Clarity Report

**Sprint:** Production Build-Info Check + Final Case UX Clarity Sprint  
**Date:** 2026-03-13  
**Mode:** Focused execution, ~30–50 min budget

---

## 1. Build info production check

| Item | Result |
|------|--------|
| **Production URL** | https://ui-smoky-beta.vercel.app/workbench/unified-intake |
| **Visible** | **Yes** — Release Identity bar is live in production |
| **Location** | Top-right of header bar, next to KpiBar (P95 Latency, Recall, QPS) |
| **What is shown** | `v0.1.0` · `Built: 2026-03-12 10:35 PM PT` · short commit hash · `PRODUCTION` (or `dev`) |
| **Redeploy needed** | **No** — feature is already deployed and visible |

**Verification method:** Browser screenshot of production frontend confirmed the build info bar in the header.

---

## 2. Case UX audit

| Surface | Strength | Weakness |
|---------|----------|----------|
| **Broker Workbench / Customer Entry** | Full Case Report with focus, status, next move, collected/still needed, human confirmation | Tags scattered; no one-line handoff summary; "What changed" was small italic text |
| **Simulation Assistant** | Compact Case Report after run completes | No case focus; Collected/Still needed inline (less scannable) |

**Biggest clarity gap:** The Case Report lacked a one-line handoff summary. Brokers had to scan tags + next move to understand "what this case is and what to do" in under 10 seconds.

---

## 3. Chosen improvements

| Improvement | Why |
|-------------|-----|
| **One-line handoff summary** | "Ready for handoff: Add car quote — send quote after broker review" or "Collecting: Payment risk — need DL, payment link" — instant scan |
| **Reordered Case Report** | Status tags first, then one-liner, then Next move, then Collected/Still needed — clearer hierarchy |
| **"What changed recently" box** | When `follow_up_added`, show a subtle blue box instead of small italic text — more visible |
| **Human confirmation wording** | "Verify before acting: VIN, primary driver" instead of mixed 请人工确认 — consistent, actionable |
| **Case Report subtitle** | "— handoff summary, collected, next move" — tighter than "what this case is, what we collected, what to do next" |
| **Simulation Assistant** | Collected / Still needed as block labels (Collected, Still needed) for consistency |

---

## 4. Implementation changes made

| File | Change |
|------|--------|
| `ui/src/pages/UnifiedIntakePage.tsx` | Added `getCaseReportOneLiner()` helper; restructured Case Report: status → one-liner → next move → collected/still needed → "What changed recently" box (when present) → human confirmation; tightened subtitle and human-confirmation copy |
| `ui/src/components/simulation/SimulationAssistant.tsx` | Collected / Still needed with block labels for consistency |

---

## 5. Before vs after

| Aspect | Before | After |
|--------|--------|-------|
| **Top summary** | Tags only; no one-line | "Ready for handoff: Add car quote — send quote…" or "Collecting: Payment risk — need DL…" |
| **What changed** | Small italic text | Blue box with "What changed recently" + explanation |
| **Human confirmation** | "请人工确认：…" or "AI collected… verify" | "Verify before acting: VIN, primary driver" |
| **Case Report flow** | Case focus inline with tags | Status → one-liner → next move → collected/still needed |

**What still remains weak:** The "Where this case stands now" and "Keep this case moving" sections are separate cards — could be merged in a future pass for a single "case status" block. Not done in this sprint to avoid scope creep.

---

## 6. Validation summary

| Check | Result |
|-------|--------|
| `run_inbox_triage_scenarios.py` (LLM_GENERATION_ENABLED=0) | 49/49 passed |
| `run_multi_turn_simulations.py` (LLM_GENERATION_ENABLED=0) | 38 strong, 0 weak |
| `audit_state_field_accuracy.py` | 7/7 passed |
| `guardrail_inbox_triage.sh` | PASS |
| `cd ui && npm run build` | Success |

---

## 7. Redeploy readiness

| Component | Redeploy needed |
|----------|-----------------|
| **Frontend** | **Yes** — Case Report and Simulation Assistant UI changes |
| **Backend** | No |

**Command:** `cd ui && vercel --prod`

---

## 8. Final verdict

**Strong improvement.** Build info is confirmed live in production. Case Report is clearer: one-line handoff summary, reordered flow, and a visible "What changed recently" box make the handoff moment easier to scan. Human confirmation wording is more consistent. Remaining weakness: "Where this case stands" and "Keep this case moving" are still separate; a future consolidation would help but is out of scope for this sprint.

---

## 9. 中文宏观总结

- **版本号 / build 信息线上到底有没有？** 有。v0.1.0、Built 时间（LA）、commit 短 hash、环境标签都在 header 右上角，已确认。
- **现在最终 case 展示是不是更清楚了？** 是。加了「Ready for handoff: X — Y」或「Collecting: X — Y」一行总结，Case Report 顺序更清晰，「What changed recently」用蓝框突出。
- **哪个地方最像正式办公工具了？** Case Report 卡片：状态 → 一行总结 → 下一步 → 已收集 / 仍缺 → 人工确认，结构更像正式 case handoff。
- **还剩下最大的缺点是什么？** 「Where this case stands」和「Keep this case moving」还是两张卡，未来可以合并成一个 case 状态块。
- **下一步要不要重新发布前端？** 要。`cd ui && vercel --prod` 把 Case Report 改进发上去。

---

## 10. COPY/PASTE SUMMARY BLOCK

```
Production Build-Info + Case UX Sprint — Summary
=================================================
Build info: LIVE in production (v0.1.0, Built: LA time, commit, env)
Strongest case surface: Broker Workbench Case Report
Biggest case UX improvement: One-line handoff summary + reordered flow + "What changed recently" box
Biggest remaining weakness: "Where this case stands" and "Keep this case moving" still separate cards
Redeploy needed: Yes — frontend only (cd ui && vercel --prod)
```
