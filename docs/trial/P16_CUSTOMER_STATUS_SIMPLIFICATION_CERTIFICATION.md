# P16 Customer Status Simplification — Certification

**Sprint:** P16-P2-CUSTOMER-STATUS-SIMPLIFICATION-SPRINT  
**Date:** 2026-06-07  
**Certifier:** Cursor agent

---

## Scope

Align runtime customer surfaces to **four business states only**. No new Constitution rules, workflows, or lifecycle states.

---

## Local verification

### pytest

```
tests/test_active_case_by_phone.py ...........
tests/test_collecting_case_memory_persistence.py ..
11 passed
```

### Simulation battery

```
Pass rate: 7/7 (100%)
BASE=http://127.0.0.1:8001
```

---

## BMW X5 regression

Phone `6265558001` — **PASS** (all lifecycle steps; see report §3)

Critical anti-regression checks:

- Collecting turns show **等客户补资料** — not 已提交办公室
- No green closure card before formal submit
- Formal submit → **已提交办公室** only after `formal_submit=true` + empty gaps

---

## Phone return

Phone `6265558002` — **PASS** (case id, state, missing fields restored)

---

## Deploy verification

| Target | Status |
|--------|--------|
| Cloud Run revision | **fiqa-api-00088-w6l** |
| Vercel Preview URL | **https://ui-6hc7cfoxk-andys-projects-1f411b73.vercel.app** |
| Alias | https://ui-waterwoods-andys-projects-1f411b73.vercel.app |
| Preview customer tab loads | **PASS** (HTTP 200) |
| Preview API `business_state` on lookup | **PASS** (`6265558002` → `awaiting_customer`) |

---

## Final verdict

## **GO**

- Four-state business model live on Cloud Run + Preview
- BMW regression + simulation battery 100% local; live API exposes `business_state`
- Customer surfaces show single status (no Status + Contact State split)
