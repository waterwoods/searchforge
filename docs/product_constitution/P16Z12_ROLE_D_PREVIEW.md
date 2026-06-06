# P16-Z12 Phase 7 — Role D Preview Reality Test

**Date:** 2026-06-02

---

## Method

| Attempt | Result |
|---------|--------|
| Role D battery against deployed Preview URL | ❌ No `--url` flag on `run_role_d_memory_battery.py` |
| Role D via browser on Preview | ❌ CORS disallows Preview origin on Cloud Run |
| Role D on **local** module path | ✅ Executed (rules engine, `LLM_GENERATION_ENABLED=0`) |

**Documented limitation:** Role D preview automation blocked; local module battery used as **engine proxy only** — not Preview parity proof.

---

## Local Role D (engine proxy)

| Metric | Result | Target | Met? |
|--------|--------|--------|------|
| **Role D reread** | **82.6** | ≥80 | ✅ |
| **Need WeChat** | **0/10** | ≤2/10 | ✅ |
| **Waiting-on** | **9/9** | ≥7/9 | ✅ |
| **Claims retention** | **71%** | ≥70 | ✅ |

Source: `docs/product_constitution/.role_d_results/role_d_battery.json` (run 2026-06-02 Z12 session).

---

## Deployed backend proxy (acceptance paste)

Not Role D — single-turn sprint cases on Cloud Run:

| Metric | Approximation |
|--------|----------------|
| Reread-equivalent | **~15/100** (0/3 cases usable without WeChat) |
| Need WeChat | **3/3** |
| Waiting-on | **0/3** |
| Claims retention | **0%** on case 3 |

---

## PASS / FAIL

| Scope | Verdict |
|-------|---------|
| **Role D on deployed Preview/backend** | **FAIL** (not run; CORS + no deploy) |
| **Role D local engine** | **PASS** |

**Overall Phase 7:** **FAIL** for sprint acceptance criteria ("Role D or deployed backend validation ≥80 reread on **deployed** path").
