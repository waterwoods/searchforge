# P16 4-Day Build Plan

**Date:** 2026-06-20  
**Sprint:** P16 Structured Build  
**Authority:** `docs/p16/P16_DECISION_FREEZE_V1.md` · `docs/p16/P16_REQUEST_FRAMEWORK.md`  
**Supersedes:** `docs/p16/P16_72_HOUR_BUILD_PLAN.md` (completed / historical)

---

## Goal

Production-level demo for Chen Kui.  
Real cases possible by Day 3.  
First $49 invoice possible after 10 cases.

---

## North Star

```
Customer submits in < 3 minutes
Extraction completes in < 60 seconds
Broker understands packet in < 30 seconds
Copy All works cleanly
No technical noise visible
```

---

## Scope (Non-Negotiable)

**Build:**
- Add Vehicle full loop (stable, ready for real cases)
- Replace Vehicle V1 Safe (if time allows after Day 2)

**Do Not Build:**
- Switch Insurance
- Renewal / Quote Shopping
- Add Driver, Address Change, Coverage Change
- Timeline UI (see ADR-002)
- Carrier API (see ADR-003)
- CRM integration
- PDF export
- Customer login / accounts
- WeChat Bot
- Trade-in automation
- Multi-tenant / multi-broker

---

## Success Criteria

| Criterion | Pass Condition |
|-----------|----------------|
| Customer flow | Submits real documents in < 3 minutes on mobile |
| Extraction | Completes in < 60 seconds with real iPhone photos |
| HEIC support | iPhone HEIC upload succeeds end-to-end |
| Broker packet | Wu Xiaojie reads packet in < 30 seconds |
| Copy All | Pastes cleanly into Google Docs / AMS clipboard |
| Source attribution | Every field shows "from: filename" — no hidden data |
| No mock banner | Production deploy shows no mock mode banners |
| No model names | "gemini" or "gpt" never visible in any UI |
| Real case logged | CK-001 completed with time savings recorded |
| Go/No-Go | `trial_launch_check.sh` PASS on Day 4 |

---

## Day 1 — Jun 20 (Docs Freeze + UI Polish)

**Goal:** Documentation system frozen. Product demo-ready for internal walkthrough.

### AM — Documentation (no code)

| Task | Owner | Est. |
|------|-------|------|
| Create `docs/p16/adr/` directory | Agent | 5 min |
| Write ADR-001 (Request Readiness) | Agent | 20 min |
| Write ADR-002 (No Timeline V1) | Agent | 15 min |
| Write ADR-003 (No Carrier API V1) | Agent | 15 min |
| Write `P16_REQUEST_FRAMEWORK.md` | Agent | 30 min |
| Write `P16_CUSTOMER_FLOW_BLUEPRINT.md` | Agent | 30 min |
| Write `P16_4_DAY_BUILD_PLAN.md` (this file) | Agent | 20 min |
| Update Decision Freeze — add ADR Index | Agent | 10 min |
| Mark 72-hour plan as HISTORICAL | Agent | 5 min |

### PM — UI Polish (P1 items from P16_DECISION_FREEZE_V1.md §12)

| Item | Change | File | Est. |
|------|--------|------|------|
| UI-05 | Screen 3: Replace bare spinner with animated steps | AddCarPage.tsx | 30 min |
| UI-06 | Screen 1: "Customer Information" → "Your Information" | AddCarPage.tsx | 2 min |
| UI-07 | Screen 2: `InboxOutlined` → `CloudUploadOutlined` | AddCarPage.tsx | 2 min |
| UI-08 | Screen 2: "Read Documents" → "Continue →" | AddCarPage.tsx | 2 min |
| UI-09 | Screen 3: Bilingual loading steps | AddCarPage.tsx | 20 min |
| UI-10 | Screen 4: Customer name + garaging ZIP above fold | AddCarPage.tsx | 15 min |

### Day 1 QA Checklist

```
□ bash scripts/run_demo_local.sh → clean (port 8001)
□ Full Add Vehicle flow: info → upload → extract → packet → copy
□ "Your Information" on Screen 1 (not "Customer Information")
□ Animated loading on Screen 3 (not bare spinner)
□ Source attribution visible inline on VIN field
□ Warnings appear BEFORE vehicle fields
□ Copy All → paste into Google Docs → format clean
□ No "gemini" or AI model names visible anywhere
□ No mock mode banner visible
```

### Day 1 Demo Checkpoint

- Internal walkthrough (Andy) using real documents
- All 5 screens complete without interruption
- Copy Packet readable in 10 seconds

### Day 1 Demo Script Update

- Update Screen 1 description: "Your Information"
- Update Screen 3 description: animated steps, not spinner
- Note any friction points for Day 2

---

## Day 2 — Jun 21 (Replace Vehicle V1 Safe)

**Goal:** Replace Vehicle request type end-to-end. Wu Xiaojie test ready.

### AM — Replace Vehicle Backend

| Task | Est. |
|------|------|
| Register `replace_vehicle` in RequestTypeFieldConfig | 30 min |
| Define Replace Vehicle schema (new + old vehicle fields) | 20 min |
| Extend extract endpoint to handle replace_vehicle path | 45 min |
| Add old vehicle identifier to packet assembly | 30 min |
| Add Replace Vehicle safety rules (no auto-remove, conflict flag) | 20 min |

### PM — Replace Vehicle Frontend

| Task | Est. |
|------|------|
| Intent Selector: add "Replace my car" option | 15 min |
| Screen 1 / Fix Missing: old vehicle fields (plate or VIN) | 30 min |
| Packet: Related Vehicle section (old car details) | 30 min |
| Packet: Replace Vehicle safety warning ("Broker must process") | 10 min |
| Replace Vehicle output language: "Broker will review replacement" | 5 min |

### Day 2 QA Checklist

```
□ Add Vehicle flow unchanged after Replace Vehicle addition
□ Intent Selector shows both options correctly
□ Replace Vehicle dry run: new purchase agreement + old insurance card
□ Old vehicle identifier captured (plate or VIN)
□ Packet shows: New Vehicle · Old Vehicle · Warnings
□ Copy All output includes "REPLACE-VEHICLE PACKET" header
□ No "auto-remove" language in any output
□ Replace Vehicle readiness state correct (READY / NEED_INFO / BROKER_REVIEW)
□ bash scripts/run_demo_local.sh → clean
```

### Day 2 Demo Checkpoint

- Replace Vehicle dry run with real docs (Andy)
- Packet shows new + old vehicle, source attribution, warnings
- Copy All pastes cleanly

### Day 2 Demo Script Update

- Add Replace Vehicle scene (3 talking points)
- Add "old vehicle flagged, not auto-removed" trust moment

---

## Day 3 — Jun 22 (First Real Case — Wu Xiaojie)

**Goal:** CK-001 real case. First time savings data point.

### AM — Wu Xiaojie Real Test

| Step | What |
|------|------|
| Send QA URL to Wu Xiaojie | `https://ui-smoky-beta.vercel.app/add-car` |
| Wu Xiaojie uses real customer documents | WeChat export / dealer PDF / iPhone photo |
| Time the full flow (manual vs. product) | Stopwatch both paths |
| Observe every screen for friction | Note anything that causes pause or confusion |
| Log CK-001 in tracker | `docs/trial/P16_TIME_SAVINGS_TRACKER.md` |

### PM — Fix + Record

| Task | Est. |
|------|------|
| Fix any P0 bugs found in Wu Xiaojie test | Up to 2 hours |
| Fill `P16_CASE_EVIDENCE_LOG.md` (CK-001) | 15 min |
| Fill `P16_BROKER_FEEDBACK.md` (Wu Xiaojie reaction) | 15 min |
| Update `P16_REAL_PILOT_DASHBOARD.md` | 10 min |
| If HEIC issue: test with real iPhone, fix MIME or conversion | Up to 1 hour |

### Day 3 QA Checklist

```
□ CK-001 completed end-to-end without blocking error
□ Time savings recorded: [manual time] vs. [product time]
□ HEIC upload from real iPhone camera roll: success
□ Copy Packet → clean paste confirmed by Wu Xiaojie
□ P16_TIME_SAVINGS_TRACKER.md has 1 real data row
□ No mock mode banner fired during real test
□ Wu Xiaojie able to read packet in < 30 seconds
```

### Day 3 Demo Checkpoint

- Can demonstrate using CK-001 as a real example
- "We already have a real case" is the most powerful demo moment

### Day 3 Demo Script Update

- Add Wu Xiaojie real quote (if positive) to opening hook
- Add CK-001 time savings to demo closing ("saved X minutes on a real case")

---

## Day 4 — Jun 23 (Stabilize + Chen Kui Ready)

**Goal:** Chen Kui can use the product directly. Invoice path clear.

### AM — CK-002 / CK-003 (if available)

| Step | What |
|------|------|
| CK-002: second real case | Wu Xiaojie brings another customer file |
| CK-003: if available | Third real case |
| Log each case | Tracker, Evidence Log, Feedback |
| If Wu Xiaojie confirms GO: send URL to Chen Kui | Direct URL + brief walkthrough note |

### PM — Invoice Prep + Final QA

| Task | Est. |
|------|------|
| Update `P16_INVOICE_READINESS_TRACKER.md` | 10 min |
| Prepare `INVOICE_TEMPLATE_49.md` (fill Chen Kui info) | 10 min |
| Run `bash scripts/trial_launch_check.sh` | 5 min |
| Run `bash scripts/demo_quick_validate.sh` | 5 min |
| Update demo script: final version with real data | 20 min |
| Update `P16_REAL_PILOT_DASHBOARD.md` | 10 min |

### Day 4 QA Checklist

```
□ trial_launch_check.sh PASS
□ demo_quick_validate.sh PASS
□ P16_REAL_PILOT_DASHBOARD.md reflects actual case count
□ P16_TIME_SAVINGS_TRACKER.md has real data (at least CK-001)
□ Replace Vehicle still works (regression check)
□ Add Vehicle still works (regression check)
□ Demo script: final version, includes real data point
□ Invoice template: filled, ready to send after 10 cases
```

### Day 4 Demo Checkpoint

- Full demo: Add Vehicle + Replace Vehicle back to back
- Real case data shown ("saved X minutes on Y cases")
- Chen Kui receiving the product directly, or Wu Xiaojie confirmed GO

### Day 4 Go/No-Go

| Gate | Pass Condition |
|------|----------------|
| `trial_launch_check.sh` | PASS |
| Add Vehicle real case | ≥ 1 case logged |
| Time savings | ≥ 1 data point (even if < 4 min) |
| Copy All | Confirmed clean by Wu Xiaojie |
| Broker packet | Readable in < 30 seconds |
| Demo script | Final version exists |
| Invoice ready | Template filled, waiting for 10-case gate |

**GO = all 7 pass.**  
**NO-GO = any one fails. Fix before Chen Kui call.**

---

## What Not to Build — Permanent List

These items are off-limits for the entire 4-day sprint. If any of these come up in a coding session, stop and refer to this list.

| Item | Rule |
|------|------|
| Timeline UI | ADR-002: deferred to post-10-case |
| Carrier API | ADR-003: deferred indefinitely for V1 |
| Quote engine | Not P16's product |
| CRM integration | Out of scope |
| PDF export | Deferred per Decision Freeze §4 |
| Customer login | Phone + link identity only |
| WeChat Bot | Paste/link only |
| Trade-in automation | Flag only; broker resolves |
| Multi-broker | Single pilot |
| Switch Insurance | V2, after pilot proven |
| Renewal / Quote Shopping | V2, after pilot proven |
| New DB tables (timeline) | ADR-002: use existing fields only |

---

## Document Hierarchy During Build

| Priority | Document | Read Before... |
|----------|----------|----------------|
| 1 | `docs/p16/P16_DECISION_FREEZE_V1.md` | Any scope decision |
| 2 | `docs/p16/P16_REQUEST_FRAMEWORK.md` | Any new request type work |
| 3 | `docs/p16/adr/ADR_001_REQUEST_READINESS.md` | Any UI state work |
| 4 | `docs/p16/adr/ADR_002_NO_TIMELINE_V1.md` | Any timeline discussion |
| 5 | `docs/p16/adr/ADR_003_NO_CARRIER_API_V1.md` | Any carrier/quote discussion |
| 6 | `docs/p16/P16_CUSTOMER_FLOW_BLUEPRINT.md` | Any frontend UX work |
| 7 | `docs/CURRENT_PRODUCT_SHAPE.md` | Any deploy/env question |

---

*Historical: `docs/p16/P16_72_HOUR_BUILD_PLAN.md` (completed Jun 18–19)*
