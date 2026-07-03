# Track A — Acceptance Report

**Status:** ✅ **TRACK A PRODUCTION READY — ACCEPTED**
**Date accepted:** 2026-07-03
**Scope:** Enterprise WeCom 微信客服 (Channel Adapter #1) — networking, authorization, and message-pull path only. No application/business logic in scope.

---

## 1. Architecture

### Channel context

Track A implements the transport layer for **Enterprise WeCom Channel Adapter #1** (`docs/p16/adr/ADR_004_ENTERPRISE_WECOM_CHANNEL_INTEGRATION.md`). Insurance Case IQ is channel-agnostic; WeCom is the first official customer-facing channel after Web Intake.

### Final production topology

```
Personal WeChat (customer)
        │
        ▼
Enterprise WeCom 微信客服 (KF)
        │  (webhook callback + sync_msg pull)
        ▼
Cloud Run — fiqa-api (us-west1)
        │  Direct VPC Egress (--vpc-egress=all-traffic)
        ▼
VPC "default" — subnet "default" (us-west1, 10.138.0.0/20)
        │
        ▼
Cloud Router "fiqa-wecom-nat-router"
        │
        ▼
Cloud NAT "fiqa-wecom-nat-gateway"
        │  (manual NAT IP allocation)
        ▼
Static external IP — 8.235.43.132 (reserved, Premium tier)
        │
        ▼
Enterprise WeCom 企业可信IP (Trusted IP allowlist)
        │
        ▼
WeCom Open API (qyapi.weixin.qq.com)
  → gettoken → kf/account/list → kf/sync_msg
```

This replaces the temporary VM (`wecom-egress-test`, `us-west1-a`) that was used to prove the message-pull path while production networking was being built. The VM has been deleted (see §5).

### Resources created (all new; VPC/subnet reused)

| Resource | Name | Type |
|---|---|---|
| Static external IP | `fiqa-wecom-static-ip` | Regional, Premium tier, `us-west1` |
| Cloud Router | `fiqa-wecom-nat-router` | `us-west1`, attached to existing `default` VPC |
| Cloud NAT gateway | `fiqa-wecom-nat-gateway` | Manual IP allocation, scoped to `default` subnet only |
| Cloud Run egress | `fiqa-api` revision `fiqa-api-00112-q2n` | Direct VPC Egress, `--network=default --subnet=default --vpc-egress=all-traffic` |

### Resources reused (no new VPC/subnet/connector)

- VPC network: `default` (already existed)
- Subnet: `default` in `us-west1` (`10.138.0.0/20`, already existed)
- No Serverless VPC Connector was created — Direct VPC Egress was used instead (lower cost, no connector instances to run)

---

## 2. Authorization Timeline

| Step | Result | Notes |
|---|---|---|
| Callback URL + Token + EncodingAESKey configured | ✅ PASS | Signature verification + decrypt confirmed |
| `gettoken` (WECOM_AGENT_SECRET) | ✅ PASS | `errcode: 0` — secret/CorpID pair valid |
| CaseIQ AI Adapter added to 可调用接口的应用 | ✅ Confirmed | Required to avoid `48002` |
| 客服账号 bound under 通过API管理微信客服账号 | ✅ Confirmed | Required to avoid `48007` |
| `kf/account/list` | ✅ PASS | `manage_privilege: true`, account `CaseaIQ AI客服` (`open_kfid: wktLevSgAAM9st2kyoeHS4KQtisH0bww`) |
| `sync_msg` from trusted VM (temporary) | ✅ PASS | Proved app-level permission was correct; blocked only by IP trust when run from Cloud Run |
| Static IP reserved | ✅ `8.235.43.132` | 2026-07-03 |
| Static IP added to 企业可信IP (WeCom admin console) | ✅ Confirmed by operator | 2026-07-03, manual admin step (cannot be automated) |
| Cloud NAT + Direct VPC Egress attached to `fiqa-api` | ✅ Deployed | 2026-07-03 |
| `sync_msg` from Cloud Run production egress | ✅ PASS — `errcode: 0` | 2026-07-03, see §4 |

---

## 3. Root Causes Solved

| Symptom | Root cause | Fix |
|---|---|---|
| `errcode=60020` (`not allow to access from your ip`) on `sync_msg` from Cloud Run | Cloud Run's default egress uses **dynamic, unpredictable Google IPs** — no way to whitelist a moving target in WeCom's 企业可信IP | Direct VPC Egress + Cloud NAT + one **reserved static IP**, whitelisted once in WeCom admin |
| `gettoken` PASS did not guarantee `sync_msg` PASS | `gettoken` only proves the secret/CorpID pair is valid for *some* app scope — it does not prove KF API permission, KF-account binding, or IP trust (three independent gates) | Verified all three gates explicitly: app callable list, KF account binding, and now IP trust |
| Temporary VM required as a workaround | VM had a stable IP that could be whitelisted, but is not a production-grade architecture (single point of failure, manual ops, no autoscaling) | Retired in favor of Cloud Run's own production-grade static egress path |

---

## 4. Final Validation Results

Validation was run **from inside Cloud Run's actual network path** (a short-lived Cloud Run Job configured with the identical `--network=default --subnet=default --vpc-egress=all-traffic` settings as `fiqa-api`, used only to prove egress and deleted immediately after — no application code was created, modified, or deployed for this test).

| Check | Result |
|---|---|
| Observed egress IP | `8.235.43.132` ✅ (exact match to reserved static IP) |
| `cgi-bin/gettoken` | `errcode: 0, errmsg: "ok"` ✅ |
| `cgi-bin/kf/account/list` | `errcode: 0`, `manage_privilege: true` ✅ |
| `cgi-bin/kf/sync_msg` | `errcode: 0, errmsg: "ok"`, 3 real messages returned (`msg_list` non-empty) ✅ |

`errcode=60020` is fully resolved on the production Cloud Run path. The temporary VM is no longer required for any part of this flow.

---

## 5. Cleanup

- Temporary VM `wecom-egress-test` (zone `us-west1-a`) — **deleted 2026-07-03**, removal verified via `gcloud compute instances list` (empty result).
- Temporary Cloud Run Job used for egress validation — **deleted immediately after use** (never a permanent resource).
- Remaining GCP compute/network footprint for Track A: `fiqa-wecom-static-ip`, `fiqa-wecom-nat-router`, `fiqa-wecom-nat-gateway`, and the Direct VPC Egress annotation on `fiqa-api`. No VMs remain.

---

## 6. Lessons Learned

1. **`gettoken` PASS is necessary but not sufficient.** Always verify KF-specific permission (`可调用接口的应用`), KF-account binding (`通过API管理微信客服账号`), and IP trust independently — they fail with distinct, easily-confused error codes (`48002`, `48007`, `60020`).
2. **Cloud Run's default egress IP is not suitable for any API that requires IP allowlisting.** This should be identified as an architecture requirement *before* integration work begins on any external channel with IP-based trust models, not discovered via a production error code.
3. **Direct VPC Egress is strictly better than a Serverless VPC Connector for this use case.** No connector instances to provision or pay for continuously; egress attaches directly to the existing subnet.
4. **A temporary VM is a legitimate bridge, not an endpoint.** It correctly de-risked the integration (proving app-level WeCom permissions were correct independent of the networking problem) but should be tracked as technical debt and retired as soon as the production path is validated — done here.
5. **Validating NAT egress without touching application code is possible** via a short-lived, throwaway Cloud Run Job sharing the same network configuration as the real service — useful pattern for future infra-only verification without risking application deploys.

---

## 7. Rollback Procedure

**Revert Cloud Run to previous (public/dynamic) egress** — service continues running, only the trusted-IP path is lost:

```bash
gcloud run services update fiqa-api --region=us-west1 --clear-network --clear-vpc-egress
```

**Full teardown of the production networking (only if abandoning this architecture entirely):**

```bash
gcloud compute routers nats delete fiqa-wecom-nat-gateway --router=fiqa-wecom-nat-router --region=us-west1 --quiet
gcloud compute routers delete fiqa-wecom-nat-router --region=us-west1 --quiet
gcloud compute addresses delete fiqa-wecom-static-ip --region=us-west1 --quiet
```

Note: if the static IP is deleted, it must be removed from WeCom's 企业可信IP list as well, and `sync_msg` will fail with `60020` again for any future Cloud Run egress until a new IP is reserved and re-whitelisted.

---

## 8. Cost

Estimated incremental monthly cost of the production networking (Cloud NAT + static IP; Direct VPC Egress itself is free):

- NAT gateway: ~$2.04/mo (based on `fiqa-api` `maxScale=2`)
- Static IP (in-use rate): ~$3.65/mo
- Data processed: <$0.10/mo at current message volume
- **Total ≈ $6–8/month**

---

*Related: `docs/p16/adr/ADR_004_ENTERPRISE_WECOM_CHANNEL_INTEGRATION.md` · `docs/p16/WECOM_ADMIN_DIAGNOSTIC.md` · `scripts/validate_wecom_gettoken.py` · `scripts/validate_wecom_sync_msg.py` · `scripts/track_a_e2e_acceptance.py`*
