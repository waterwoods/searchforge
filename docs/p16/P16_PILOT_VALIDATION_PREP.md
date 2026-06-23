# P16 Pilot Validation Prep — Real Broker Testing

**Date:** 2026-06-21  
**QA URL (only):** https://ui-smoky-beta.vercel.app/add-car  
**Backend:** Cloud Run `fiqa-api-00102-fbp` (PDF text-layer VIN fix deployed)

---

## A. Wu Xiaojie Test Plan

**Goal:** One real add-car case, end-to-end, timed.

| Step | Action | Record |
|------|--------|--------|
| 1 | Open https://ui-smoky-beta.vercel.app/add-car on phone or laptop | Start timer |
| 2 | Select **I bought a new car** → enter name, phone, garaging ZIP | — |
| 3 | Upload **one real document** (purchase agreement, reg card, or insurance card — redact PII in notes if sharing screenshots) | Document type |
| 4 | Wait for packet → check **VIN**, **Year/Make/Model**, readiness badge | Screenshot |
| 5 | Note **VIN source** (PDF vs photo) and **Case ID** on packet screen | — |
| 6 | Tap **Copy Packet** | — |
| 7 | Paste into WeChat / Google Doc / AMS notes field | Stop timer |
| 8 | Answer 3 questions (below) | Written notes |

**Three questions (record verbatim):**

1. **Would you use this?** (Yes / Maybe / No — why?)
2. **What was confusing?** (UI, language, missing fields, warnings?)
3. **Did it save time?** (vs current manual intake — estimate minutes saved or lost)

**Success signal:** Copy-paste into carrier/AMS takes < 2 minutes after upload; VIN matches document.

**Do not:** Share customer PII in group chats; use redacted docs or office-owned samples only.

---

## B. Chen Kui Demo Plan (5 minutes)

| Min | Beat | Show |
|-----|------|------|
| 0:00 | **Pain question** | "When a customer sends you a purchase agreement on WeChat, how long until you can start a quote?" |
| 0:45 | **Case A — READY** | Upload `pa_007` or real clean PDF → **READY FOR BROKER** → VIN + YMM visible |
| 1:30 | **Copy Packet** | Copy → paste into notepad; show broker-ready format |
| 2:15 | **Case B — NEED_INFO** | Upload grocery receipt or partial chat → **NEED_INFO** + missing items list |
| 3:00 | **Auto Follow-Up** | Show follow-up message block; explain customer gets clear ask, not fake READY |
| 3:45 | **Case ID** | Point to case ID on packet — office can reference in follow-up |
| 4:15 | **Pilot ask** | "Can we run 10 real add-car cases through this URL over the next 2 weeks?" |
| 5:00 | **Close** | Share QA URL only; no preview URLs |

**Backup if READY fails:** Show BROKER_REVIEW with warnings — honest about broker verify step.

---

## C. Broker Outreach Targets (5 archetypes)

Prepare only — **do not send** until Andy approves.

| # | Archetype | Why | Contact angle |
|---|-----------|-----|---------------|
| 1 | **Chinese auto insurance broker (SGV)** | Primary pilot persona; WeChat intake, bilingual docs | "Upload-first add-car packet — 3 min, no login" |
| 2 | **Small independent agency (1–3 agents)** | Fast decision, pain is manual re-keying | Time-savings demo + 10-case pilot |
| 3 | **Uber Black / commercial auto broker** | High add-car volume, VIN-heavy | VIN accuracy + conflict warnings |
| 4 | **Orange County / Irvine broker office** | Local, can meet in person for feedback | Live demo on stable QA URL |
| 5 | **Office with assistant doing intake** | Assistant is daily user; broker validates | Assistant uploads → broker copies packet to AMS |

**Outreach template (draft, not sent):**

> Hi [Name] — we built a 3-minute add-car intake link for CA brokers. Customer uploads purchase agreement or reg card; you get a copy-ready packet with VIN and vehicle info. Looking for 10-case pilot feedback. Stable link: https://ui-smoky-beta.vercel.app/add-car

---

*Related: `P16_PDF_VIN_EXTRACTION_FIX_REPORT.md` · `P16_REAL_WORLD_VALIDATION_REPORT.md` · `P16_DEPLOYMENT_PLAYBOOK.md`*
