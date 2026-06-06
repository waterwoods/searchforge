# P16-O Phase 1 — Implementation Plan

**Date:** 2026-06-01  
**Sprint:** P16-O Customer Entry Simplification (implementation)  
**Scope:** Capability 4 — Customer Intake Collection  
**Source:** P16-N phases 1–10  
**Constraint:** UI/copy/layout only — no capability, Constitution, or triage engine changes

---

## Baseline → Target

| Metric | Before (P16-N) | Target |
|--------|----------------|--------|
| Customer Entry score | ~50 | ≥75 |
| Landing 5s test | 33 | ≥75 |
| Visible empty-state objects | 16–18 | 8–10 |
| Primary-action pages passing | 3/7 | 7/7 |

---

## Top 20 Items (Implemented)

All items map to **Capability 4 — Customer Intake Collection**.

| # | Item | Cap 4 | ROI | Effort | Risk | Status |
|---|------|-------|-----|--------|------|--------|
| 1 | Message-first headline + trust line | Landing clarity | 5 | S | Low | ✅ |
| 2 | Hero textarea + single 发送 button | Primary action | 5 | M | Med | ✅ |
| 3 | Remove 3-button category row | Competing primaries | 5 | M | Med | ✅ |
| 4 | Hide flow step track until first submit | Progressive disclosure | 5 | M | Low | ✅ |
| 5 | Remove ①②③ instructions | Onboarding noise | 5 | S | Low | ✅ |
| 6 | Demote 联系人工 to footer link | Competing primaries | 5 | S | Low | ✅ |
| 7 | Structured add-car behind opt-in link | Form wall | 4 | M | Low | ✅ |
| 8 | Merge handoff-pending into one alert | Dual path | 5 | M | Med | ✅ |
| 9 | Remove UTC timing truth footnote | Engineer metadata | 4 | S | Low | ✅ |
| 10 | Remove AddCarFlowExplanation post-handoff | Education overload | 4 | S | Low | ✅ |
| 11 | Single wait CTA on confirmation | Post-submit clarity | 4 | S | Low | ✅ |
| 12 | Remove 查看工作台 from customer view | Broker leak | 4 | S | Low | ✅ |
| 13 | Collapse record rail to 「已记录 N 项」 | Mid-flow density | 4 | M | Low | ✅ |
| 14 | Hide bubble micro-tags | Engineer metadata | 4 | S | Low | ✅ |
| 15 | Remove tab suffix micro-copy (customer tabs) | Chrome noise | 3 | S | Low | ✅ |
| 16 | Remove transaction gradient banner | Duplicate status | 4 | M | Low | ✅ |
| 17 | Fix 上传材料 → 描述要补的材料 | Trust break | 4 | S | Low | ✅ |
| 18 | Inline placeholder examples | Example toggle | 4 | M | Low | ✅ |
| 19 | Alert stack max 1 above input (handoff) | Alert fatigue | 4 | M | Low | ✅ |
| 20 | Toast 已整理成 case → 已收到 | Jargon | 3 | S | Low | ✅ |

**Deferred (backlog):** Separate customer-only URL hiding broker/sim tabs (#19 P16-N full route split) — partial via suffix removal + pilot intro hide.

---

## Files Changed

| File | Change |
|------|--------|
| `ui/src/features/intake/components/CustomerEntryTab.tsx` | Message-first empty state, progressive disclosure, post-submit strip |
| `ui/src/pages/UnifiedIntakePage.tsx` | Tab suffix removal, pilot intro hide, trust line on customer tabs |
| `ui/src/components/intake/UserCaseListProgressPanel.tsx` | My requests cleanup |
| `configs/clients/chen_kui/ui_copy.json` | P16-O customer copy |
| `ui/src/api/clientConfig.ts` | New optional copy keys |

---

## Review Loops

| Loop | Action |
|------|--------|
| 1 Implement | Top 20 items shipped |
| 2 Delete more | Examples toggle, identity strip, broker_next_step, boundary essays, refresh button |
| 3 Typeform challenge | Structured form + 更多类型 demoted to footer links only |

---

*End of P16-O Phase 1 — Implementation Plan*
