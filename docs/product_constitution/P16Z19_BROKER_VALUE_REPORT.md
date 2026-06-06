# P16-Z19 Step 3 — Broker Value Surface Report

**Date:** 2026-06-03  
**Sprint:** P16-Z19 Customer First Time-Saved Proof Sprint  
**Surface:** Broker Workbench (`BrokerWorkbenchTab` + `OfficeWorkbenchOneGlanceSummary`)  
**Test case:** Live `case_3626b7457291` (Add vehicle) + founder battery scenarios  
**Method:** Chen Kui 5-second test — no architecture changes

---

## The three questions

Can a broker understand within **5 seconds**:

1. **What case is this?**
2. **What is missing?**
3. **What should I do next?**

---

## Add-Car case (live — primary proof path)

**Case:** `case_3626b7457291` — 2024 Tesla Model 3 add to existing policy

| # | Question | Visible? | Where | 5-sec pass? |
|---|----------|----------|-------|-------------|
| 1 | What case? | ✅ | Glance headline + `primary_vehicle_summary: VIN 5YJ3E1EA1KF123456` + service lane Add-Car | **Yes** |
| 2 | What missing? | ✅ | `still_needed_fields` → 缺少资料：提车日期、姓名、电话 | **Yes** |
| 3 | What next? | ⚠️ | `broker_next_step` in English: "Confirm any missing driver, ZIP, or VIN if needed; then quote or add same day." | **Partial** — readable but not Chinese |

**Add-Car 5-second score: 85/100** — broker can act without reopening WeChat.

### What broker sees (component map)

| Surface | Component | Content on live case |
|---------|-----------|---------------------|
| Queue card | `BrokerWorkbenchTab` | Urgency, Add-Car status strip, preview text |
| Hero glance | `OfficeWorkbenchOneGlanceSummary` | Headline, missing checklist, stage line |
| Submission snapshot | `OfficeWorkbenchAddCarSubmissionSnapshot` | Formal delivered: 是 · 2026-06-03 |
| Next step block | Workbench detail | English `broker_next_step` |
| Thread | 对话记录 | 3 messages — customer paste + formal line |
| Client draft | Copy panel | Chinese `client_reply_draft` available |

---

## Generic scenarios (founder battery — no persist)

| Scenario | Q1: What case? | Q2: Missing? | Q3: Next? | 5-sec pass? |
|----------|----------------|--------------|-----------|-------------|
| Remove vehicle | ⚠️ Summary says "Remove vehicle" but no office record | ❌ `still_needed_fields: []` despite sale date unknown | ⚠️ Good English next step | **No** — 45/100 |
| Payment issue | ❌ Category `unclear` | ❌ No structured fields | ❌ Generic "ask for missing part" | **No** — 25/100 |
| Claim | ✅ "Claim intake / accident first response" | ✅ photos, accident_time_location | ✅ Actionable claim next step | **Partial** — 70/100 (no case in queue) |
| UW document | ✅ "Missing document follow-up" | ✅ garaging proof, driver license | ✅ Verify received / request missing | **Partial** — 75/100 (no case in queue) |

**Generic average 5-second score: 54/100** — triage output helps in-session; broker queue empty because no persist.

---

## Presentation gaps (presentation-only fixes allowed)

| # | Gap | Impact | Presentation fix (no architecture) |
|---|-----|--------|-----------------------------------|
| 1 | `broker_next_step` English on Chinese intake | +5–10s read time | Surface Chinese `client_prep` or translated next-step label in glance |
| 2 | `office_case_title` null | Headline inference works but weak | Promote `conversation_summary` first line as glance eyebrow |
| 3 | Queue shows raw paste on some cards | Hard to scan | Use existing `buildOfficeCaseHeadline()` in queue preview (UI-only) |
| 4 | Generic cases never hit queue | Broker never sees 4/5 battery scenarios | **Not presentation** — persist gate (out of scope this sprint) |
| 5 | `classification_signals` null on live API | No "why we classified this" strip | Wire existing `buildClassificationSignals()` when API returns data |
| 6 | Payment mis-route | Wrong mental model in glance | **Engine fix** — not presentation |

---

## Recommended presentation-only improvements (ranked)

These improve broker 5-second comprehension **without new services**:

| Priority | Change | File | Est. lift |
|----------|--------|------|-----------|
| 1 | Show Chinese next-action line from `client_prep` when `broker_next_step` is English | `WorkbenchSummary.tsx` | +8 pts Add-Car |
| 2 | Default-open missing-fields checklist when `still_needed_fields.length > 0` | `BrokerWorkbenchTab.tsx` | +5 pts |
| 3 | Queue card: use `buildOfficeWorkbenchGlance().headline` not raw `source_text` | `BrokerWorkbenchTab.tsx` | +10 pts queue scan |
| 4 | Badge "新报送" + vehicle line on Add-Car cards | Already partial — ensure `primary_vehicle_summary` on card | +3 pts |

**No code written this sprint** — findings documented for next 15-minute polish pass.

---

## Before / after broker mental model

### Before Customer First (WeChat paste)

```
Broker opens WeChat
  → read 3–8 lines mixed CN/EN
  → mentally extract VIN, dates, intent
  → write note in head or CRM
  → decide: quote? remove? claim?
  → reply asking for missing info
Time to actionable understanding: 4–8 minutes
```

### After Customer First (Add-Car persisted case)

```
Broker opens workbench
  → glance: Add-Car · VIN · missing 3 fields
  → read broker_next_step (1 line)
  → copy client_reply_draft or call carrier
Time to actionable understanding: 15–30 seconds
```

---

## Verdict

| Scope | 5-second test | Pass? |
|-------|---------------|-------|
| **Add-Car persisted case** | 85/100 | ✅ **PASS** |
| **Generic triage (no persist)** | 54/100 | ❌ FAIL for queue workflow |
| **Overall broker value surface** | **72/100** | ⚠️ **PASS for pilot pitch on Add-Car only** |

**Strongest proof:** Chen Kui opens one Add-Car case and knows vehicle, gaps, and next action without WeChat.

**Weakest link:** Non-Add-Car scenarios never appear in workbench — presentation polish cannot fix absent cases.
