# P29B — Lightweight Identity & Session Foundation

**Status:** Implemented — production foundation (not a Customer Account system)  
**Date:** 2026-07-19  
**Sprint:** P29B  
**Authority class:** Product + technical contract for Resume Current Task identity  
**Does not supersede:** `docs/product/p20_product_north_star.md`, P29 Service Home, Claim workflow, Broker UI case facts  
**Decision log:** D-012 (`docs/product/decision_log.md`)

---

## 0. One-sentence freeze

OpenID is a **technical resume key** for one Active Case — not a customer profile, account, or history system.

---

## 1. User-facing objective (P20 Production Loop)

**Exactly one objective**

A returning Mini Program customer can see **Continue Current Task** when they still have an Active Case, without building a Customer Account product.

**Explicit out of scope**

- Profile Center / My Account  
- Policy List / Claim History  
- Multi-session picker / Customer Dashboard / Vehicle Center  
- Displaying OpenID to customers or brokers  
- Replacing phone/name contact fields on the case  

---

## 2. Architecture

```text
Mini Program
  → wx.login (code)
  → POST /api/h5/customer/session
  → jscode2session OpenID          ← ephemeral; never stored raw; never returned
  → person_link_key (HMAC)         ← opaque technical id
  → Customer Contact (optional)    ← name/phone on Active Case when collected
  → Active Case (at most one)      ← resume_token for Continue
```

Service Home remains the product root (D-011). Identity only answers: “Is there an Active Case to continue?”

---

## 3. Database relationship (not an account model)

```text
┌─────────────────────┐
│  WeChat OpenID      │  technical only — NEVER persisted / displayed
└─────────┬───────────┘
          │ HMAC(pepper)
          ▼
┌─────────────────────┐       1         ┌──────────────────────────┐
│ person_link_key     │────────────────▶│ mp_customer_active_case  │
│ (opaque wx_…)       │                 │ person_link_key PK       │
└─────────────────────┘                 │ case_id                  │
          │                             └────────────┬─────────────┘
          │ optional stamp                           │ 0..1 Active
          ▼                                          ▼
┌─────────────────────┐                 ┌──────────────────────────┐
│ service_records /   │◀────────────────│ Active Case              │
│ claim case          │                 │ customer_name (opt)      │
│ person_link_key     │                 │ customer_phone (opt)     │
│ entry_channel=      │                 │ case_status              │
│   mini_program      │                 │ source → WeChat Mini     │
└─────────────────────┘                 │            Program       │
                                        └──────────────────────────┘
```

There is **no** `customers` / `profiles` / `accounts` table.

---

## 4. Security notes

1. **Never return OpenID** from `/api/h5/customer/session` or start-claim.  
2. **Never display OpenID** (or raw person_link_key) in Broker UI or customer UI.  
3. Persist only `person_link_key = HMAC(pepper, openid)`. Rotate pepper = loss of resume linkage (acceptable; Start New Claim still works).  
4. Resume credential remains the signed `h5t1.*` token — OpenID alone does not authorize task writes.  
5. Simulate codes (`sim:…`) require `WECHAT_MP_ALLOW_SIMULATE=1` (dev/test only).  
6. Env: `WECHAT_MP_APP_ID` / `WECHAT_MP_APP_SECRET` (fallback `WECHAT_APP_ID` / `WECHAT_APP_SECRET`).

---

## 5. Migration impact

| Change | Impact |
|--------|--------|
| Table `mp_customer_active_case` | Additive; auto-create on first use; SQL in `005_p29b_mp_customer_active_case.sql` |
| Case fields `entry_channel`, `person_link_*`, `created_by_actor` | Additive JSON / structured_payload keys |
| Broker source label | Display-only: “WeChat Mini Program” |
| Existing anon sessions | Still work; resume stays local until wx.login succeeds |

Rollback: drop `mp_customer_active_case`; customers fall back to local resume token only.

---

## 6. Resume rules

| Condition | Service Home primary |
|-----------|----------------------|
| OpenID → Active Case bound and open | Continue Current Task |
| No Active Case | Start New Claim |
| Tap Start New Claim while Active Case exists | Policy modal → Continue / Contact broker (P30 / D-013; no second case) |

---

## 7. Broker UI contract

Broker continues to see:

- Customer Name  
- Phone  
- Case Number  
- Case Status  
- Source: **WeChat Mini Program**  

Broker must **not** see OpenID or person_link_key.
