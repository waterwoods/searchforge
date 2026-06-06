# Case Handoff Mainline Sprint Report

**Sprint:** Case Handoff Mainline  
**Date:** 2026-03-13  
**Scope:** Customer Entry, Broker Workbench, Simulation Assistant — case handoff clarity

---

## 1. Handoff blueprint summary

### Why current output still feels scattered
- Important info split across 6+ cards (Case created, Case Report, Where this case stands, Client prep, Draft, Full conversation)
- Case meaning not obvious at first glance — Customer Entry handoff showed only last message, no case focus
- "What changed recently" buried at bottom of Case Report
- Human confirmation separated from "Your next move"
- Simulation Assistant Case Report lacked case focus and one-line summary

### What good handoff should contain
1. Case focus (Add car quote, Premium review, Missing document, etc.)
2. Status / readiness (Ready for handoff vs Collecting)
3. One-line handoff summary
4. Broker next move
5. Human confirmation (when needed) — grouped with next move
6. Collected / Still needed
7. What changed recently (when append)
8. Conversation — secondary

### What should be primary vs secondary
**Primary:** What this case is, whether it is ready, what to do next, what to verify.  
**Secondary:** Detailed replay, client prep, draft, "Where this case stands" tracking.

---

## 2. Current handoff audit

| Surface | Classification | Strongest | Weakest |
|---------|----------------|-----------|---------|
| **Broker Workbench** | Usable but fragmented | Collected/Still needed chips, broker_next_step | 6+ separate cards; human confirmation at bottom |
| **Customer Entry** | Too scattered at handoff | Handoff-ready card, "查看工作台" button | No case focus or one-line summary before switch |
| **Simulation Assistant** | Usable but incomplete | Case Report with next move, collected, still needed | No case focus label, no one-line summary |

**Biggest handoff clarity gaps:**
1. Workbench: too many conceptual boxes; human confirmation easy to miss
2. Customer Entry: handoff moment not explicit — user switches without knowing "what this case is"
3. Simulation Assistant: outcome less office-like without case focus and one-liner

---

## 3. Handoff structure design

**One unified "Case handoff" block** (replaces fragmented Case Report + status card):

| Order | Section | Content |
|-------|---------|---------|
| 1 | Context | Case created/reopened; Resume here (when reopened); What changed recently (when append) |
| 2 | Case focus | Blue tag: Add car quote, Premium review, Missing document, etc. |
| 3 | Status | Ready for handoff, Collecting info, Your move, Same-day action |
| 4 | One-line summary | "Ready for handoff: Add car quote — Collect vehicle details, confirm delivery, then quote" |
| 5 | Your next move | One operational sentence |
| 6 | Human confirmation | Highlighted block when present — verify before acting |
| 7 | Collected / Still needed | Green / orange chips |
| 8 | Response window / tracking | Secondary |

**Rationale:** Same structure across all surfaces; human confirmation and "what changed" moved up; fewer boxes.

---

## 4. Implementation changes made

| File | Change |
|------|--------|
| `docs/CASE_HANDOFF_MAINLINE_BLUEPRINT.md` | **Created.** Blueprint: why scattered, what good handoff contains, primary vs secondary, implementation principles. |
| `ui/src/pages/UnifiedIntakePage.tsx` | **Customer Entry:** Added case focus tag + one-line summary to handoff moment before "查看工作台". **Workbench:** Merged "Case created/reopened" status card into Case Report; renamed to "Case handoff"; reordered: context → case focus → status → one-liner → next move → human confirmation (highlighted block) → collected/still needed; moved "What changed recently" to top when present. |
| `ui/src/components/simulation/SimulationAssistant.tsx` | Added `inferCaseFocus()` and `getOneLiner()`; Case Report → "Case handoff"; added case focus tag, one-line summary, human confirmation block; same structure as Workbench. |
| `scripts/unified_intake_smoke_check.sh` | Updated step 15d: "Case Report" → "Case handoff". |

---

## 5. Office-style usefulness check

| View | Can understand in &lt;10s? | Can act without rereading chat? | Human-confirm boundary obvious? | Feels like handoff object? |
|------|----------------------------|----------------------------------|---------------------------------|----------------------------|
| **Founder** | Yes — case focus + one-liner first | Yes — next move prominent | Yes — gold block when present | Yes — one main block |
| **Broker/assistant** | Yes — same structure | Yes — collected/still needed visible | Yes — grouped with next move | Yes — fewer cards |
| **Simulation/demo** | Yes — case focus + one-liner | Yes — mirrors Workbench | Yes — human confirm block | Yes — office-style outcome |

---

## 6. Validation results

| Check | Result |
|-------|--------|
| `cd ui && npm run build` | **Pass** |
| `run_inbox_triage_scenarios.py` | **Pass** (49/49) |
| `run_multi_turn_simulations.py` | **Pass** (38/38 Strong) |
| `audit_state_field_accuracy.py` | **Pass** (7/7) |
| `guardrail_inbox_triage.sh` | **Pass** |

---

## 7. Refinement loop

**Not needed.** Validation passed; handoff structure is consistent across surfaces. No further refinement in this sprint.

---

## 8. Final evaluation

| Question | Answer |
|----------|--------|
| Is the case now more like a real handoff object? | **Yes.** One main "Case handoff" block; case focus + one-liner at top; human confirmation grouped with next move. |
| Is it easier for brokers/assistants to act? | **Yes.** Fewer cards to scan; "what changed" and human confirmation more prominent. |
| Is it better for founder debugging? | **Yes.** Same structure in Simulation Assistant; case focus + one-liner visible in every surface. |
| Is the product more sellable to small clients? | **Yes.** Output feels like office handoff, not debug output. |
| **Biggest handoff gain** | **Unified handoff block** — one primary card instead of 6+; case focus + one-liner at top; human confirmation grouped with next move. |
| **Biggest remaining weakness** | **"Where this case stands"** still a separate card; tracking (waiting on, due date) could be folded into handoff block for reopened cases. Defer for now. |

**Verdict:** **Good first handoff mainline.** Case output is now clearer and more office-like. Not perfect, but a strong step forward.

---

## 9. Redeploy readiness

**Frontend only.** Changes are in `ui/` and `docs/`. No backend changes. Redeploy frontend (Vercel) to pick up changes.

---

## 10. 中文宏观总结

- **现在最终结果是不是更像正式交接 case 了？** 是。三个表面（客户入口、工作台、Simulation Assistant）都用同一套「Case handoff」结构，case focus 和 one-liner 在最上面。
- **哪些地方最像办公室工具了？** 工作台合并成一个主 handoff 卡片；客户入口在「查看工作台」前显示 case focus 和 one-liner；Simulation Assistant 的 outcome 和 Workbench 一致。
- **陈奎和助手会不会更容易接手？** 会。一眼能看到 case focus、next move、human confirmation；collected/still needed 更集中。
- **我们开发时会不会更容易检查了？** 会。Simulation Assistant 的 Case handoff 和 Workbench 结构一致，demo/QA 更直观。
- **还剩下最大的 handoff 缺点是什么？** 「Where this case stands」还是单独卡片；reopened 的 tracking 可以进一步并入 handoff block，暂不处理。
- **下一步该做什么？** 跑一次完整 demo 验证；如需要，可把「Where this case stands」并入 handoff block 作为可选 refinement。

---

## 11. COPY/PASTE CASE HANDOFF BLOCK

**What the new handoff structure is:**
- One "Case handoff" block (replaces fragmented Case Report + status card)
- Order: context → case focus → status → one-liner → Your next move → Human confirmation (when needed) → Collected → Still needed
- Same structure in Customer Entry handoff moment, Broker Workbench, Simulation Assistant

**What got easier to understand:**
- Case focus and one-line summary at top
- Human confirmation grouped with next move
- "What changed recently" moved up when present

**What got easier to act on:**
- Fewer cards to scan
- Broker next move more prominent
- Trust boundary (human confirmation) harder to miss

**Biggest remaining weakness:**
- "Where this case stands" still separate; could be merged for reopened cases

**Redeploy needed:** Frontend only (Vercel)

**What to do after this mainline:**
- Run full demo walkthrough
- Optional: merge "Where this case stands" into handoff block for reopened cases
- Continue using same handoff structure for any new case surfaces
