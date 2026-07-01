# WeCom KF Callback Spike (Prompt 3)

**Date:** 2026-06-26  
**Scope:** Technical spike only — prove Enterprise WeCom can reach Cloud Run, verify/decrypt, and emit structured logs.  
**Authority:** ADR-004 Phase 0 · Decision Freeze (no engine integration)

---

## 1. Files Created

| File | Purpose |
|------|---------|
| `services/fiqa_api/routes/wecom_kf_callback.py` | GET/POST `/api/wecom/kf/callback` handlers |
| `services/fiqa_api/wecom/config.py` | Env-based credential loader |
| `services/fiqa_api/wecom/event_parser.py` | Decrypted XML → structured log payload |
| `services/fiqa_api/wecom/crypto/WXBizMsgCrypt3.py` | Tencent official crypto (Python 3 vendored) |
| `services/fiqa_api/wecom/crypto/ierror.py` | Tencent error codes |
| `tests/test_wecom_kf_callback.py` | Unit tests (crypto round-trip + routes) |
| `scripts/test_wecom_kf_callback_local.py` | Local HTTP round-trip against running server |
| `requirements.txt` | Added `pycryptodome` dependency |

---

## 2. Route Structure

```
GET  /api/wecom/kf/callback?msg_signature=&timestamp=&nonce=&echostr=
     → verify signature, decrypt echostr, return plaintext

POST /api/wecom/kf/callback?msg_signature=&timestamp=&nonce=
     → verify signature, decrypt XML body, log JSON, return "success" (200)
```

Mounted in `app_main.py` alongside inbox/add-car routes (always on, not lab-gated).

WeCom callback path is **outside** `/api/inbox/*` intake perimeter — no broker token required.

---

## 3. Environment Variables Required

| Variable | Required | Description |
|----------|----------|-------------|
| `WECOM_KF_TOKEN` | Yes | Callback Token from WeCom admin (客服账号 → API → 接收消息) |
| `WECOM_KF_ENCODING_AES_KEY` | Yes | 43-char EncodingAESKey |
| `WECOM_CORP_ID` | Yes | Enterprise Corp ID (`ww…`) — used as ReceiveId for decrypt |

**Fallback aliases:** `WECOM_TOKEN`, `WECOM_ENCODING_AES_KEY`, `WECOM_KF_CORP_ID`

If any required var is missing → `503 wecom_kf_callback_not_configured_v1`

---

## 4. Local Test Instructions

### Install dependency

```bash
pip install pycryptodome
```

### Unit tests (no server)

```bash
PYTHONPATH=. pytest tests/test_wecom_kf_callback.py -q
```

### Live server round-trip

```bash
export WECOM_KF_TOKEN="your_token"
export WECOM_KF_ENCODING_AES_KEY="your_43_char_key"
export WECOM_CORP_ID="wwyourcorpid"

bash scripts/run_demo_local.sh
# in another terminal:
PYTHONPATH=. python3 scripts/test_wecom_kf_callback_local.py --url http://localhost:8001
```

Expected: `GET 200 body='local_spike_echo'`, `POST 200 body='success'`, log line `wecom_kf_callback_event_v1`.

---

## 5. Cloud Run Deployment Checklist

- [ ] Add env vars to Cloud Run service (`WECOM_KF_TOKEN`, `WECOM_KF_ENCODING_AES_KEY`, `WECOM_CORP_ID`)
- [ ] Deploy backend revision with this spike (do **not** promote to production traffic until WeCom admin URL is configured)
- [ ] Confirm public HTTPS URL: `https://<cloud-run-host>/api/wecom/kf/callback`
- [ ] In WeCom Admin → 微信客服 → API → 接收消息 server URL, paste callback URL
- [ ] Token + EncodingAESKey must match env vars exactly
- [ ] Trigger URL verification (GET) — WeCom sends echostr; expect 200 plaintext response
- [ ] Send test customer message — expect POST 200 + structured log in Cloud Logging
- [ ] Verify **no** calls to P16 extract, OCR, case store, or sync_msg (grep logs)
- [ ] Rollback: remove WeCom callback URL or unset env vars; web intake unaffected

---

## 6. Sample Callback Payload

WeCom POST body (encrypted wrapper):

```xml
<xml>
   <ToUserName><![CDATA[ww12345678910]]></ToUserName>
   <AgentID><![CDATA[1000002]]></AgentID>
   <Encrypt><![CDATA[msg_encrypt]]></Encrypt>
</xml>
```

After decrypt (kf_msg_or_event):

```xml
<xml>
   <ToUserName><![CDATA[ww12345678910]]></ToUserName>
   <CreateTime>1348831860</CreateTime>
   <MsgType><![CDATA[event]]></MsgType>
   <Event><![CDATA[kf_msg_or_event]]></Event>
   <Token><![CDATA[ENCApHxnGDNAVNY4AaSJKj4Tb5mwsEMzxhFmHVGcra996NR]]></Token>
   <OpenKfId><![CDATA[wkxxxxxxx]]></OpenKfId>
</xml>
```

Query params on both GET and POST: `msg_signature`, `timestamp`, `nonce` (+ `echostr` on GET).

---

## 7. Sample Log Output

```
INFO wecom_kf_callback_event_v1 {"event_type": "wecom_kf_callback", "channel": "wecom_kf", "msg_type": "event", "event": "kf_msg_or_event", "to_user_name": "ww12345678910", "create_time": "1348831860", "token": "ENCApHxnGDNAVNY4AaSJKj4Tb5mwsEMzxhFmHVGcra996NR", "open_kf_id": "wkxxxxxxx", "msg_signature_prefix": "a1b2c3d4e5f6", "timestamp": "1476416373", "nonce": "47744683", "raw_fields": {"ToUserName": "ww12345678910", "CreateTime": "1348831860", "MsgType": "event", "Event": "kf_msg_or_event", "Token": "ENCApHxnGDNAVNY4AaSJKj4Tb5mwsEMzxhFmHVGcra996NR", "OpenKfId": "wkxxxxxxx"}}
```

---

## 8. Risks Encountered

| Risk | Notes |
|------|-------|
| Official SDK is Python 2 | Vendored Python 3 port of Tencent `WXBizMsgCrypt`; requires `pycryptodome` |
| ReceiveId mismatch | Decrypt fails (-40005) if `WECOM_CORP_ID` ≠ `ToUserName` in payload |
| No WeCom POC doc in repo | Implemented from ADR-004 + Tencent kf_msg_or_event docs |
| Callback URL must be public HTTPS | Local dev needs ngrok/Cloudflare tunnel for real WeCom verify |
| Spike mounted on main app | Isolated route module; no engine hooks; easy rollback via env unset |
| POST returns `success` only | Per WeCom callback contract; sync_msg intentionally not called (out of scope) |

---

## 9. GO / NO-GO

| Criterion | Status |
|-----------|--------|
| GET verify + decrypt echostr | **GO** (unit tested) |
| POST verify + decrypt + structured log + 200 | **GO** (unit tested) |
| No P16 engine / OCR / cases / sync_msg | **GO** (not wired) |
| Tencent official crypto vendored | **GO** |
| Real WeCom corp callback E2E | **PENDING** — requires broker corp credentials + public URL |

**Spike verdict: GO for code merge and Cloud Run staging test.**  
**Production WeCom wiring: NO-GO until real corp URL verification succeeds** (expected for a spike).

---

*Related: `docs/p16/adr/ADR_004_ENTERPRISE_WECOM_CHANNEL_INTEGRATION.md`*
