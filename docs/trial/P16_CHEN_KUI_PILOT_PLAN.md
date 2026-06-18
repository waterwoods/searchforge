# P16 Chen Kui Pilot Plan

**Sprint:** P16-CHEN-KUI-PILOT-SPRINT · Phase 0  
**Date:** 2026-06-06  
**Status:** Ready to start

---

## Pilot definition

| Field | Value |
|-------|-------|
| **Pilot Owner** | Andy |
| **Broker** | Chen Kui (陈魁) |
| **Pilot Duration** | 3–7 days (minimum 3 active days; extend to 7 if broker wants full trial window) |
| **Target Case Type** | **Add-Car only** |
| **Target Volume** | **10 real customer cases** |
| **Success Threshold** | **≥ 4 minutes saved per case** (broker-estimated, logged per case) |

---

## Why add-car only

Add-car is Chen Kui's highest-frequency, highest-friction WeChat workflow:

- Messages arrive fragmented (year, VIN, ZIP, driver in separate bubbles)
- Broker re-reads the thread to build a quote packet for office
- Append paths (return later with name/phone) are now integrity-certified (P16 Append Sprint PASS)

Cancellation and missing-doc remain valuable but are **out of scope** for this pilot. Narrow scope = measurable ROI.

---

## What Chen Kui does

1. Paste real WeChat customer messages into **办公室工作台** (broker workbench)
2. Review structured case: Collected / Still needed / Next step / Draft
3. Copy draft (with edits) → send on WeChat himself
4. Append new customer messages to the same case when they return later
5. Log every case in [`P16_PILOT_CASE_LOG_TEMPLATE.md`](./P16_PILOT_CASE_LOG_TEMPLATE.md)

---

## What Andy does

| Day | Andy action |
|-----|-------------|
| Day 0 | Run `bash scripts/trial_launch_check.sh`; kickoff per [`CHEN_KUI_DAY0_SCRIPT.md`](./CHEN_KUI_DAY0_SCRIPT.md) |
| Daily | WeChat check-in; review case log; note friction (no feature work during pilot) |
| Day 3 | Mid-pilot pulse: ≥5 cases logged? On track for 4 min/case? |
| Day 7 (or end) | 15-min review: minutes saved, draft usage, payment conversation |

---

## Success criteria

| Gate | Target | Evidence source |
|------|--------|-----------------|
| Real add-car cases | ≥ 10 | Case log |
| Avg minutes saved | ≥ 4 min/case | Case log column |
| Draft copied (with edits OK) | ≥ 7 of 10 | Case log |
| Append used without field loss | 0 regressions | Case log + append spot-check |
| Broker would continue | Y on Day 7 | Founder simulation debrief |

**Simulation baseline (pre-pilot):** 30 AI add-car scenarios, 100% pass rate, 6.2 min avg saved vs manual workflow. Pilot must confirm this holds on **real** WeChat paste.

---

## Out of scope (hard rules)

- No UI redesign
- No new features
- No architecture changes
- No main merge or deployment changes during pilot
- No cancellation / missing-doc cases in success denominator

---

## Materials

| Doc | Purpose |
|-----|---------|
| [`P16_PILOT_CASE_LOG_TEMPLATE.md`](./P16_PILOT_CASE_LOG_TEMPLATE.md) | Per-case evidence |
| [`PILOT_TERMS_V1.md`](./PILOT_TERMS_V1.md) | Trial terms ($49 / $99) |
| [`CHEN_KUI_DAY0_SCRIPT.md`](./CHEN_KUI_DAY0_SCRIPT.md) | 30-min kickoff |
| [`INVOICE_TEMPLATE_49.md`](./INVOICE_TEMPLATE_49.md) | Day 7 payment |
| [`BROKER_ONE_PAGER.md`](../BROKER_ONE_PAGER.md) | Broker-facing summary |

---

## Pre-flight (complete)

| Check | Status |
|-------|--------|
| Append integrity | PASS (22/22 battery) |
| Demo readiness | PASS |
| Governance | Complete |
| Add-car simulation (30 scenarios) | PASS (100%, avg 6.2 min saved) |

---

## Pilot start command

```bash
bash scripts/trial_launch_check.sh
bash scripts/guardrail_inbox_triage.sh
```

Then: Day 0 call with Chen Kui → first real add-car paste → start case log.

---

*Phase 0 complete — pilot definition locked.*
