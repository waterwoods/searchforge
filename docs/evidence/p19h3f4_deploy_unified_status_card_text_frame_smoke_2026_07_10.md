# P19H-3f-4 Deploy Smoke — Unified Status Card + Text Frame

**Date:** 2026-07-10  
**Branch:** `sprint/p16-trust-layer`  
**Type:** Deploy + QA smoke evidence (no schema, no frontend deploy)

---

## 1. Goal

Deploy unified WeCom text-frame cards (Start / Status / Confirm / Collision / End) and verify on Cloud Run + QA Cloud SQL that status requests, lane switch, collision resolver, and broker_done End Card behave correctly without breaking Start Card policy.

---

## 2. Deployed revision

| Deploy | GIT_SHA | Cloud Run revision | Notes |
|--------|---------|-------------------|-------|
| 1 | `e1aed6068` | `fiqa-api-00189-bmg` | Status Card + text frame feature |
| 2 | `a425fa461` | `fiqa-api-00190-989` | **Production** — PG extra persistence for `claim_collision_pending` / `lane_switch_pending` / `claim_end_card_state` / `claim_flow_state` |

Service URL: `https://fiqa-api-g7zatxrycq-uw.a.run.app`

---

## 3. Health / readyz

| Endpoint | Result |
|----------|--------|
| `/version` | `{"commit":"a425fa461",...}` |
| `/health/live` | 200 |
| `/readyz` | 200 |

---

## 4. QA gate

```bash
bash scripts/check_chen_kui_demo_environment.sh --cloud-api
```

| Check | Result |
|-------|--------|
| readyz | PASS |
| Cloud SQL alignment | PASS (total_count aligned) |
| Demo seed names on API page | FAIL (known — re-seed `chen_kui_p18`) |
| Per-demo field completeness | FAIL (known non-core seed drift) |

**Verdict:** Core API / Cloud SQL / Workbench list **healthy**. Seed gaps are **known non-core** — not blocking this card deploy.

---

## 5. Start Card frame (Smoke A)

Customer: `我要理赔`

| Assertion | Result |
|-----------|--------|
| Claim created | PASS |
| `━━━━━━━━━━━━` frame | PASS |
| `【事故记录已开始 ✅】` | PASS |
| 陈总办公室 / 有没有受伤 / 不代表已经向保险公司正式报案 | PASS |
| Injury quick-reply menu | PASS |
| Forbidden language | none |

---

## 6. Status Card (Smoke B)

Active Claim → `进度` / `状态` / `理赔进度`

| Assertion | Result |
|-----------|--------|
| `【当前状态】` + frame | PASS |
| 已收到 / 还缺 / 下一步 / 提醒 | PASS |
| No new Claim / no second Start Card | PASS |
| Forbidden language | none |

---

## 7. No-active-Claim status (Smoke C)

`理赔进度` with no open Claim

| Assertion | Result |
|-----------|--------|
| No Claim created | PASS |
| Suggests `我要理赔` | PASS |
| No Start Card | PASS |

---

## 8. Confirm Card frame (Smoke D)

Active Add Car → `我要理赔` → `开始事故记录`

| Assertion | Result |
|-----------|--------|
| Confirm Card framed `【请确认】` | PASS |
| 暂停当前加车资料收集 / 开始事故记录 / 继续加车 | PASS |
| No immediate Claim on first message | PASS |
| Framed Start Card after confirm | PASS |

---

## 9. Collision Resolver frame (Smoke E)

Open Claim + new accident narrative → `开始新的事故记录`

| Assertion | Result |
|-----------|--------|
| Resolver framed `【请选择事故记录】` | PASS |
| 继续上一个事故 / 开始新的事故记录 / 联系陈总 | PASS |
| No silent append / no silent new Claim | PASS |
| Choice 2 → new Claim + framed Start Card | PASS |

**Deploy blocker fixed:** collision pending state now round-trips via `service_records.extra` (commit `a425fa4`).

---

## 10. End Card frame (Smoke F)

`POST /api/inbox/cases/{id}/broker-done`

| Assertion | Result |
|-----------|--------|
| broker_done HTTP 200 | PASS |
| Preview contains frame + `【陈总已确认 ✅】` | PASS |
| 收集阶段已结束 + disclaimer | PASS |
| Second broker_done idempotent (200) | PASS |

**Note:** Cloud log shows `claim_end_card_failed_v1` (RuntimeError — `WECOM_SLICE_SEND_REPLY` not set on Cloud Run). Customer send skipped; **preview copy verified**. Same pattern as P19H-3f-2 smoke.

---

## 11. Regression checks

| Check | Result |
|-------|--------|
| Random photo → `wecom_media_intake`, hidden from default queue | PASS |
| Random narrative → no Claim | PASS |
| broker_done rejects raw inbound (400) | PASS |
| pytest `test_p19h3f4_unified_status_card.py` | PASS |
| pytest `-k claim` | PASS |
| pytest `-k h5` | PASS |

Smoke artifact: `docs/evidence/p19h3f4_smoke_run_3f4_smoke_210725.json`

---

## 12. Logs

Scanned Cloud Run logs post-smoke. No 500s on claim routes. Observed:

- `claim_end_card_failed_v1` — send disabled (expected without WeCom send env)
- No status-card formatting errors
- No collision / lane-switch 500s after PG extra fix

Qdrant/Redis warmup noise: not observed in sample.

---

## 13. Constraints

- No schema / DB table migration
- No WeCom template card
- No OCR / ASR
- No fault / coverage / carrier filing changes
- Start Card policy / Collision logic / broker_done triggers unchanged

---

## 14. Known limitations

- End Card **preview** verified; live WeCom send requires `WECOM_SLICE_SEND_REPLY` + channel binding on Cloud Run
- QA demo seed names incomplete on API page (pre-existing)
- Enterprise WeCom template card still deferred

---

## 15. Next recommended prompt

**Pilot Demo Script / Chen readiness** — operator walkthrough with unified card language on real WeChat + Workbench.
