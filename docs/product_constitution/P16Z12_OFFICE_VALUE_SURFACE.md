# P16-Z12 Phase 8 — Office Value Surface Review (Preview Reality)

**Date:** 2026-06-02  
**Preview:** https://ui-d7pyq2yau-andys-projects-1f411b73.vercel.app/workbench/unified-intake

---

## Five office questions (Chen Kui 5-second test)

| # | Surface | Preview + deployed backend | Visible? |
|---|---------|----------------------------|----------|
| 1 | **什么案子** (what case) | No `office_case_title` from API; queue may show raw paste | ❌ |
| 2 | **当前等待** (waiting) | `suggested_waiting_on` absent on live triage | ❌ |
| 3 | **缺少资料** (missing) | No glance checklist from API on test cases | ❌ |
| 4 | **办公室下一步** (next) | English generic `broker_next_step` only | ⚠️ partial |
| 5 | **系统判断依据** (signals) | `classification_signals` empty `[]` | ❌ |

---

## Surface complete?

**NO** — UI components exist in bundle (`office_case_title`, Z11 layout) but **deployed backend does not supply office fields** on `/api/inbox/triage` for acceptance pastes.

---

## Missing UI pieces (blocked on backend/CORS)

- Office headline in one-glance summary (no API field)
- Waiting-on chip without manual PATCH
- Missing-info checklist (□ VIN style)
- Chinese next action block
- Classification evidence strip
- End-to-end browser verification (CORS)

---

## Top 10 office-value issues

1. Backend revision stale — Z11 `_apply_office_value_surface` not live.
2. CORS blocks Preview browser calls — surface never hydrates in prod-like test.
3. Payment case text **没有成功扣款** vs marker **没扣** — even post-deploy risk.
4. Claim mis-route to add_car on HTTP path.
5. `office_*` fields not returned on simple triage POST (deployed).
6. English broker_next_step on Chinese intake.
7. Waiting-on not persisted — only suggested when present.
8. Queue compact preview may show raw source (P16-Z11 #4).
9. No screenshots — automation blocked.
10. Founder local green ≠ Preview reality — deploy gate skipped.

---

## Office value score (Preview reality)

**~25/100** (aligned with founder walkthrough average)

*Local Z11 audit claimed **79/100** after code — **not validated on Preview** in Z12.*
