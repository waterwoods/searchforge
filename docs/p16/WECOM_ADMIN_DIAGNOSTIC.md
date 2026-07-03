# WeCom Admin Diagnostic Runbook

**Track A only** — deterministic admin debugging for Enterprise WeCom 微信客服.  
**Not** product features, ADP, or media pipeline.

---

## Why gettoken PASS can still fail sync_msg

`cgi-bin/gettoken` only proves that **some** CorpID + Secret pair is valid for **that secret’s app scope**.

| Check | What it proves | What it does **not** prove |
|-------|----------------|----------------------------|
| `validate_wecom_gettoken.py` PASS | Secret matches CorpID; app can obtain `access_token` | `kf/sync_msg` permission |
| Callback verify PASS | Token + EncodingAESKey + CorpID correct | API pull permission |
| `validate_wecom_sync_msg.py` PASS | App may call `kf/sync_msg` for the bound KF account | Messages exist (need live test msg) |

**Common trap:** `WECOM_AGENT_SECRET` (自建应用 Secret) often passes gettoken but returns **48002** on `kf/sync_msg` because the KF API requires the **微信客服 Secret** (`WECOM_KF_SECRET`) and admin bindings below.

---

## Credential types (do not mix these up)

| Env var | Admin source (EN / 中文) | Used for |
|---------|--------------------------|----------|
| `WECOM_KF_SECRET` | WeChat Customer Service → API → Secret / 微信客服 → API → Secret | `gettoken` (KF scope), `kf/sync_msg`, `kf/send_msg` |
| `WECOM_AGENT_SECRET` | App Management → Self-built → CaseIQ AI Adapter → Secret / 应用管理 → 自建 → Secret | General app APIs; **often wrong for sync_msg** |
| `WECOM_CORP_SECRET` / `WECOM_SECRET` | Legacy aliases | Same resolution order as agent/corp secrets — treat as non-KF unless confirmed |
| `WECOM_KF_TOKEN` | KF callback → Token / 接收消息服务器 → Token | URL verify + decrypt callback only |
| `WECOM_KF_ENCODING_AES_KEY` | KF callback → EncodingAESKey / 接收消息服务器 → EncodingAESKey | Callback decrypt only |

**Callback credentials ≠ API Secret.** A working callback does not mean sync_msg will work.

---

## Error codes

### 48002 — API permission mismatch

**Meaning:** The `access_token` was issued, but this app/secret is **not allowed** to call `kf/sync_msg`.

**Typical causes:**
- Using `WECOM_AGENT_SECRET` instead of `WECOM_KF_SECRET`
- CaseIQ AI Adapter not listed under **可调用接口的应用** (callable apps)
- Wrong WeCom edition Secret (联合版 vs 独立版)

### 48007 — KF account not bound to app

**Meaning:** App may have KF API access, but this **客服账号** (`open_kfid`) is not authorized under **通过API管理微信客服账号**.

**Typical causes:**
- `WECOM_TEST_OPEN_KF_ID` does not match the account bound in admin
- Account bound to a different self-built app

### Other mapped codes

| errcode | Summary |
|---------|---------|
| 95011 / 95012 | 联合版 / 独立版 Secret mode mismatch |
| 60020 | Outbound IP not in 企业可信IP |
| 40001 | Invalid secret or CorpID mismatch |
| 0 | sync_msg permission OK |

---

## Admin runbook (Andy manual steps)

### Step 1 — Confirm 微信客服 mode

Enterprise WeCom Admin → **微信客服** / WeChat Customer Service.

Confirm you are on the correct edition (**联合版** vs **独立版**). Secret and API menus differ by edition.

### Step 2 — Find / copy 微信客服 Secret

Path: **微信客服 → API → Secret** (or equivalent in your edition console).

Copy the **微信客服 Secret** — not the self-built app Secret.

### Step 3 — Configure `WECOM_KF_SECRET`

In `.env.cloudrun` (local diagnostic file only — do not commit secrets):

```bash
WECOM_KF_SECRET=<微信客服 Secret>
WECOM_CORP_ID=<企业ID>
```

Unset or ignore `WECOM_AGENT_SECRET` for sync_msg testing if it causes confusion.

### Step 4 — Add CaseIQ AI Adapter to 可调用接口的应用

Path: **微信客服 → API → 可调用接口的应用** / callable apps.

Add **CaseIQ AI Adapter** (your self-built app). Without this → **48002**.

### Step 5 — Bind 客服账号 under 通过API管理微信客服账号

Path: **微信客服 → API → 通过API管理微信客服账号**.

Bind the target customer-service account to **CaseIQ AI Adapter**.

Copy the account’s `open_kfid` into:

```bash
WECOM_TEST_OPEN_KF_ID=wkxxxxxxxx
```

Without this → **48007**.

### Step 6 — Confirm callback URL / Token / EncodingAESKey

Path: **微信客服 → 接收消息服务器** (or app callback settings).

| Setting | Env var |
|---------|---------|
| URL | `https://<your-host>/api/wecom/kf/callback` |
| Token | `WECOM_KF_TOKEN` |
| EncodingAESKey | `WECOM_KF_ENCODING_AES_KEY` |

Run callback verify separately; callback PASS does not replace Step 4–5.

### Step 7 — Send one personal WeChat test message

From **personal WeChat** (not WeCom app), send a text message to the bound 客服账号.

Optional: capture callback `Token` from logs → `WECOM_TEST_CALLBACK_TOKEN` for a pull with pending messages.

### Step 8 — Run sync_msg diagnostic

```bash
cd /home/andy/searchforge
PYTHONPATH=. python3 scripts/validate_wecom_sync_msg.py
```

**PASS:** `errcode: 0` and diagnosis `SUCCESS: sync_msg permission works.`  
**FAIL:** follow printed `next_action` for your errcode.

---

## Diagnostic commands

| Command | Purpose |
|---------|---------|
| `PYTHONPATH=. python3 scripts/validate_wecom_gettoken.py` | Secret class + gettoken only |
| `PYTHONPATH=. python3 scripts/validate_wecom_sync_msg.py` | **Authoritative** sync_msg permission check |

---

## Common mistakes

1. **Agent Secret in `WECOM_KF_SECRET` slot** — gettoken passes, sync_msg 48002.
2. **Correct KF Secret but app not in 可调用接口的应用** — 48002.
3. **App callable but KF account not bound** — 48007.
4. **Wrong `open_kfid`** — 48007 or empty pulls.
5. **Confusing callback Token with API Secret** — callback works; sync_msg fails.
6. **联合版 Secret on 独立版 corp (or vice versa)** — 95011 / 95012.
7. **Cloud Run IP not whitelisted** — 60020 (if IP restriction enabled).

---

## Pass / fail log examples

### gettoken PASS with risky secret class (warning)

```
=== WeCom credential readiness ===
  WECOM_KF_SECRET: unset
  WECOM_AGENT_SECRET: SET
  resolved_secret_class: WECOM_AGENT_SECRET
  secret_fingerprint: agen…5678 (len=32)

  WARNING: gettoken PASS does not imply kf/sync_msg permission.

=== gettoken result ===
  errcode: 0
  gettoken: PASS
```

**Interpretation:** Credentials are valid for the **agent app**, not proof of KF API access. Run `validate_wecom_sync_msg.py`.

### sync_msg FAIL — 48002

```
=== sync_msg result ===
  errcode: 48002
  errmsg: api forbidden

=== diagnosis ===
  API permission mismatch. Check KF Secret, 可调用接口的应用, app permissions.

=== next action ===
  Enterprise WeCom Admin → 微信客服 → API → 可调用接口的应用 → add CaseIQ AI Adapter...
  sync_msg: FAIL
```

### sync_msg PASS

```
=== sync_msg result ===
  errcode: 0
  errmsg: ok
  message_count: 1
  has_next: false

=== diagnosis ===
  SUCCESS: sync_msg permission works.
  sync_msg: PASS
```

---

## Track A vs Track B

- **Track A (preferred):** Enterprise WeCom 微信客服 + `kf/sync_msg` — use this runbook until sync_msg PASS.
- **Track B (fallback):** Only after this diagnostic proves Track A is blocked by irrecoverable admin constraints — not because gettoken alone passed.

---

## Related

- `docs/p16/adr/ADR_004_ENTERPRISE_WECOM_CHANNEL_INTEGRATION.md`
- `docs/p16/WECOM_VERTICAL_SLICE_PROMPT1.md`
- `scripts/validate_wecom_gettoken.py`
- `scripts/validate_wecom_sync_msg.py`
- `services/fiqa_api/wecom/diagnostics.py`
