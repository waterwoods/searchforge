# Capability Contract 04 — Customer Intake Collection

**Capability:** Customer Intake Collection  
**Version:** V1 Ratified  
**Date:** 2026-05-31  
**Maps to:** Capability Map V1 §4

---

## SECTION 1 — Purpose

Why this capability exists.

Accept messy inbound customer information into the system via **broker paste** (primary v1 path) or **customer portal** (secondary — Add-Car). Raw text enters without cleanup; the system creates a triage request and case/session ID for continuity.

Manual paste is the real workflow (P10 #7). No WeChat sync in v1 — this must be explicit at every touchpoint.

---

## SECTION 2 — Primary User

Who uses it.

| User | Path | Priority |
|------|------|----------|
| **Broker owner** | Paste on 办公室工作台 | **Primary GTM** |
| **Office assistant** | Same paste workflow | **Primary GTM** |
| **End customer** | 客户报送 Add-Car portal | Secondary — not Chen Kui sales lead |

---

## SECTION 3 — Inputs

What enters the capability.

| Input | Format | Notes |
|-------|--------|-------|
| Pasted message text | Raw — WeChat, email body, notice, OCR text pasted externally | No cleanup required |
| Optional broker context | Short note with paste | Optional |
| Add-Car structured form | Customer portal fields | Secondary surface |
| Session/case reference | On follow-up paste to existing case | Lifecycle overlap |

---

## SECTION 4 — Outputs

What must come out.

| Output | Requirement |
|--------|-------------|
| Triage request | Triggers Urgent Message Triage |
| Case/session ID | Continuity for follow-up |
| Case appears in workbench queue | Visible after triage completes |
| Paste confirmation | User knows analysis started (loading state) |
| Workflow expectation set | "原样粘贴微信/通知文字，不用整理" |

---

## SECTION 5 — Success Metrics

How success is measured.

| Metric | Target | Source |
|--------|--------|--------|
| Raw paste success rate | ≥95% without pre-formatting | Trial observation log |
| Real cases logged | ≥3 during 7-day trial | TRIAL_ONE_PATH |
| Paste-to-case latency | ≤30s with loading message | P11 |
| Wrong-surface paste | 0 brokers pasting on Customer Entry for triage | Observation log |
| Guardrail scenarios | PASS on paste-equivalent inputs | guardrail script |

---

## SECTION 6 — Acceptance Criteria

How we know it works.

- [ ] Broker can paste raw Chinese/English mixed text on 办公室工作台  
- [ ] Paste area copy sets expectation: no cleanup needed  
- [ ] Case appears in queue after triage without manual refresh  
- [ ] Follow-up paste via 更新客户新消息 updates same case  
- [ ] Add-Car portal works but is not default trial path  
- [ ] First-request loading prevents "broken" abandon  
- [ ] Paste works on prod URL with Postgres persistence  

---

## SECTION 7 — Current State

Score **0–100** today.

### Score: **62 / 100**

| Dimension | Score | Notes |
|-----------|-------|-------|
| Broker paste mechanism | 85 | Core path works |
| Paste UX copy | 55 | Expectation not always clear |
| Loading states | 50 | 30s wait without message |
| Surface promotion | 40 | Add-Car default vs broker paste |
| Follow-up paste discoverability | 60 | 更新客户新消息 not prominent |
| Customer portal | 70 | Add-Car works; wrong GTM lead |
| Mobile paste | 45 | Weak on phone |

---

## SECTION 8 — Gap Analysis

What's missing.

| Gap | Severity |
|-----|----------|
| Two doors (客户报送 vs 办公室工作台) — broker starts wrong | **P0** |
| Paste expectation copy missing | **P1** |
| First-request loading state | **P1** |
| 更新客户新消息 not prominent on case detail | **P1** |
| Add-Car-first UI vs cancellation-first trial story | **P1** |
| Mobile-friendly paste area | **P3** |
| Demo vs real paste workflow unclear | **P2** |

---

## SECTION 9 — Top 10 Improvements

Ranked.

| # | Improvement | ROI |
|---|-------------|-----|
| 1 | Broker tab default (Front Door #1) — paste surface visible first | Critical |
| 2 | Paste area copy: "原样粘贴微信/通知文字，不用整理" | Sets workflow expectation |
| 3 | First-request loading: "首次分析约30秒" | Prevents abandon |
| 4 | Highlight 更新客户新消息 when case selected | Follow-up discoverability |
| 5 | One-line wayfinding on paste surface | Reduces wrong-tab paste |
| 6 | Reconcile Add-Car banner with cancellation-first demo | Story alignment |
| 7 | Empty queue: 3-step "paste → review → copy" zero-state | Onboarding |
| 8 | Mobile-friendly paste area (if phone-first office) | P3 — optional v1 |
| 9 | Separate demo queue paste from real paste visually | Clarity |
| 10 | Log paste source (real vs demo) in observation template | Trial measurement |

---

## SECTION 10 — Must Not Build

Prevent scope creep.

- WeChat inbox sync  
- Email IMAP integration  
- In-product OCR / screenshot upload as primary intake  
- WhatsApp / SMS connectors  
- Bulk import from carrier systems  
- Customer self-serve signup portal  
- Multi-channel unified inbox UI  
- Voice message transcription  
- Browser extension for WeChat (v1)  
- API-first intake for third-party integrations  

---

*End of Capability Contract 04*
