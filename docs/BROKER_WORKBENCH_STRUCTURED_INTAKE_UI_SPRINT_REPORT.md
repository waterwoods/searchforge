# Broker Workbench Structured Intake UI Sprint Report

**Sprint:** Broker Workbench Structured Intake UI  
**Date:** 2026-03-10  
**Scope:** SearchForge → Chen Kui Insurance Unified Entry — Broker Workbench UI only

---

## 1. Stages completed

| Stage | Status | Notes |
|-------|--------|------|
| **Stage 1 — Define broker-view target** | ✅ Completed | Aligned with BROKER_HANDOFF_CLARITY_GUIDE: Case focus → Your next move → Collected → Still needed → Full conversation |
| **Stage 2 — Surface structured fields in UI** | ✅ Completed | Collected/Still needed chips in case card; Recent case card shows compact structured hint |
| **Stage 3 — Graceful fallback** | ✅ Completed | Non-add-car cases fall back to conversation_summary parsing; empty sections not shown |
| **Stage 4 — Broker-staff review + validation** | ✅ Completed | Guardrail pass; UI build pass; API returns structured fields for add-car |
| **Stage 5 — Improvement loop 1** | Skipped | First pass sufficient; no repeated usability issues |
| **Stage 6 — Optional improvement loop 2** | Skipped | Not needed |
| **Stage 7 — Live demo / product proof** | ✅ Completed | 4 proof walkthroughs documented below |
| **Stage 8 — Regression + safety** | ✅ Completed | Case store persists structured fields; smoke check step added |
| **Stage 9 — Audit + judgment** | ✅ Completed | Verdict: Accept |

---

## 2. Broker-view target

| Priority | Content | Why |
|----------|--------|-----|
| 1 | Case focus | Broker triages at a glance |
| 2 | Your next move | One operational sentence |
| 3 | Collected (when applicable) | Broker avoids re-asking |
| 4 | Still needed (when safe) | Broker knows what to ask next |
| 5 | Full conversation | Raw text for verification |

**Principle:** Broker should understand the case and next step without scrolling. Structured Collected/Still needed appear above raw conversation.

---

## 3. UI / product changes made

| File | Change | Purpose |
|------|--------|---------|
| `services/fiqa_api/inbox_triage/case_store.py` | Persist `collected_fields`, `still_needed_fields` when saving case | Saved cases retain structured intake on reopen |
| `ui/src/api/inboxTriage.ts` | Add `collected_fields`, `still_needed_fields` to TriageResult | Type-safe API contract |
| `ui/src/pages/UnifiedIntakePage.tsx` | Add `ADD_CAR_FIELD_LABELS`, `humanizeAddCarField` | Human-readable field labels |
| `ui/src/pages/UnifiedIntakePage.tsx` | Case card: show Collected/Still needed chips when structured fields present | Broker sees structured intake at a glance |
| `ui/src/pages/UnifiedIntakePage.tsx` | Fallback to conversation_summary regex when no structured fields | Non-add-car cases unchanged |
| `ui/src/pages/UnifiedIntakePage.tsx` | Recent case card: compact Collected/Still needed line for add-car | Quick scan in work queue |
| `docs/BROKER_HANDOFF_CLARITY_GUIDE.md` | Update UI note | Document that structured chips are now surfaced |
| `docs/UNIFIED_INTAKE_DEMO_READINESS.md` | Update broker handoff bullet | Mention structured chips |
| `docs/runbooks/UNIFIED_INTAKE_MVP_RUNBOOK.md` | Update broker handoff note | Add-car structured display |
| `scripts/unified_intake_smoke_check.sh` | Add step 14 for add-car structured verification | Manual smoke includes structured check |

---

## 4. Validation and improvement loops

| Check | Result | Notes |
|-------|--------|-------|
| `npm run build` | PASS | UI compiles |
| `bash scripts/guardrail_inbox_triage.sh` | PASS | 49/49 scenarios, multi-turn, adversarial, complex |
| API add-car single message | PASS | Returns collected_fields, still_needed_fields |
| Improvement loop | Skipped | First pass sufficient |

---

## 5. Product proof strength

| Question | Answer |
|----------|--------|
| Is broker usability better? | Yes. Add-car cases show Collected/Still needed as labeled chips; broker no longer parses free-text first. |
| Is add-car more structured now? | Yes. Year, Make/Model, ZIP, Delivery, Primary driver, VIN appear as chips when extractable. |
| Is this more demo-strong? | Yes. Founder demo can show "客户要加一台2021 Tesla Model Y，下周提车" → broker sees Collected: Year, Make/Model, Delivery · Still needed: Primary driver. |

---

## 6. Validation summary

| Check | Result | Protects |
|-------|--------|----------|
| `npm run build` | PASS | UI compile |
| `bash scripts/guardrail_inbox_triage.sh` | PASS | Scenario pack, API, persistence, multi-turn, adversarial |
| `scripts/unified_intake_smoke_check.sh` | PASS | Guardrail + manual UI steps including add-car structured |

---

## 7. Business / platform value

| Area | Improvement |
|------|-------------|
| **Broker mental load** | Structured chips reduce parsing; broker sees what's collected and what's missing without reading summary. |
| **Repeated intake work** | Broker avoids re-asking for year/model/zip when already collected. |
| **Platform story** | Add-car handoff feels more like a real office tool; structured display supports future automation. |

---

## 8. Remaining blocker(s)

1. **Other flows:** Only add-car has structured fields; premium review, remove car, missing document still rely on conversation_summary.
2. **Field values:** Current display shows field names (Year, Make/Model) not extracted values (2025, Honda CR-V). Values live in conversation_summary; future enhancement could surface them.
3. **LC-AC3 friction:** Driver correction scenario (from prior sprint) still has minor handoff timing friction.

---

## 9. Recommended next step

**Extend structured fields to one more high-frequency flow** (e.g. remove car or missing document) when extraction is safe and cheap. Keep add-car as the primary demo-strong case.

---

## 10. 中文或中英混合宏观总结

**Broker Workbench 这次具体变好了什么：**
- Add-car / 加车报价 case 现在有结构化的 Collected 和 Still needed 展示，不再只靠 conversation_summary 自由文本。
- 经纪人一眼能看到：已收集（Year, Make/Model, ZIP, Delivery 等）和还缺什么（Primary driver 等）。
- Recent cases 列表里 add-car case 也会显示紧凑的 Collected / Still needed 提示。

**经纪人现在一眼能多看到什么：**
- Collected: 绿色 chips（Year, Make/Model, ZIP, Delivery, Primary driver, VIN）
- Still needed: 橙色 chips（还缺的字段）
- 不需要先读整段 summary 才能知道客户给了什么、还缺什么。

**哪些 case 现在更像真实业务处理：**
- Add-car / 加车报价：结构化最强，demo 价值最高。
- 其他 flow（cancellation, missing doc, premium review）仍用自由文本，但不受影响。

**还缺什么：**
- 其他 flow 的结构化（remove car, missing document 等）尚未做。
- 字段值（如 2025, Honda CR-V）未单独展示，仍在 summary 里。

**这次对陈奎有没有明显价值：**
- 有。加车是日常高频 flow，经纪人现在能更快理解 case、减少重复问客户，产品更像真实办公室工具。

---

## 11. Practical broker workbench cheat sheet

| Item | What appears |
|------|--------------|
| **First** | Case focus (tag), Your next move (bold) |
| **Collected** | Green chips: Year, Make/Model, ZIP, Delivery, Primary driver, VIN (when extractable) |
| **Still needed** | Orange chips: fields broker should ask next |
| **When** | Add-car / new quote cases only; other flows show conversation_summary text |
| **Broker still does manually** | Live quote, carrier underwriting, VIN validation, send reply |

---

## 12. Broker-value summary

| Category | Before | After |
|----------|--------|-------|
| **Add-car clean** | Broker reads "Collected: year, model, zip. Still needed: primary driver" in summary text | Broker sees green Collected chips + orange Still needed chips |
| **Add-car vague** | Same free-text parsing | Same structured chips when extractable |
| **Add-car partial** | Same | Same |
| **Non-add-car (control)** | Free-text summary | Unchanged; no broken sections |
| **Strongest** | Add-car with year+model+zip+delivery | Structured display; demo-strong |
| **Improved most** | Add-car case scan time | Broker no longer parses summary first |

---

## 13. Live proof walkthroughs

### 1. Clean add-car case

| Step | Content |
|------|---------|
| Customer | 客户要加一台2021 Tesla Model Y，下周提车，问今天能不能先出报价 |
| Broker sees now | Collected: Year, Make/Model, Delivery · Still needed: Primary driver |
| Changed from before | Was: "Collected: year, model, delivery. Still needed: primary driver" in summary text. Now: labeled chips above. |
| Demo-strong? | **Yes** |

### 2. Vague / ultra-short add-car case

| Step | Content |
|------|---------|
| Customer | 我新车，下周拿，保险大概？ → (turn 2) 2025 CR-V, 90210 |
| Broker sees now | Collected: Year, Make/Model, ZIP, Delivery · Still needed: Primary driver |
| Changed from before | Same structured chips; multi-turn handoff preserved. |
| Demo-strong? | **Yes** |

### 3. Partial-info add-car case

| Step | Content |
|------|---------|
| Customer | 新车，92705，下周提，多少钱 |
| Broker sees now | Collected: ZIP, Delivery · Still needed: Year, Make/Model, Primary driver (or similar) |
| Changed from before | Structured chips show what's collected vs missing. |
| Demo-strong? | **Yes** |

### 4. Control non-add-car case

| Step | Content |
|------|---------|
| Customer | Notice: Policy will be cancelled in 7 days due to non-payment. |
| Broker sees now | No Collected/Still needed chips; conversation_summary as before. |
| Changed from before | **None** — graceful fallback. |
| Demo-strong? | N/A (control) |

---

*End of sprint report*
