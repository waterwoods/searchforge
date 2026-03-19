# Today Sprint Plan Review

**Sprint:** Today Plan Review + Mainline Lock  
**Date:** 2026-03-09  
**Role:** Planning reviewer / sprint architect

---

## 1. What should remain in scope

| Item | Why |
|------|-----|
| **Lock mainline** | Continuous Conversational Intake sprint is done. Lock `CONTINUOUS_CUSTOMER_INTAKE_MVP.md`, `MATURE_INTAKE_SKELETON.md`, and current triage flow as canonical. No doc churn today. |
| **Validate 3 live chains end-to-end** | BMW X5/new car, payment failed, English notice/DMV-SR22. These are the highest-value Chen Kui chains. Run walkthroughs; fix only what breaks. |
| **Broker handoff polish (lightweight only)** | If broker case card can show a one-line "Collected: year, zip, delivery" for add-car without new backend structs, do it. Otherwise defer. |
| **Demo readiness** | `unified_intake_smoke_check.sh` + `run_inbox_triage_scenarios.py` pass. Demo script mentions the 3 focus flows. |

---

## 2. What should be removed or deferred

| Item | Reason |
|------|--------|
| **"Collected from conversation" structured summary** | Sprint report deferred `progressive_answers` struct. Do not add key-value extraction today. Broker already sees full `source_text`; that is enough for sellable demo. |
| **Expanding beyond 3 scenarios** | 29 scenario pack is for regression. Today: only BMW X5, payment failed, notice/DMV-SR22. Do not tune for S1–S29. |
| **OCR, CRM, auth, inbox sync, automation** | Explicitly out of scope. Do not even discuss. |
| **Broker workbench feature work** | Customer Entry is the sellable surface. Workbench polish (status, notes, waiting_on) is secondary. Do not mix goals. |
| **New intent categories or triage logic** | Mature skeleton covers the 3 flows. Triage already has add-car, payment_lapse_expiration, customer_question. No new branches. |

---

## 3. Corrected execution plan

**Stage 1 — Lock mainline (30 min)**  
- Mark `docs/CONTINUOUS_CUSTOMER_INTAKE_MVP.md` and `docs/MATURE_INTAKE_SKELETON.md` as locked for today.  
- Run `guardrail_inbox_triage.sh` and `unified_intake_smoke_check.sh`. Fix only blocking failures.  
- No new design docs.

**Stage 2 — Validate 3 live chains (45 min)**  
- Walk through each chain manually in UI:  
  1. **BMW X5:** "I bought a new BMW X5, how much is insurance?" → system asks year/model/zip → customer replies "2024, 90210, next week" → handoff.  
  2. **Payment failed:** "这个英文 notice 说 payment failed，我现在怎么办？" → system asks notice/screenshot → "我发了截图" → handoff.  
  3. **Notice/DMV-SR22:** "客户发来一张DMV的信，问这是什么意思？" → system asks full notice or context → customer adds info → handoff.  
- If any chain breaks (wrong ask, wrong handoff, wrong broker_next_step), fix in triage or reply strategy. Do not add features.

**Stage 3 — Broker handoff (optional, 20 min)**  
- If broker case card can show a short "Collected: …" line by parsing `source_text` in UI only (no backend change), add it.  
- If it requires backend `progressive_answers` or new API fields, skip. Defer to next sprint.

**Stage 4 — Demo readiness (15 min)**  
- Ensure `docs/UNIFIED_INTAKE_DEMO_READINESS.md` or demo script lists the 3 focus flows.  
- Run `prepare_unified_intake_founder_demo.py` if needed.  
- Final smoke: `unified_intake_smoke_check.sh` PASS.

---

## 4. Success criteria for today

| Criterion | How to verify |
|-----------|---------------|
| **3 chains work** | Manual walkthrough: each chain reaches handoff with correct broker_next_step and full conversation in source_text. |
| **No scope creep** | No new routes, no new triage categories, no progressive_answers struct. |
| **Guardrails pass** | `guardrail_inbox_triage.sh`, `unified_intake_smoke_check.sh` PASS. |
| **Demo script ready** | Andy can run the 3 flows in under 5 minutes for a founder demo. |

---

## 5. Risks to watch

| Risk | Mitigation |
|------|------------|
| **Overbuilding "Collected" summary** | UI-only, no backend. If not trivial, defer. |
| **Tuning for full scenario pack** | Focus only on the 3 chains. Scenario pack is regression, not today's target. |
| **Mixing customer entry and workbench** | Customer Entry = primary. Workbench = "view case, copy draft." No new workbench features. |
| **Adding "one more thing"** | Strict: if it's not in Stage 1–4, it's out. |

---

## 6. Recommended next implementation prompt

```
Today: Mainline Lock + 3-Chain Validation

1. Lock docs: CONTINUOUS_CUSTOMER_INTAKE_MVP.md, MATURE_INTAKE_SKELETON.md. No edits unless fixing errors.

2. Run guardrail_inbox_triage.sh and unified_intake_smoke_check.sh. Fix blocking failures only.

3. Validate 3 live chains in UI:
   - BMW X5 / new car quote (add-car → ask year/zip/delivery → handoff)
   - Payment failed / cancellation risk (payment_lapse → ask notice/screenshot → "我发了" → handoff)
   - English notice / DMV-SR22 (customer_question → ask full notice → handoff)

4. Optional: If broker case card can show "Collected: …" from source_text in UI only (no backend change), add one line. Otherwise skip.

5. Update demo script to list these 3 flows. Run prepare_unified_intake_founder_demo.py. Final smoke: unified_intake_smoke_check.sh PASS.

Constraints: No new triage categories, no progressive_answers struct, no workbench features, no scope beyond these 3 chains.
```

---

*End of plan review*
