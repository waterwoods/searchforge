# P19H-3g-2 — WeCom Customer Identity Display Recon

**Date:** 2026-07-10  
**Sprint:** P19H-3g-2 Recon  
**Status:** Recon complete — **GO (Phase 1)** recommended  
**Scope:** WeCom inbound identity fields, Workbench display, broker lookup; no schema change, no customer name prompts

---

## Executive summary

WeCom **already provides** a stable customer anchor (`external_userid`) on every `sync_msg` row, and we **already persist** it on cases via `wecom_external_userid`. We do **not** receive nickname, remark, avatar, or unionid in the callback or `sync_msg` payload.

Workbench shows the generic label **「企业微信客户」** because:

1. **Claim** and **Add Car** case-creation paths bind `wecom_external_userid` but **never set `customer_name`**.
2. The UI fallback that could derive a suffix label needs `wecom_external_userid`, but **`sanitize_case_for_workbench_api()` masks it to `null`** before the response leaves the API.
3. `wecom_customer_display_label()` exists and is used for **minimal lanes** and **media attachment metadata**, but not for Claim / Add Car.

**WeCom profile lookup is feasible** for nickname via **`POST /cgi-bin/kf/customer/batchget`** using the existing **`WECOM_KF_SECRET`** token path. No code calls this today. **`externalcontact/get`** (broker remark / CRM name) requires a separate **客户联系** secret that is **not** in env.

**Do not ask the customer for their name** in the normal accident / add-car flow. Use platform identity first; real-name confirmation is a later broker workflow.

| Recommendation | Verdict |
|----------------|---------|
| Phase 1 — persist suffix display label at bind time | **GO** (small, no-risk) |
| Phase 2 — best-effort `kf/customer/batchget` nickname cache | **GO** (non-blocking) |
| Phase 3 — broker manual rename / CRM merge | Future |
| Ask customer「你叫什么」in Claim / Add Car | **NO** |

---

## 1. Current state — inbound identity data

### 1.1 Callback payload (kf event notification)

Source: `services/fiqa_api/wecom/event_parser.py`, `routes/wecom_kf_callback.py`

The decrypted callback XML is parsed to flat tags. For kf message notifications, logged fields include:

| Field | Present | Customer identity? |
|-------|---------|-------------------|
| `MsgType` | ✅ | — |
| `Event` | ✅ | — |
| `Token` | ✅ | sync_msg cursor token (not customer id) |
| `OpenKfId` | ✅ | 客服账号 id |
| `CreateTime` | ✅ | — |
| `ToUserName` | ✅ | corp id |

**No customer fields** in callback XML. Customer identity arrives only after **`kf/sync_msg`**.

### 1.2 sync_msg message row (normalized channel event)

Source: `services/fiqa_api/wecom/sync_msg.py`, `normalize.py`, `synthetic_fixtures.py`

Per customer message (`origin == 3`, text/image/file):

| Field | Persisted on case? | Notes |
|-------|-------------------|-------|
| `external_userid` | ✅ → `wecom_external_userid` | Primary WeCom customer anchor |
| `open_kfid` / `open_kf_id` | ✅ → `wecom_open_kf_id` | Required for `kf/send_msg` |
| `msgid` | Evidence / dedup only | |
| `msgtype` | Routing | text / image / file |
| `send_time` | Timestamps | |
| `origin` | Routing filter | 3 = customer |
| `text.content` | Source text / extractors | Phone/VIN/ZIP regex only |
| `image.media_id` / `file` | Attachments | |
| `nickname` | ❌ | Not in API row |
| `remark` | ❌ | Not in API row |
| `avatar` | ❌ | Not in API row |
| `unionid` | ❌ | Not in API row |
| `name` | ❌ | Not in API row |

Normalized event shape (`normalize_text_message` / `normalize_media_message`):

```python
{
  "event_type": "message.received",
  "channel": "wecom_kf",
  "external_userid": "...",
  "open_kf_id": "...",
  "msg_id": "...",
  "msgtype": "text|image|file",
  "text": "...",        # text only
  "phone": None,        # regex from text only
  "raw": { ... sync_msg item ... },
}
```

### 1.3 Case persistence today

Source: `services/fiqa_api/inbox_triage/case_store.py`

| Field | Schema | Set when |
|-------|--------|----------|
| `wecom_external_userid` | Top-level case JSON | `bind_case_channel_identity()` — Claim, Add Car, minimal lanes, media |
| `wecom_open_kf_id` | Top-level case JSON | Same |
| `customer_name` | Top-level case JSON | **Only** minimal lanes (`minimal_lanes.py`) via `wecom_customer_display_label()`; **not** Claim / Add Car create |
| `customer_phone` | Top-level case JSON | Text extractors when customer types phone |
| `extra.customer_identity` | — | **Does not exist yet** |
| Attachment `customer_label` | `case_attachments[]` | Media intake only — not promoted to case `customer_name` when bound |

**Claim create** (`claim_basics._create_claim_case`): binds `wecom_external_userid`, **no** `update_case_customer`.

**Add Car Start** (`active_case_bridge.create_or_attach_draft_case_for_start_click`): binds `wecom_external_userid`, **no** `customer_name`.

**Media intake** (`media_intake.py`): computes `customer_label = wecom_customer_display_label(external_userid)` for attachment metadata and unassigned intake source text, but **does not** write `customer_name` on the bound Claim/Add Car case.

### 1.4 Why Workbench shows 「企业微信客户」

Display chain:

```
API case row
  customer_name = null          (Claim / Add Car never set)
  wecom_external_userid = "wm…" (stored)
       ↓
sanitize_case_for_workbench_api()
  wecom_external_userid → null  (masked)
       ↓
UI resolveCustomerDisplayName()
  name empty, phone empty, ext null
       ↓
fallback → "企业微信客户"
```

Evidence: `docs/evidence/p19h3a_claim_workbench_visibility_2026_07_09.md` — production Claim case with empty `customer_name`, cosmetic only.

Status Card path is separate: `reply._claim_status_customer_name()` falls back to **「微信客户」** when `customer_name` is empty (`services/fiqa_api/wecom/reply.py`).

### 1.5 Existing display helper (backend)

`services/fiqa_api/wecom/identity.py` — `wecom_customer_display_label()`:

| Priority | Value |
|----------|-------|
| 1 | `customer_name` if provided |
| 2 | Formatted US phone |
| 3 | `企业微信客户（尾号 {last4}）` |
| 4 | `企业微信客户` |

**Gap vs product principle:** uses **last 4** chars and **企业微信客户** prefix; target is **`微信客户 · {last6}`**.

UI mirror: `ui/src/features/intake/utils/intakePure.ts` — `resolveCustomerDisplayName()` uses same last-4 / 企业微信客户 pattern when `wecom_external_userid` is present (but API masking prevents this path today).

### 1.6 Broker manual lookup

| Method | Available today? |
|--------|------------------|
| Search Workbench by `external_userid` | **No** — masked in API (`case_attachment_api.sanitize_case_for_workbench_api`) |
| Search Workbench by nickname | **No** — nickname not stored |
| Distinguish multiple WeCom customers in list | **Poor** — all show same generic label |
| WeCom 微信客服 admin console | **Yes** — operator can find session by customer; `external_userid` is the stable key there |
| Full `external_userid` in broker UI | **Intentionally blocked** — H5 tokens use `external_userid_ref()` (8-char HMAC), not full id |

Broker can manually correlate via **WeCom console + accident context** (time, photos, brief). Workbench should show at least **suffix label** so list rows are distinguishable without exposing full id.

---

## 2. WeCom API feasibility

### 2.1 Current credentials & token path

| Env var | Purpose | In codebase |
|---------|---------|-------------|
| `WECOM_KF_SECRET` | 微信客服 Secret — **correct** for `sync_msg`, `send_msg`, `media/get` | `wecom/config.py`, `access_token.py` |
| `WECOM_AGENT_SECRET` / `WECOM_CORP_SECRET` | Self-built app — often **48002** on kf APIs | Fallback only; documented trap |
| `WECOM_CORP_ID` | Corp id | ✅ |
| `WECOM_KF_TOKEN` + AES key | Callback crypto | ✅ |
| **客户联系 secret** | `externalcontact/*` | **Not configured** |

Token fetch: `GET https://qyapi.weixin.qq.com/cgi-bin/gettoken` with `corpsecret=WECOM_KF_SECRET` (`access_token.py`).

**Current app channel:** **微信客服 (WeCom KF)** — not direct 企业微信客户联系 chat. Chen pilot uses KF variant per `docs/p19d05_wechat_native_guided_workflow_channel_recon.md`.

### 2.2 Option A — 微信客服客户基础信息 (recommended)

**Endpoint:** `POST /cgi-bin/kf/customer/batchget?access_token=ACCESS_TOKEN`

| Item | Detail |
|------|--------|
| Token | **Must** be from 微信客服 Secret (`WECOM_KF_SECRET`) — same as today |
| Request | `{ "external_userid_list": ["wm..."], "need_enter_session_context": 0 }` |
| Returns | `nickname`, `avatar` (limited for third-party), `gender`, `unionid` (needs 开放平台绑定), optional `enter_session_context` |
| `external_userid` compatibility | **Yes** — same `wm…` id from `sync_msg` / callback pipeline |
| Permission | 微信客服 API scope; admin must grant app access (same class as `sync_msg`) |
| **48-hour window** | Customer must have messaged or entered session in last **48h** or id lands in `invalid_external_userid` |
| Failure modes | Missing secret → skip; 48002 → log + fallback; invalid id → fallback; timeout → non-blocking |

**No production call made in this recon.** Official doc: [获取客户基础信息](https://developer.work.weixin.qq.com/document/path/95159).

### 2.3 Option B — 企业微信客户联系详情 (secondary / broker remark)

**Endpoint:** `GET /cgi-bin/externalcontact/get?external_userid=…`

| Item | Detail |
|------|--------|
| Token | **客户联系** secret — **not** in current env |
| Returns | `name` (WeChat nickname for type=1), `follow_user[].remark` (per-member broker remark), `avatar`, `unionid` |
| KF-only customers | May work if same `external_userid` exists in 客户联系; **not guaranteed** for pure KF entry without 联系我 |
| Use case | Broker remark name, CRM-style enrichment **after** 客户联系 secret + permission |

**Not recommended for Phase 1.** Defer until Chen corp configures 客户联系 API secret.

### 2.4 API comparison

| Capability | `kf/customer/batchget` | `externalcontact/get` |
|------------|------------------------|----------------------|
| Works with current `WECOM_KF_SECRET` | ✅ | ❌ |
| WeChat nickname | ✅ `nickname` | ✅ `name` |
| Broker remark | ❌ | ✅ `follow_user.remark` |
| Avatar | ✅ (restrictions) | ✅ (restrictions) |
| Unionid | ✅ if dev account bound | ✅ if dev account bound |
| 48h activity rule | ✅ | No (but customer must exist in 客户联系) |
| Code exists today | ❌ | ❌ |

---

## 3. Recommended display name policy

**Principle:** Platform identity only in customer-facing flow. Nickname is **display label**, not legal name.

### 3.1 Priority (broker Workbench + Status Card)

| Rank | Source | Example |
|------|--------|---------|
| 1 | `extra.customer_identity.broker_manual_display_name` (future) | 「陈总备注：李先生」 |
| 2 | WeCom broker remark (`externalcontact` follow_user.remark) | When Phase 2b enabled |
| 3 | WeCom / WeChat nickname (`kf/customer/batchget`) | 「张三」 |
| 4 | `customer_name` already on case (includes suffix label) | 「微信客户 · rmxcw6」 |
| 5 | Suffix fallback | `微信客户 · {external_userid_last6}` |
| 6 | Generic | `企业微信客户` (only when no `external_userid`) |

### 3.2 Exposure rules

| Data | Store | Show in Workbench | Show to customer (WeCom reply) |
|------|-------|-------------------|-------------------------------|
| Full `external_userid` | Case JSON / `extra.customer_identity` | **Never** | **Never** |
| Last 6 of `external_userid` | In `customer_name` suffix label | ✅ | **Never** |
| Nickname | `extra.customer_identity.wecom_nickname` | ✅ as display | **Never** unless customer already uses it in chat |
| Unionid | `extra` only | Internal / future merge | **Never** |
| Legal / confirmed name | Future broker field | After explicit broker confirm | Only after broker workflow |

### 3.3 Ask customer for name?

**NO** — not in Claim Start, basics collection, Add Car, or Status Card. Phone may still be collected when needed for carrier workflow; name confirmation is **broker-side later**.

---

## 4. Minimal implementation plan

### Phase 1 — Suffix label at bind (GO now)

**Goal:** Every case with `wecom_external_userid` gets a distinguishable Workbench label without API calls or schema change.

1. Update `wecom_customer_display_label()`:
   - Suffix: **last 6** chars (not 4)
   - Format: **`微信客户 · {suffix}`** (align Status Card fallback wording)
2. Central hook in `bind_case_channel_identity()` (or thin wrapper):
   - If `customer_name` empty → `update_case_customer(case_id, customer_name=label)`
   - **Never overwrite** non-empty `customer_name` (broker seed, phone-derived, future manual)
3. Mirror UI fallback in `intakePure.resolveCustomerDisplayName()` for consistency
4. Optionally add `extra.customer_identity = { display_suffix, bound_at }` — **no full external_userid in API responses**

**Risk:** Low. Additive. Claim / Add Car / Status flows unchanged.

**Estimated touch:** ~3–5 files, <80 LOC.

### Phase 2 — Best-effort nickname lookup (GO next)

1. New `services/fiqa_api/wecom/customer_profile.py`:
   - `fetch_kf_customer_profile(cfg, external_userid) -> dict | None`
   - Uses existing `get_access_token(cfg)`
   - Timeout 2–3s; log errcode; never raise into slice
2. Call on **first bind** or first inbound when `extra.customer_identity.wecom_nickname` absent
3. Cache in `extra.customer_identity`:
   ```json
   {
     "wecom_nickname": "...",
     "wecom_avatar_url": "...",
     "profile_source": "kf/customer/batchget",
     "profile_fetched_at": "2026-07-10T...",
     "display_suffix": "rmxcw6"
   }
   ```
4. If nickname returned → update `customer_name` **only if** still auto-generated (prefix `微信客户 ·` or empty)
5. Admin: confirm 微信客服 app has **获取客户基础信息** permission

**Failure:** Flow continues; suffix label from Phase 1 remains.

### Phase 3 — Broker tools (future)

- Workbench manual display name / remark (writes `broker_manual_display_name`)
- Optional `externalcontact/get` when 客户联系 secret available
- CRM merge — **out of scope**

---

## 5. Proposed tests

| # | Test | Phase |
|---|------|-------|
| 1 | `external_userid` bound, empty name → Workbench `customer_name` = `微信客户 · {last6}` | 1 |
| 2 | Nickname from mocked `batchget` → Workbench shows nickname | 2 |
| 3 | Broker manual name (future) wins over nickname | 3 |
| 4 | `batchget` failure / timeout → case created; suffix label still set | 2 |
| 5 | Customer WeCom reply / Status Card does not contain full `external_userid` | 1 |
| 6 | Two customers → list shows different suffix labels | 1 |
| 7 | Claim Start / Status / End unchanged | 1 |
| 8 | Add Car Start / photo flow unchanged | 1 |
| 9 | `bind_case_channel_identity` does not overwrite seeded `customer_name` | 1 |
| 10 | `sanitize_case_for_workbench_api` still masks `wecom_external_userid` | 1 |

Existing tests to update: `tests/test_wecom_identity_b0_extractors.py` (suffix format).

---

## 6. Risks

| Risk | Mitigation |
|------|------------|
| Nickname ≠ legal name | Label only; no「已验证姓名」copy |
| 48h `batchget` invalid id | Phase 1 suffix always works |
| Overwriting broker-set name | Only fill when `customer_name` empty or auto-prefix |
| `external_userid` leak via API | Keep masking; store full id server-side only |
| Wrong secret (48002) | Use `WECOM_KF_SECRET` only; diagnostics already document trap |
| Asking customer name | **Explicitly out of scope** |

---

## 7. Files to change (implementation reference)

### Phase 1

| File | Change |
|------|--------|
| `services/fiqa_api/wecom/identity.py` | `微信客户 · {last6}` format |
| `services/fiqa_api/inbox_triage/case_store.py` | Auto `customer_name` on bind when empty |
| `services/fiqa_api/wecom/reply.py` | Align Status Card fallback with same resolver |
| `ui/src/features/intake/utils/intakePure.ts` | Match suffix format in UI fallback |
| `tests/test_wecom_identity_b0_extractors.py` | Update assertions |
| `tests/test_wecom_claim_basics.py` or bind test | Assert name set on claim create |

### Phase 2

| File | Change |
|------|--------|
| `services/fiqa_api/wecom/customer_profile.py` | **New** — `kf/customer/batchget` client |
| `services/fiqa_api/wecom/slice.py` or `case_store.py` | Trigger profile fetch post-bind |
| `tests/test_wecom_customer_profile.py` | **New** — mocked HTTP |

### No change (this sprint)

- Schema / migrations
- Claim / Add Car state machines
- Customer-facing「你叫什么」prompts
- Workbench layout redesign

---

## 8. GO / HOLD

| Scope | Verdict | Rationale |
|-------|---------|-----------|
| **Phase 1** — suffix label at bind | **GO** | Fixes root cause; tiny diff; no API dependency |
| **Phase 2** — `kf/customer/batchget` | **GO** (after Phase 1) | Fits existing KF secret; non-blocking |
| **Phase 2b** — `externalcontact/get` | **HOLD** | No 客户联系 secret in env |
| **Ask customer name** | **HOLD / NO** | Violates product principle |
| **CRM merge** | **HOLD** | Out of scope |

**Overall: GO** for Phase 1 immediately; Phase 2 in following sprint.

---

## 9. Answers to recon questions

| Question | Answer |
|----------|--------|
| Callback payload customer identifiers? | **None** — only `Token`, `OpenKfId`; customer id in `sync_msg` |
| Persist `external_userid`? | **Yes** → `wecom_external_userid` |
| Persist nickname/remark/avatar? | **No** |
| Why generic Workbench name? | **No `customer_name` on Claim/Add Car** + **API masks `wecom_external_userid`** |
| Broker search by `external_userid`? | **Not in Workbench**; use WeCom admin; suffix label helps list disambiguation |
| Feasible API? | **`kf/customer/batchget`** with `WECOM_KF_SECRET` — **yes** |
| Ask customer name? | **NO** |

---

## Related

| Doc | Role |
|-----|------|
| `docs/p19d05_wechat_native_guided_workflow_channel_recon.md` | Chen uses KF channel |
| `docs/p16/WECOM_ADMIN_DIAGNOSTIC.md` | KF vs Agent secret |
| `docs/evidence/p19h3a_claim_workbench_visibility_2026_07_09.md` | Empty name on production Claim |
| `docs/pilot/p19h3g_pilot_readiness_audit_chen_2026_07_10.md` | 「微信客户」cosmetic ack |
| `services/fiqa_api/wecom/identity.py` | Current display helper |
| `services/fiqa_api/inbox_triage/case_attachment_api.py` | API masking |

---

*P19H-3g-2 recon — documentation only unless Phase 1 explicitly scheduled. STOP.*
