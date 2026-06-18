# P16 Commercial Readiness Review

**Sprint:** P16-CHEN-KUI-PILOT-SPRINT · Phase 4  
**Date:** 2026-06-06  
**Question:** If Chen Kui uses this tomorrow, what delights, annoys, builds trust, or causes abandonment?

**Scope:** Commercial issues only. No engineering perfectionism.

---

## If Chen Kui uses this tomorrow

### What will delight him

| # | Delight | Why |
|---|---------|-----|
| D1 | **No re-read WeChat** — Collected / Still needed on one screen | Core pain; simulation avg 6.2 min saved |
| D2 | **Chinese broker next step** — "联系客户补齐车架号、提车日期，然后出报价" | Speaks his language; office handoff clear |
| D3 | **Draft he can copy** — asks for missing VIN/ZIP, not generic fluff | Day 0 success = copy ≥1 draft |
| D4 | **Append without losing fields** — return-later name/phone keeps VIN/ZIP | Trust restored after append integrity sprint |
| D5 | **Add-car focus** — not another CRM; paste → case → WeChat | Matches one-pager promise |
| D6 | **Insurance card "already sent" handled** — doesn't re-ask for photo | AC05 quality 100; reduces customer annoyance |
| D7 | **7-day free trial, no auto-send** | Low risk; he stays in control |

### What will annoy him

| # | Annoyer | Severity |
|---|---------|----------|
| A1 | **Must paste manually** — no WeChat sync | Expected (v1); still friction vs dream product |
| A2 | **Draft needs edits** — especially minimal openers (AC11/AC12) | Medium; structure still helps |
| A3 | **Relative delivery dates** — "下周五" may stay in still_needed until resolved | Medium; broker knows calendar |
| A4 | **First turn on AC30-style threads** — turn 0 may not route add_car until turn 1 | Low if he pastes full thread |
| A5 | **URL / login surprises** — Preview SSO or wrong port | High if not pre-flighted |
| A6 | **Slow triage** — >60 sec wait on paste | Medium; breaks flow |
| A7 | **English customer threads** — mixed quality on driver/spouse edge cases | Low; he has English clients |

### What causes trust

| # | Trust builder | Evidence |
|---|---------------|----------|
| T1 | **Fields match what he pasted** — VIN, ZIP, vehicle correct | 96.6 avg quality; route 100% |
| T2 | **Append doesn't erase** — delivery_date stays collected | 22/22 append battery PASS |
| T3 | **Same-day founder WeChat support** | PILOT_TERMS_V1: 24h weekday |
| T4 | **He sends the message** — system never auto-replies customer | Product constitution |
| T5 | **Wrong output → Andy fixes, doesn't argue** | Day 0 script: "这条我记下来" |
| T6 | **Demo queue works offline** — can show value if paste fails | CHEN_KUI_DAY0_SCRIPT fallback |

### What causes abandonment

| # | Abandonment trigger | Likelihood |
|---|---------------------|------------|
| X1 | **Paste fails / 503 / embedding_warming** | High if not recovered |
| X2 | **Output wrong on first real case** + no visible fix | High |
| X3 | **Expected WeChat integration** — "why doesn't it read my chat?" | Medium |
| X4 | **Office says case packet incomplete** — still_needed wrong | Medium |
| X5 | **Forgot URL / SSO wall** — can't open alone after Day 0 | Medium |
| X6 | **Draft tone wrong for his customers** — too formal or English-only for 中文客户 | Low–Medium |
| X7 | **No perceived time savings after 3 cases** | High → trial ends early |

---

## Ranked issues (commercial only)

### P0 — Must not fail in pilot week

| ID | Issue | Mitigation |
|----|-------|------------|
| P0-1 | Workbench unreachable (503, CORS, SSO) | `trial_launch_check.sh` + Day 0 screen share fallback |
| P0-2 | Append loses VIN/ZIP/delivery | Integrity sprint complete; log append cases |
| P0-3 | First real paste returns garbage / empty | Demo queue fallback; founder on-call Day 0–2 |
| P0-4 | Chen Kui can't copy a usable draft by Day 2 | Day 0 must hit ≥1 draft copy; mid-pilot check |

### P1 — Affects retention and payment

| ID | Issue | Mitigation |
|----|-------|------------|
| P1-1 | Manual paste friction | Set expectation in one-pager; future ≠ pilot scope |
| P1-2 | Draft edit burden on minimal messages | Use multi-line paste tip; log edit level |
| P1-3 | Relative delivery in still_needed | Broker accepts; note in case log |
| P1-4 | No case log habit → no ROI proof | Andy daily nudge; template pre-filled |
| P1-5 | Day 7 payment conversation unprepared | INVOICE_TEMPLATE_49 ready; PILOT_TERMS sent Day 0 |

### P2 — Nice to fix; not pilot blockers

| ID | Issue | Notes |
|----|-------|-------|
| P2-1 | AC11/AC12 minimal opener quality 83 | Still PASS; asks right fields |
| P2-2 | AC30 turn-0 routing delay | Paste full thread |
| P2-3 | Customer append UI needs lastCaseId in browser | Broker-side append works |
| P2-4 | Teen/spouse driver ambiguity scoring | Broker confirms manually |
| P2-5 | My Requests / refresh continuity | Out of pilot scope |

---

## Commercial verdict (pre-pilot)

**Ready for supervised pilot:** YES  
**Ready for unsupervised Chen Kui solo from Day 1:** CONDITIONAL (URL stable + Day 0 complete)  
**Ready to invoice without 10 real cases logged:** NO

---

*Phase 4 complete — commercial lens applied.*
