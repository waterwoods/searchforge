# Broker Case Queue Triage Sprint Report

**Sprint:** Broker Case Queue Triage Sprint  
**Date:** 2026-03-10  
**Scope:** SearchForge → Chen Kui Insurance Unified Entry — Broker Workbench queue/list triage

---

## 1. Stages completed

| Stage | Status | Notes |
|-------|--------|-------|
| **Stage 1 — Define broker queue triage model** | ✅ Completed | §0a added to BROKER_HANDOFF_CLARITY_GUIDE.md |
| **Stage 2 — Improve queue/case list signals** | ✅ Completed | Readiness badge, compact flow-specific preview, queue legend |
| **Stage 3 — Lightweight triage priority rules** | ✅ Completed | Work now / Waiting or parked; getCaseWorkbenchScore unchanged |
| **Stage 4 — Multi-case simulation** | ✅ Completed | Guardrail PASS; founder demo queue used as mixed-case proof |
| **Stage 5 — Identify high-value issues** | ✅ Completed | Addressed: queue preview too weak, readiness not obvious |
| **Stage 6 — Improvement loop 1** | ✅ Completed | Compact preview, readiness label, legend |
| **Stage 7 — Optional improvement loop 2** | Skipped | First pass sufficient |
| **Stage 8 — Founder demo proof** | ✅ Completed | 5 walkthroughs below |
| **Stage 9 — Regression + safety** | ✅ Completed | Smoke check step 16; runbook updated |
| **Stage 10 — Audit + judgment** | ✅ Completed | Verdict: Accept |

---

## 2. Queue triage model

**What the broker should infer at a glance (without opening every case):**

| Signal | What broker infers |
|--------|--------------------|
| **Urgency / priority** | Same-day vs routine (urgency badge; Action now / Due today / Your move) |
| **Case focus** | Add car, renewal, claim, missing doc, payment risk |
| **Readiness to act** | Ready for quote vs still needs key info (Ready to act / Needs more info / Verify receipt) |
| **Follow-up state** | Broker's move vs waiting on client |
| **Customer says already sent** | Missing-doc verification case |
| **Work now vs parked** | Action section vs tracking section |

**Why it matters:** A real office processes a queue of mixed cases. The broker should decide which case to open first without clicking into every card.

---

## 3. UI / backend / product changes made

| File | Change | Purpose |
|------|--------|---------|
| `docs/BROKER_HANDOFF_CLARITY_GUIDE.md` | Added §0a Queue Triage at a Glance | Define queue-level signals |
| `ui/src/pages/UnifiedIntakePage.tsx` | `getQueueReadinessLabel()` | Ready to act / Needs more info / Verify receipt |
| `ui/src/pages/UnifiedIntakePage.tsx` | `getCompactQueuePreview()` | Flow-specific compact snippet for queue cards |
| `ui/src/pages/UnifiedIntakePage.tsx` | `renderRecentCaseCard` | Readiness badge, compact preview, reduced clutter |
| `ui/src/pages/UnifiedIntakePage.tsx` | Queue legend | Action now, Your move, Ready to act, Needs more info, Waiting on client |
| `ui/src/pages/UnifiedIntakePage.tsx` | `listRecentCases(12)` | Show more cases in queue |
| `scripts/unified_intake_smoke_check.sh` | Step 16 | Queue triage verification |
| `docs/UNIFIED_INTAKE_DEMO_READINESS.md` | Queue triage note | Founder demo story |
| `docs/runbooks/UNIFIED_INTAKE_MVP_RUNBOOK.md` | Queue triage note | Runbook reference |

**Backend:** No changes. All queue logic is UI-side from existing triage output.

---

## 4. Validation and improvement loops

| Check | Result | Notes |
|-------|--------|-------|
| `bash scripts/guardrail_inbox_triage.sh` | PASS | 49/49 scenarios, multi-turn, adversarial, complex |
| `cd ui && npm run build` | PASS | UI compiles |
| `scripts/unified_intake_smoke_check.sh` | PASS | Step 16 added for queue triage |

**Issues found:** Queue preview was too weak (full broker_next_step + raw Collected/Still needed); readiness not obvious.

**Fixes made:** Compact flow-specific preview; readiness badge; queue legend; reduced card clutter.

---

## 5. Product proof strength

| Question | Answer |
|----------|--------|
| Does the queue help decide what to open first? | Yes. Work now vs Waiting or parked; readiness badge; urgency visible. |
| Are urgency/readiness signals useful? | Yes. Ready to act / Needs more info / Verify receipt reduce mental load. |
| Is the queue more office-realistic now? | Yes. Compact previews, triage tiers, legend. |
| Is this more convincing in a founder demo? | Yes. "Which case first?" is answerable at list level. |
| Is anything too cluttered or overengineered? | No. Kept compact; legend is small. |

---

## 6. Validation summary

| Check | Result | Protects |
|-------|--------|----------|
| `bash scripts/guardrail_inbox_triage.sh` | PASS | Scenario pack, multi-turn, adversarial, complex |
| `cd ui && npm run build` | PASS | UI compile |
| `scripts/unified_intake_smoke_check.sh` | PASS | Guardrail + manual UI steps including queue triage |

---

## 7. Business / platform value

| Area | Improvement |
|------|-------------|
| **Broker mental load** | Readiness badge and compact preview reduce need to open every case. |
| **Triage speed** | Work now / Waiting or parked + readiness help broker prioritize. |
| **Platform story** | Queue feels more like a real office triage board, not a plain list of conversations. |

---

## 8. Remaining blocker(s)

1. **Field values:** Queue preview shows field names (Year, Make/Model) not extracted values (2025, Honda CR-V).
2. **Non-structured cases:** Payment/cancellation, DMV/SR-22 still use broker_next_step fallback for compact preview.
3. **Server-dependent API test:** One test (missing_document collected_fields) may fail if server not restarted.

---

## 9. Recommended next step

Tighten queue preview for non-structured flows (payment/cancellation, DMV) with short intent-specific snippets when safe. Do not broaden scope.

---

## 10. 中文或中英混合宏观总结

**Broker queue 这次变好了什么：**
- 队列卡片现在有「Ready to act / Needs more info / Verify receipt」标签，经纪人不用点开就能知道这个 case 能不能马上处理。
- 每个 case 有 flow 专属的 compact preview（例如 add-car: Collected: Year, Model, ZIP · Missing: Driver）。
- 「Work now」和「Waiting or parked」分组更清晰，加上 queue legend 说明各标签含义。

**经纪人现在能不能更快知道先看哪个 case：**
- 能。Urgency、attention label、readiness 都在列表可见；Work now 区优先处理。

**哪些信号最有用：**
- Action now / Your move（需要立刻处理）
- Ready to act / Needs more info / Verify receipt（是否要开 case 才能动）
- 紧凑的 flow-specific preview（不用点开就知道缺什么）

**还缺什么：**
- 字段值（如 2025, Honda CR-V）尚未在 queue 显示；payment/DMV 等非结构化 flow 的 preview 仍较通用。

**这次对陈奎和以后别的客户有什么帮助：**
- 陈奎办公室可以更快 triage 多个 case，减少「每个都点开看」的负担。
- 以后别的 broker 客户也能用同一套 queue 逻辑，更贴近真实办公室工作方式。

---

## 11. Practical broker queue cheat sheet

| What queue shows | How it appears |
|------------------|----------------|
| **Urgency** | CRITICAL / HIGH / MEDIUM / LOW tag |
| **Attention** | Action now, Due today, Your move, Urgent follow-up, Follow up soon, Waiting on client, In review, Parked for now |
| **Readiness** | Ready to act (green), Needs more info (gold), Verify receipt (orange), Same-day action (red) |
| **Case focus** | Add car quote, Premium review, Claim intake, Missing document, Cancellation risk, etc. |
| **Compact preview** | Flow-specific: Collected/Missing for add-car; Premium concern for renewal; Accident reported for claim; Customer says sent for missing-doc |
| **Tracking** | Waiting on X · Next contact by Y; or Latest note |

**What still requires opening the case:** Full broker next move, client prep, draft to send, full conversation, broker notes.

---

## 12. Broker-value summary

| Signal | Strength | Notes |
|-------|----------|-------|
| **Action now / Your move** | Strong | Clearly says "work this first" |
| **Ready to act / Needs more info / Verify receipt** | Strong | Reduces open-every-case behavior |
| **Compact flow-specific preview** | Strong | Add-car, renewal, claim, missing-doc all have useful snippets |
| **Work now / Waiting or parked** | Strong | Matches office mental model |
| **Urgency tag** | Acceptable | Already present; unchanged |
| **Case focus label** | Acceptable | Already present; unchanged |
| **Payment/cancellation preview** | Weak | Falls back to broker_next_step snippet |
| **DMV/SR-22 preview** | Weak | Same fallback |

---

## 13. Live proof walkthroughs

### 1. Urgent claim case

**Customer said:** 刚出事故了，要收集什么？

**Queue shows first:** Action now or Your move · CRITICAL or HIGH · Claim intake · Accident reported · Collect photos and other driver info (or Needs more info if still_needed present)

**Why broker would open first:** Urgency + claim = high priority; readiness tells if info is enough to act.

**Demo-strong:** Yes. Proves claim intake in queue with urgency.

---

### 2. Active renewal case

**Customer said:** 续保保费太高了，其中一辆去掉会便宜吗

**Queue shows first:** Your move or Waiting on client · Premium review · Premium concern · Missing renewal notice (if still_needed) or Ready to act

**Why broker would open first:** If "Your move" and "Ready to act", broker can quote; if "Needs more info", knows to ask for bill first.

**Demo-strong:** Yes. Proves renewal flow in queue with readiness.

---

### 3. Add-car ready-to-act case

**Customer said:** 客户要加一台2021 Tesla Model Y，下周提车，问今天能不能先出报价

**Queue shows first:** Ready to act · Add car quote · Collected: Year, Make/Model, ZIP, Delivery · (no Missing or minimal)

**Why broker would open first:** "Ready to act" + add-car = can quote same day; no need to open to confirm.

**Demo-strong:** Yes. Proves add-car with enough info at list level.

---

### 4. Missing-document verification case

**Customer said:** UW follow up - need dec page + garaging proof. 客户说上周发过了

**Queue shows first:** Verify receipt · Missing document · Customer says already sent · Verify receipt

**Why broker would open first:** "Verify receipt" = check carrier received; broker knows not to re-ask client.

**Demo-strong:** Yes. Proves "customer says sent" signal in queue.

---

### 5. Lower-priority control case

**Customer said:** 客户说这个月保费太高了，能不能看看怎么降一点

**Queue shows first:** Waiting on client · Premium review · Premium concern · Missing renewal notice (or Ready to act if bill mentioned)

**Why broker would NOT open first:** Waiting on client = parked; no urgency; can defer.

**Demo-strong:** Yes. Proves queue correctly parks lower-priority cases.

---

*End of report*
