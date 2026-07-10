# P19H-3g-2 Phase 1 — WeCom Customer Display Label Evidence

**Date:** 2026-07-10  
**Branch:** `sprint/p16-trust-layer`  
**Verdict:** **PASS (local tests + build)**

---

## 1. Goal

Stop Workbench showing identical **「企业微信客户」** for every WeCom customer. Auto-set broker-visible label:

`微信客户 · {external_userid_last6}`

Without asking customer name, CRM merge, schema change, or `kf/customer/batchget`.

---

## 2. Why Workbench showed generic name

| Layer | Issue |
|-------|-------|
| Claim / Add Car create | `bind_case_channel_identity()` stored `wecom_external_userid` but not `customer_name` |
| Workbench API | `sanitize_case_for_workbench_api()` masks full `wecom_external_userid` |
| UI fallback | `resolveCustomerDisplayName()` could not derive suffix without masked field |

---

## 3. New display priority

| Rank | Source |
|------|--------|
| 1 | Meaningful `customer_name` (broker seed, extracted name, phone label) — **never overwritten** |
| 2 | Auto label at bind: `微信客户 · {last6}` |
| 3 | UI final fallback: `企业微信客户` (no ext available) |

**Customer-facing Status Card:** uses `customer_name` when meaningful; auto suffix labels shown as **「微信客户」** only (no suffix in WeCom chat).

---

## 4. What changed

| File | Change |
|------|--------|
| `services/fiqa_api/wecom/identity.py` | `微信客户 · {last6}` format; `is_generic_wecom_customer_name()`; `wecom_customer_facing_display_name()` |
| `services/fiqa_api/inbox_triage/case_store.py` | `bind_case_channel_identity()` backfills `customer_name` when empty/generic |
| `services/fiqa_api/wecom/reply.py` | Status Card uses customer-facing name helper |
| `ui/src/features/intake/utils/intakePure.ts` | Rely on `customer_name`; legacy label polish; no masked-ext fallback |
| `tests/test_wecom_identity_b0_extractors.py` | Updated label assertions |
| `tests/test_p19h3g2_wecom_customer_display_label.py` | **New** — bind, Claim, Add Car, API mask, Status Card |

---

## 5. What did not change

- No schema migration
- No `kf/customer/batchget` / `externalcontact/get`
- No customer name prompts in Claim / Add Car flows
- Full `external_userid` still masked in Workbench API
- Claim / Add Car / Status / End Card / Single Active Task logic unchanged

---

## 6. Tests

```bash
PYTHONPATH=. python3 -m pytest tests/test_wecom_identity_b0_extractors.py -q
# 31 passed

PYTHONPATH=. python3 -m pytest tests/test_p19h3g2_wecom_customer_display_label.py -q
# 10 passed

PYTHONPATH=. python3 -m pytest tests -q -k "claim"
# PASS

PYTHONPATH=. python3 -m pytest tests -q -k "h5"
# PASS

cd ui && npm run build
# PASS (~24s)
```

---

## 7. Deploy result

| Item | Value |
|------|-------|
| Commit | _(filled after deploy)_ |
| Backend revision | _(filled after deploy)_ |
| GIT_SHA | _(filled after deploy)_ |
| Frontend deploy | Yes — `intakePure.ts` changed |
| `/health/live` | _(filled after deploy)_ |
| `/readyz` | _(filled after deploy)_ |

### Post-deploy smoke (operator)

1. Fresh WeCom customer starts Claim → Workbench row shows `微信客户 · {last6}`
2. Seeded case with `customer_name=张先生` → unchanged after bind
3. API case list: `wecom_external_userid` null; `customer_name` has suffix only
4. Claim Start / Status / basics flow unchanged

---

## 8. Known limitations (Phase 2+)

- No WeChat **nickname** from API yet
- No broker **remark** from 客户联系
- No real-name verification
- `kf/customer/batchget` deferred to Phase 2
- Existing cases without re-bind keep empty name until next inbound message triggers bind

---

*P19H-3g-2 Phase 1 — STOP after deploy smoke.*
