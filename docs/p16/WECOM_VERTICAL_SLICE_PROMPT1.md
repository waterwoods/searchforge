# P16 WeCom Vertical Slice — Prompt 1

**Date:** 2026-06-27  
**Scope:** Smallest end-to-end communication pipeline only. No Case IQ engine, no Broker Inbox.  
**Authority:** ADR-003 (safe language) · ADR-004 Phase 0

---

## Pipeline

```
Personal WeChat (customer)
        ↓
Enterprise WeCom (微信客服)
        ↓
POST /api/wecom/kf/callback
        ↓
kf/sync_msg (pull message body)
        ↓
normalize → message.received
        ↓
rule-based intent (add_vehicle | claim | policy_review | unclear)
        ↓
bilingual safe reply (ADR-003)
        ↓
optional kf/send_msg (WECOM_SLICE_SEND_REPLY=1)
```

**Explicitly out of scope:** case creation, Broker Inbox, OCR, Trusted Packet, Bubble Map, Knowledge Graph, carrier API, readiness changes.

---

## Files

| File | Role |
|------|------|
| `services/fiqa_api/routes/wecom_kf_callback.py` | Callback verify + decrypt + invoke slice |
| `services/fiqa_api/wecom/slice.py` | Orchestrator |
| `services/fiqa_api/wecom/sync_msg.py` | `kf/sync_msg` pull |
| `services/fiqa_api/wecom/normalize.py` | Channel event normalization |
| `services/fiqa_api/wecom/intent.py` | Rules-first intent (no LLM) |
| `services/fiqa_api/wecom/reply.py` | ADR-003 bilingual replies + guided menu |
| `services/fiqa_api/wecom/send_msg.py` | Outbound text / native `msgmenu` (env-gated) |
| `services/fiqa_api/wecom/config.py` | Env credentials |
| `services/fiqa_api/wecom/event_parser.py` | Decrypted XML → structured log |
| `tests/test_wecom_*.py` | Unit tests |
| `scripts/test_wecom_kf_callback_local.py` | Local HTTP round-trip |

---

## Environment Variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `WECOM_KF_TOKEN` | Yes (callback) | URL verification token |
| `WECOM_KF_ENCODING_AES_KEY` | Yes (callback) | 43-char AES key |
| `WECOM_CORP_ID` | Yes (callback) | Corp ID for decrypt |
| `WECOM_KF_SECRET` | Yes (slice) | 微信客服 Secret → sync_msg + send_msg |
| `WECOM_SLICE_SEND_REPLY` | No | `1`/`true`/`yes` sends reply; default log-only |

Aliases: `WECOM_TOKEN`, `WECOM_ENCODING_AES_KEY`, `WECOM_CORP_SECRET`, `WECOM_SECRET`.

---

## Test Instructions (local, no WeCom corp)

### Unit tests

```bash
cd /home/andy/searchforge
PYTHONPATH=. pytest tests/test_wecom_intent.py tests/test_wecom_reply.py tests/test_wecom_slice.py tests/test_wecom_kf_callback.py -q
```

### Callback round-trip (server required)

```bash
export WECOM_KF_TOKEN="your_token"
export WECOM_KF_ENCODING_AES_KEY="your_43_char_key"
export WECOM_CORP_ID="wwyourcorpid"
export WECOM_KF_SECRET="your_kf_secret"   # optional for slice; required for sync_msg

bash scripts/run_demo_local.sh
# second terminal:
PYTHONPATH=. python3 scripts/test_wecom_kf_callback_local.py --url http://localhost:8001
```

Expected server log stages (grep `wecom_slice_` or `wecom_kf_`):

| Stage | Log prefix |
|-------|------------|
| Callback received | `wecom_kf_callback_event_v1` |
| sync_msg ok | `wecom_slice_sync_msg_ok_v1` |
| Normalized event | `wecom_slice_normalized_event_v1` |
| Detected intent | `wecom_slice_intent_v1` |
| Reply generated | `wecom_slice_reply_generated_v1` |
| Reply sent or log-only | `wecom_slice_reply_sent_v1` or `wecom_slice_reply_logged_only_v1` |

Without `WECOM_KF_SECRET`: callback works; slice logs `wecom_slice_skipped_v1`.

---

## Real WeCom Test Procedure

### Prerequisites

1. Enterprise WeCom admin access (微信客服 → API)
2. Public HTTPS callback URL (Cloud Run staging or ngrok tunnel to `:8001`)
3. Env vars set on the running service
4. 微信客服 account linked so Personal WeChat customers can message

### Steps

1. **Deploy / tunnel** with callback env vars + `WECOM_KF_SECRET`.
2. **Register callback URL** in WeCom Admin → 微信客服 → API → 接收消息:
   `https://<host>/api/wecom/kf/callback`
3. **URL verification** — WeCom sends GET; expect 200 plaintext echostr.
4. **Send test message** from Personal WeChat to the 微信客服 entry:
   - Clear intent: `I was in an accident` → expect `detected_intent: claim`
   - Unclear: `hi` → expect guided menu (`guided_menu_required: true`)
5. **Check logs** for all six stages above.
6. **Optional outbound** — set `WECOM_SLICE_SEND_REPLY=1`, redeploy, send `hi` again:
   - Customer receives native WeCom clickable menu (not numbered 1/2/3/4)
   - Tap **Add Vehicle / 加车** → next message routes as `add_vehicle`

### Intent smoke matrix

| Customer text | Expected `detected_intent` |
|---------------|---------------------------|
| `我买了一辆新车，想加到保险上` | `add_vehicle` |
| `I was in an accident` | `claim` |
| `Can you review my policy?` | `policy_review` |
| `hello` | `unclear` (+ guided menu) |
| `I had an accident and bought a new car` | `unclear` (multi-intent) |

---

## Remaining Blockers

| Blocker | Impact | Owner |
|---------|--------|-------|
| Real corp E2E not run in CI | Prompt 1 GO depends on staging test | Andy + broker corp |
| Public HTTPS URL for local dev | Requires ngrok/Cloudflare tunnel | Ops |
| No sync_msg cursor persistence | Duplicate pull on rapid callbacks (acceptable for slice) | Prompt 2 |
| Menu click `claim` vs `claim_intake` internal mapping | Handled in `intent.py` | — |
| `WECOM_SLICE_SEND_REPLY` not in deploy script | Manual env on Cloud Run | Ops |

---

## GO / NO-GO for Prompt 2

| Criterion | Status |
|-----------|--------|
| Callback verify + decrypt | **GO** (unit tested) |
| sync_msg → normalize → intent → reply pipeline | **GO** (unit tested) |
| Rules-first intent (no LLM routing) | **GO** |
| ADR-003 safe bilingual replies | **GO** |
| Guided menu without 1/2/3/4 prompt | **GO** |
| Native WeCom `msgmenu` when send enabled | **GO** (code ready) |
| Log-only default (`WECOM_SLICE_SEND_REPLY` unset) | **GO** |
| No case / inbox / OCR / packet wiring | **GO** |
| Real Personal WeChat → WeCom E2E | **PENDING** |

**Prompt 1 code verdict: GO** — merge and run staging E2E with broker corp credentials.  
**Prompt 2 entry: NO-GO until one real customer message completes all six log stages on staging.**

---

*Related: `docs/p16/WECOM_CALLBACK_SPIKE.md` · `docs/p16/adr/ADR_004_ENTERPRISE_WECOM_CHANNEL_INTEGRATION.md`*
