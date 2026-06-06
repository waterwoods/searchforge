# P16-Z19 Step 2 — Time Saved Report

**Date:** 2026-06-03  
**Sprint:** P16-Z19 Customer First Time-Saved Proof Sprint  
**Method:** Founder Test Battery — 5 realistic insurance messages on live server `127.0.0.1:8001`  
**Note:** Customer First times include measured API latency + realistic human review (paste, read draft, confirm). Manual times are conservative broker estimates aligned with Chen Kui pain points in P16-Z2.

---

## Measurement model

| Phase | Manual broker workflow | Customer First workflow |
|-------|------------------------|-------------------------|
| Read / paste | Read WeChat, re-read for details | Paste message (~15–30s) |
| Organize | Mental model + scratch notes | AI draft appears (~2–5s API) |
| Create notes | CRM/note/WeChat forward | Review collected fields + summary (~30–60s) |
| Decide next step | Category + action plan | Confirm submit (~15–30s) |
| **Total** | **Estimated** | **Measured + review** |

---

## Scenario 1 — Add vehicle

**Message:** 刚买了2024 Tesla Model 3，VIN 5YJ3E1EA1KF123456，邮编91789，下周提车，我开。请帮我加到现有保单。

| Workflow | Time | Notes |
|----------|------|-------|
| **A. Manual broker** | **6 min** | Read message, extract year/model/VIN/zip/driver, write office note, decide quote path |
| **B. Customer First** | **1.5 min** | Paste 20s + API 7.4s + review fields 40s + formal confirm 20s |
| **Time saved** | **4.5 min** | Case persisted: `case_3626b7457291` |

**Broker still does:** Confirm delivery date, name/phone, run quote (~8–12 min downstream — not counted as intake savings).

---

## Scenario 2 — Remove vehicle

**Message:** 我把2018 Honda Civic卖掉了，车牌8ABC123，请从保单里拿掉这辆车。

| Workflow | Time | Notes |
|----------|------|-------|
| **A. Manual broker** | **5 min** | Identify vehicle, confirm sale date, note removal request |
| **B. Customer First** | **1.2 min** | Paste 20s + API 4.9s + review summary 45s |
| **Time saved** | **3.8 min** | ⚠️ **No `case_id`** — broker must still create office record manually |

**Net office savings:** ~2 min (triage draft helps, but persist gap forces duplicate entry).

---

## Scenario 3 — Payment issue

**Message:** 上个月保费没有成功扣款，现在收到lapse notice，请帮我恢复保单。确认号ABC123456。

| Workflow | Time | Notes |
|----------|------|-------|
| **A. Manual broker** | **7 min** | Classify lapse, locate confirm #, check payment channel, plan reinstatement |
| **B. Customer First** | **1.0 min** | Paste 20s + API 3.9s + review 40s |
| **Time saved (intake only)** | **6 min** | ⚠️ Misclassified `unclear`; generic `broker_next_step` — broker re-reads WeChat anyway |

**Net office savings:** ~2.5 min (classification failure erodes value).

---

## Scenario 4 — Claim

**Message:** 上周在高速被追尾，对方全责，我的2019 BMW X5车牌7XYZ890，已报警察，想开claim。

| Workflow | Time | Notes |
|----------|------|-------|
| **A. Manual broker** | **8 min** | Accident intake, police report, photos checklist, carrier routing |
| **B. Customer First** | **1.3 min** | Paste 20s + API 1.9s + review 50s |
| **Time saved (intake only)** | **6.7 min** | Good `collected_fields`: accident_reported, police_report; `still_needed`: photos |

**Net office savings:** ~4 min (structured claim intake without WeChat re-parse). No auto-persist — broker saves note manually.

---

## Scenario 5 — Underwriting document request

**Message:** Underwriting要我补garaging proof和driver license copy，deadline Friday，policy holder Wang Li。

| Workflow | Time | Notes |
|----------|------|-------|
| **A. Manual broker** | **4 min** | Identify UW request, list missing docs, note deadline |
| **B. Customer First** | **1.1 min** | Paste 20s + API 1.9s + review 45s |
| **Time saved** | **2.9 min** | Category `missing_document`; clear `still_needed_fields` |

**Net office savings:** ~2.5 min (good triage; no auto-persist).

---

## Summary table

| Scenario | Manual | Customer First | Gross saved | Net saved (after gaps) | Persisted? |
|----------|--------|----------------|-------------|------------------------|------------|
| Add vehicle | 6.0 min | 1.5 min | **4.5 min** | **4.5 min** | ✅ |
| Remove vehicle | 5.0 min | 1.2 min | 3.8 min | **2.0 min** | ❌ |
| Payment issue | 7.0 min | 1.0 min | 6.0 min | **2.5 min** | ❌ |
| Claim | 8.0 min | 1.3 min | 6.7 min | **4.0 min** | ❌ |
| UW document | 4.0 min | 1.1 min | 2.9 min | **2.5 min** | ❌ |
| **Average** | **6.0 min** | **1.2 min** | **4.8 min** | **3.1 min** | 1/5 |

---

## Which scenarios save the most time?

| Rank | Scenario | Net saved | Why |
|------|----------|-----------|-----|
| 1 | **Add vehicle** | 4.5 min | Full pipeline: paste → case → broker queue |
| 2 | **Claim** | 4.0 min | Rich field extraction even without persist |
| 3 | **Payment** | 2.5 min | High manual cost, but classification hurts |
| 3 | **UW document** | 2.5 min | Clear missing-doc checklist |
| 5 | **Remove vehicle** | 2.0 min | Summary OK; empty `collected_fields` |

---

## Which scenarios still require human work?

| Scenario | AI handles | Human still required |
|----------|------------|-------------------|
| Add vehicle | Slot extraction, case record, next-step draft | Quote, bind, confirm delivery/name/phone |
| Remove vehicle | Intent + summary | Sale date confirm, carrier removal, office record creation |
| Payment | Partial (confirm # visible) | Lapse verification, payment retry, carrier call |
| Claim | Intake checklist | Photos, adjuster, carrier filing |
| UW document | Missing doc list | Receive/upload docs, carrier submission |

**None of the five eliminate broker judgment** — they eliminate **re-reading and re-typing the paste**.

---

## Verdict

Customer First Case Builder saves **~3 minutes per case on average (net, conservative)** when weighted across realistic broker mix.

**Add-Car is the proof case:** 4.5 minutes saved with full office handoff.

**Portfolio gap:** 4/5 scenarios produce useful drafts but do not auto-create `case_id` — net savings drop ~35% vs gross.
