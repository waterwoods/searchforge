# P19H-3g-4 — WeCom Customer Profile Lookup Evidence

**Date:** 2026-07-10  
**Branch:** `sprint/p16-trust-layer`  
**Sprint:** P19H-3g-4 Phase 2 — nickname / avatar / unionid via `kf/customer/batchget`

---

## 1. Goal

Best-effort fetch WeCom KF customer identity (nickname, avatar, unionid) at channel bind so Workbench can distinguish customers without asking for name, CRM merge, or schema change.

---

## 2. Current identity problem (before Phase 2)

Phase 1 set `customer_name = 微信客户 · {last6}` at bind. Brokers could distinguish rows by suffix but had no WeChat nickname or avatar.

---

## 3. Real WeChat ID availability

| Field | Available? | Notes |
|-------|------------|-------|
| Real WeChat ID (微信号) | **No** | WeCom KF `batchget` does not return user wxid; documented as unavailable |
| `external_userid` | **Yes** (internal) | Already persisted; masked in API |
| Nickname | **Yes** (when API permits) | `customer_list[].nickname` |
| Avatar | **Yes** (when API permits) | `customer_list[].avatar` |
| Unionid | **Conditional** | Requires corp 开放平台 binding |

Live production call not made during implementation; behavior validated via mocked API + unit tests. Live smoke will record actual field availability.

---

## 4. API used

**Endpoint:** `POST /cgi-bin/kf/customer/batchget`  
**Token:** `WECOM_KF_SECRET` via existing `get_access_token()` (same path as `sync_msg` / `send_msg`)  
**Request:** `{ "external_userid_list": ["wm..."], "need_enter_session_context": 0 }`  
**Module:** `services/fiqa_api/wecom/customer_profile.py`

**Not used:** `externalcontact/get` (requires 客户联系 secret — not in env)

**48h rule:** Customer must have messaged within 48h or id may appear in `invalid_external_userid`; flow falls back to suffix label.

---

## 5. Display priority (implemented)

| Rank | Source |
|------|--------|
| 1 | `extra.customer_identity.broker_manual_display_name` (future) |
| 2 | `extra.customer_identity.wecom_remark` (future) |
| 3 | `extra.customer_identity.wecom_nickname` |
| 4 | Meaningful `customer_name` (broker seed, etc.) |
| 5 | `微信客户 · {last6}` |
| 6 | `企业微信客户` |

Nickname promoted to `customer_name` only when current name is empty/generic/suffix. Customer-facing Status Card uses `wecom_customer_facing_display_name()` — nicknames shown; suffix labels collapsed to「微信客户」.

---

## 6. What changed

| File | Change |
|------|--------|
| `services/fiqa_api/wecom/customer_profile.py` | **New** — `fetch_kf_customer_profile`, TTL cache, `merge_customer_identity` |
| `services/fiqa_api/wecom/identity.py` | `resolve_wecom_workbench_display_name()` priority resolver |
| `services/fiqa_api/inbox_triage/case_store.py` | Profile lookup on `bind_case_channel_identity`; cache in `extra.customer_identity` |
| `services/fiqa_api/inbox_triage/case_attachment_api.py` | Sanitize `extra.customer_identity` (no full ext id) |
| `tests/test_p19h3g4_wecom_customer_profile_lookup.py` | **New** — 15 tests |

---

## 7. What did not change

- No schema migration
- No customer name prompts
- No CRM merge
- No `externalcontact/get`
- No Workbench UI redesign (nickname flows via `customer_name`)
- Full `external_userid` still masked in API
- Claim / Add Car / Single Active Task logic unchanged

---

## 8. Tests

```bash
PYTHONPATH=. python3 -m pytest tests/test_p19h3g4_wecom_customer_profile_lookup.py -q
# 15 passed

PYTHONPATH=. python3 -m pytest tests/test_p19h3g2_wecom_customer_display_label.py -q
# PASS

PYTHONPATH=. python3 -m pytest tests/test_p19h3f5_single_active_task_per_lane.py -q
# PASS

PYTHONPATH=. python3 -m pytest tests -q -k "claim"
# PASS

PYTHONPATH=. python3 -m pytest tests -q -k "h5"
# PASS
```

No UI file changes — frontend deploy not required.

---

## 9. Deployment

| Item | Value |
|------|-------|
| Commit | _(filled post-deploy)_ |
| Backend revision | _(filled post-deploy)_ |
| GIT_SHA | _(filled post-deploy)_ |
| Frontend deploy | **No** — backend-only |

---

## 10. Live smoke result

_(Operator: send「我要理赔」from real WeCom customer; verify Workbench row + logs)_

| Check | Result |
|-------|--------|
| Profile lookup attempted | _pending_ |
| Nickname in Workbench | _pending_ |
| Fallback suffix if API empty | _pending_ |
| Full external_userid hidden | _pending_ |
| Claim flow works | _pending_ |

---

## 11. Known limitations

- Real WeChat ID (微信号) **not available** from KF API
- Nickname may fail: 48h activity window, permission, or empty response
- Broker remark requires 客户联系 secret — future sprint
- Avatar URL stored in `extra.customer_identity`; UI avatar not added this sprint
- Profile TTL: 24h; skip re-fetch when nickname already cached

---

## 12. Next recommendation

1. Live smoke with Chen pilot customer — record actual nickname/avatar/unionid availability
2. Optional Workbench avatar chip (if avatar URL stable)
3. Anti double-click guard / latency (separate sprint)
4. Broker manual display name (Phase 3)

---

*P19H-3g-4 — STOP after deploy smoke.*
