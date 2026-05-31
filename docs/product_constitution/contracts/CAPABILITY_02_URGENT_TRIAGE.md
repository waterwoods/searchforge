# Capability Contract 02 — Urgent Message Triage

**Capability:** Urgent Message Triage  
**Version:** V1 Ratified  
**Date:** 2026-05-31  
**Maps to:** Capability Map V1 §2

---

## SECTION 1 — Purpose

Why this capability exists.

Classify customer message intent, urgency, and extract structured facts from unstructured text so brokers stop re-reading entire WeChat threads. Surfaces **same-day cancellation risk** and routes cases to correct issue categories.

This is the **engine** of Unified Intake. P10/P11: guardrail 13/13 PASS; triage is trial-ready.

---

## SECTION 2 — Primary User

Who uses it.

| User | Usage |
|------|-------|
| **Broker owner** | Reads triage output on case card after paste |
| **Office assistant** | Same — triage runs automatically on paste |
| **Founder/operator** | Runs guardrail regression before demo/trial |

End customer does not interact with triage directly.

---

## SECTION 3 — Inputs

What enters the capability.

| Input | Requirement |
|-------|-------------|
| Raw message text | Pasted without cleanup (WeChat, email, notice) |
| Optional conversation context | Prior case messages on reopen |
| Optional broker context | Short note with paste (if provided) |
| Scenario guardrail pack | 13 regression scenarios for QA |

---

## SECTION 4 — Outputs

What must come out.

Per `BROKER_INBOX_TRIAGE_STANDARD.md` — **6-field output** always present:

| Field | Broker-facing label |
|-------|---------------------|
| `issue_category` | Case focus (mapped via CUSTOMER_LANGUAGE_GUIDE) |
| `urgency` | Same-day / 24h / routine |
| `manual_followup_needed` | Human confirmation flag |
| Extracted facts | Feeds Collected / Still needed |
| `client_reply_draft` | Passed to Structured Case Record |
| Triage metadata | Category confidence, guardrail trace (operator only) |

**Categories:** 10+ issue types including cancellation, payment failed, missing document, add-car, and scenario pack coverage.

---

## SECTION 5 — Success Metrics

How success is measured.

| Metric | Target | Source |
|--------|--------|--------|
| Guardrail regression | 13/13 PASS | `guardrail_inbox_triage.sh` |
| Scenario pack match | Categories align with STANDARD_SCENARIO_PACKAGE | Config validation |
| Cancellation urgency | Same-day flag on cancellation scenarios | Guardrail + demo queue |
| Real-message accuracy | Broker accepts triage without full re-read | Day 7 observation log |
| Latency | First triage ≤30s with loading message | P11 workbench #10 |

---

## SECTION 6 — Acceptance Criteria

How we know it works.

- [ ] Every paste produces complete 6-field output  
- [ ] `guardrail_inbox_triage.sh` PASS (13/13) before any demo/trial  
- [ ] Cancellation scenarios surface same-day urgency  
- [ ] Missing document scenarios populate Collected / Still needed correctly  
- [ ] Mixed Chinese/English messages handled without crash  
- [ ] Issue categories map to broker-facing Case focus labels (not raw engineer names)  
- [ ] Triage failure returns actionable error (not 503 silent fail)  

---

## SECTION 7 — Current State

Score **0–100** today.

### Score: **85 / 100**

| Dimension | Score | Notes |
|-----------|-------|-------|
| Guardrail regression | 95 | 13/13 PASS |
| Category coverage | 90 | 10+ categories validated |
| Urgency detection | 88 | Cancellation same-day works |
| Field extraction | 80 | Good on scenario pack; edge cases on real messages |
| Label mapping | 70 | Engineer category names vs Case focus labels |
| Latency UX | 75 | Works; loading message missing |
| Real-message variance | 78 | Draft quality varies (see Case Record) |

**P11 reference:** "Triage engine is trial-ready."

---

## SECTION 8 — Gap Analysis

What's missing.

| Gap | Severity |
|-----|----------|
| Mixed-language edge cases on real broker messages | **P2** |
| Engineer category names visible vs CUSTOMER_LANGUAGE_GUIDE | **P1** |
| Draft quality variance passed through triage pipeline | **P1** (Case Record owns presentation) |
| First-request 503/warming without user message | **P1** |
| chen_kui client pack not fully loaded in triage/draft tuning | **P2** |
| No in-UI guardrail status for founder | **P3** |

---

## SECTION 9 — Top 10 Improvements

Ranked.

| # | Improvement | ROI |
|---|-------------|-----|
| 1 | Apply CUSTOMER_LANGUAGE_GUIDE consistently in triage → UI field mapping | Broker trust |
| 2 | Load chen_kui client pack tuning for draft generation path | Real-message draft quality |
| 3 | First-request loading copy: "首次分析约30秒" | Prevents "broken" abandon |
| 4 | Graceful warming/503 message with retry guidance | Trial Day 1 survival |
| 5 | Fix-now queue from trial: top 3 real-message triage failures only | Targeted tuning |
| 6 | Rename 高风险 → 需当天处理 in urgency display | Clearer broker language |
| 7 | Guardrail scenario alignment with 3 trial scenarios (cancellation, missing doc, add-car) | Playbook parity |
| 8 | Log triage category on observation log template | ROI measurement |
| 9 | Suppress engineer trace fields in product_only case detail | Trust |
| 10 | Weekly guardrail run in founder pre-trial checklist | Regression prevention |

---

## SECTION 10 — Must Not Build

Prevent scope creep.

- WeChat/email sync for automatic triage input  
- OCR / screenshot upload as triage input path  
- New issue categories beyond fix-now trial evidence  
- Multi-model routing / agent orchestration platform  
- Real-time streaming triage redesign  
- Carrier API integration for policy lookup  
- Auto-send based on triage output  
- Custom per-broker ML training pipeline  
- RAG `/demo` retrieval as triage substitute  
- Enterprise category taxonomy (50+ types)  

---

*End of Capability Contract 02*
