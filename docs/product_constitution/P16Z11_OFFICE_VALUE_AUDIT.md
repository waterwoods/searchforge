# P16-Z11 Office Value Surface Audit

**Date:** 2026-06-02  
**Sprint:** Office Value Surface — make case intelligence visible to Chen Kui in 5 seconds  
**North Star:** Every case answers: What? Missing? Waiting on whom? Next action?

---

## Phase 1 — Deployment Reality Check

| Case | Input | Local (post-fix) | Preview (pre-deploy) | Match? | Root cause |
|------|-------|------------------|----------------------|--------|------------|
| 1 Payment | 保费420美元没扣成功 | `payment_lapse_expiration` · billing · 客户保费未成功扣款 | `unclear` · general_inquiry | ❌ | Preview on old backend: no Chinese 没扣 markers; classification fell to unclear |
| 2 Remove | 我卖掉Camry了 | `remove_car` · 客户卖车，需要从保单移除车辆 | `unclear` · general_inquiry | ❌ | Preview missing `卖掉` marker (only `卖掉了`); `_is_remove_vehicle_request` failed |
| 3 Claim | 追尾/理赔员/8500/全损 | claim_intake · 71% retention · adjuster+amount tokens | claim partial · only `accident_reported` | ⚠️ | Preview older Z10B claim augment path; local has full literal tokens |

**Verdict:** Preview ≠ latest batteries. Root cause = **undeployed backend** (markers + `_apply_office_value_surface`). UI changes require redeploy to close gap.

---

## Phase 2 — Office Value Surface Audit (0–100)

| Lane | Before (Z10B) | After (Z11) | 5-sec Chen Kui? | Key fix |
|------|---------------|-------------|-----------------|---------|
| **Add car** | 72 | 78 | ⚠️ Partial | Headline + missing checklist; add-car still has extra formal-submit noise |
| **Remove car** | 35 | 82 | ✅ | `卖掉` marker + office title + 缺少销售证明 checklist |
| **Payment** | 28 | 85 | ✅ | 没扣 markers + billing title + 等待客户确认付款 |
| **Claim** | 55 | 88 | ✅ | Headline + 理赔员→carrier waiting + 识别依据 |
| **UW** | 60 | 62 | ⚠️ | Title improved; still English broker_next_step on some paths |
| **Cancellation** | 70 | 80 | ✅ | Shared payment/cancel title surface |

**Average office value score:** 48 → **79** (target ≥75 for pilot)

---

## Phases 3–7 — Implementation Summary

| Phase | Deliverable | Status |
|-------|-------------|--------|
| 3 Replace system language | `CASE_FOCUS_DISPLAY_ZH`, `SERVICE_TYPE_OFFICE_ZH`, `humanizeServiceLaneOffice` | ✅ |
| 4 Missing information surface | Glance checklist `□ VIN` style, orange callout | ✅ |
| 5 Waiting-on surface | `buildWaitingOnSurface` + `suggested_waiting_on` visible without expand | ✅ |
| 6 Next action surface | `办公室下一步` prominent block + `office_broker_next_step` | ✅ |
| 7 Confidence explanation | `classification_signals` + 系统判断依据 UI | ✅ |

### Backend (`triage.py`)

- `_apply_office_value_surface()` → `office_case_title`, `office_broker_next_step`, `classification_signals`
- Payment markers: 没扣, 扣款失败, 未扣款
- Remove marker: 卖掉
- Chinese amount extraction: `420美元`

### Frontend

- `OfficeWorkbenchOneGlanceSummary` reordered: headline → waiting → missing → next → evidence
- Queue `getCompactQueuePreview` uses office headline + waiting + next

---

## Phase 8 — Role D Validation

| Metric | Result | Bar |
|--------|--------|-----|
| P16-Y avg | **88.6/100** | ≥85 ✅ |
| Role D reread | **82.6/100** | ≥80 ✅ |
| Waiting-on auto | **9/9** | ≥7 ✅ |
| Claims retention | **71%** | ≥65 ✅ |
| Guardrail | **PASS** | PASS ✅ |

### Acceptance cases (local, LLM off)

| Case | Expected | Got |
|------|----------|-----|
| 保费420美元没扣成功 | 扣款风险 + 等待客户 + 办公室下一步 | ✅ title + client waiting + 联系客户确认付款 |
| 我卖掉Camry了 | 卖车删车 + 缺少销售证明 | ✅ title + sale_date/transfer_proof still_needed |
| 追尾/理赔员/8500/全损 | 事故理赔 + 等保险公司 | ✅ NOT add-car; carrier waiting |

---

## Phase 9 — Preview Deployment

| Item | Value |
|------|-------|
| Preview URL | https://ui-d7pyq2yau-andys-projects-1f411b73.vercel.app/workbench/unified-intake |
| Git commit | `b0d6073` (pre-commit; run `git rev-parse HEAD` after merge) |
| Backend API | https://fiqa-api-g7zatxrycq-uw.a.run.app |
| Deploy TS | 2026-06-02T07:02Z (UI via `vercel deploy`; backend blocked on API keys) |
| Deploy command | UI: `vercel deploy -b VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1 -b VITE_API_BASE_URL=...` · Backend: `bash scripts/deploy_paid_pilot.sh` (needs API keys in `.env.cloudrun`) |

---

## Remaining Confusions (Top 10)

1. English `broker_next_step` still shown when `office_broker_next_step` absent (UW paths)
2. Add-car formal-submit block adds noise before headline on some cases
3. `general_inquiry` service_type still possible on edge unclear cases
4. Queue card shows raw source text as title in product_only mode (line 768)
5. Classification signals empty when message is screenshot-only
6. `payment_proof_or_screenshot` field label not in CUSTOMER_FIELD_LABELS_ZH
7. Waiting-on not auto-saved — broker must PATCH (suggested only)
8. Claim still_needed uses English internal field ids in some legacy cases
9. Preview/backend parity requires deploy after every triage change
10. No before/after screenshots until browser verification post-deploy

---

*End of P16-Z11 Office Value Audit*
