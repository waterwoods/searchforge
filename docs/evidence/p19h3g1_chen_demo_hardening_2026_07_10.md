# P19H-3g-1 — Chen Demo Hardening Evidence

**Date:** 2026-07-10  
**Branch:** `sprint/p16-trust-layer`  
**Operator:** Cursor agent (P19H-3g-1)  
**Scope:** Pre-demo reliability only — no product features, no schema changes

---

## 1. Goal

Close the last demo-mile risks before Chen pilot walkthrough:

1. Confirm Cloud Run `WECOM_SLICE_SEND_REPLY`
2. Verify live End Card send path (preview + send attempt)
3. Semi-automated Workbench `broker_done` verification
4. Fresh WeCom demo script (5 scenes) via deploy smoke
5. Seed/demo data decision
6. Logs scan
7. Final Demo Ready verdict

---

## 2. Cloud Run revision / GIT_SHA

| Item | Value |
|------|-------|
| Service | `fiqa-api` @ `us-west1` |
| Project | `optimal-disk-472305-e2` |
| Latest ready revision | `fiqa-api-00190-989` |
| Traffic | 100% → `fiqa-api-00190-989` |
| `GET /version` commit | `a425fa461` |
| Deploy update this session | **No** — revision already current |

```bash
curl -s https://fiqa-api-g7zatxrycq-uw.a.run.app/version
# {"commit":"a425fa461","source":"env","service":"Unified Intake API",...}
```

---

## 3. WECOM_SLICE_SEND_REPLY status

**Confirmed set on Cloud Run:**

```text
WECOM_SLICE_SEND_REPLY=1
```

Also present (unchanged): `WECOM_CORP_ID`, `WECOM_KF_TOKEN`, `WECOM_KF_ENCODING_AES_KEY`, `WECOM_AGENT_SECRET`, `WECOM_B0_ACTIVE_WORKSPACE=1`, `WECOM_INBOX_QUEUE=0`, `WECOM_REPLY_OUTBOX=0`.

**Action taken:** None — env already correct; no redeploy required.

**Note vs P19H-3g audit:** Audit recorded send env as missing; live describe now shows `=1`. Either env was updated after audit or audit snapshot was stale.

---

## 4. Health / readyz

| Endpoint | HTTP | Notes |
|----------|------|-------|
| `/health/live` | 200 | ok |
| `/readyz` | 200 | `intake_path_ready: true`, `intake_core_readiness: true` |
| Qdrant warmup | non-blocking ERROR | gRPC connection noise on `/readyz`; intake path still ready |

---

## 5. Live End Card send result

**Smoke:** `scripts/p19h3f2_deploy_broker_done_smoke.py` (suffix `3f2_smoke_002540`)

| Check | Result |
|-------|--------|
| `POST .../broker-done` | 200 |
| `claim_phase` | `broker_done` |
| End Card preview frame | PASS — `━━━━━━━━━━━━`, `【陈总已确认 ✅】`, `收集阶段已结束`, disclaimer |
| Second POST idempotent | 200, single `broker_done` timeline event |
| `end_card_sent` (synthetic case) | **false** |
| Cloud log | `claim_end_card_failed_v1` → `RuntimeError` |

**Interpretation:**

- Send gate is **open** (`WECOM_SLICE_SEND_REPLY=1`); code reaches WeCom `kf/send_msg`.
- Synthetic smoke cases use fake `external_userid` / `open_kfid` (`wktest001`, `wm_p19h3f2_*`); WeCom API rejects → expected `RuntimeError`.
- **Not** `WECOM_SLICE_SEND_REPLY not set` (that path is cleared).
- **Live customer send** requires real WeCom-created Claim with bound channel — validate once on demo device before promising End Card delivery to Chen.

Artifact: `docs/evidence/p19h3f2_smoke_run_3f2_smoke_002540.json`

---

## 6. Workbench broker_done click result

### API layer — PASS

From broker_done smoke + live API probe:

| Check | Result |
|-------|--------|
| Active Claim in default queue | 37 rows (API `GET /api/inbox/cases?limit=50`) |
| Sample `case_8c13d28e0a38` display | `Claim · 记录中 · Broker Review pending` |
| `claim_case_brief` | Present — `key_facts`, `highlights` (4), `missing_info` (2), `next_best_question` |
| `POST .../broker-done` | 200; case leaves active semantics; idempotent |
| Raw inbound broker_done | 400 `broker_done_blocked_raw_inbound` (correct) |

### UI bundle — PASS

`https://ui-smoky-beta.vercel.app/assets/index-BwABC0DH.js` contains:

- `markClaimBrokerDone` / `POST /api/inbox/cases/${id}/broker-done`
- Button copy: `陈总已确认 / 结束收集`

### Browser semi-automation — PARTIAL (HUMAN-PENDING)

URL: https://ui-smoky-beta.vercel.app/workbench/unified-intake

| Step | Result |
|------|--------|
| Page loads | PASS |
| Refresh list | PASS — queue populated (~50 rows) |
| Drawer opens on row click | PASS |
| Claim Brief / highlights in drawer | Partial — drawer shows case detail; legacy list labels on some rows |
| Broker Done button visible + click | **Not completed** — opened row (`case_b09…`) did not surface `陈总已确认 / 结束收集` button (legacy/generic row presentation) |

**Operator action before demo:** On a **fresh WeCom Claim** row (`Claim · 记录中`), open drawer → confirm Brief + Highlights + Missing info → click **陈总已确认 / 结束收集** once on real device.

Visibility smoke (API): `scripts/p19h3f1c_deploy_visibility_smoke.py` → **OVERALL PASS**

---

## 7. Fresh WeCom demo run result (5-scene script)

**Smoke:** `scripts/p19h3f4_deploy_unified_status_card_smoke.py` (suffix `3f4_smoke_002651`) — maps to Chen demo script Scenes 1–5 at API/WeCom ingest layer.

| Scene | Smoke key | Result |
|-------|-----------|--------|
| 1 — Start (`我要理赔`) | A_start_frame | PASS — framed Start Card, injury, disclaimer |
| 2 — Story + Status (`进度`) | B_status_card | PASS — `【当前状态】`, no duplicate Claim |
| 2b — No active status | C_no_active_status | PASS |
| 3 — Photo (regression) | regression | PASS — photo → holding lane, hidden from default queue |
| 4 — Collision resolver | E_collision_frame | PASS — framed resolver, choice 2 → new Claim + Start Card |
| 5 — Broker Done / End Card | F_end_card | PASS — 200, framed End Card preview, idempotent POST |

**OVERALL PASS**

Pytest: `test_p19h3f2_true_end_card_on_broker_done.py` + `test_p19h3f4_unified_status_card.py` → 30 passed

Artifact: `docs/evidence/p19h3f4_smoke_run_3f4_smoke_002651.json`

**Not run in this session:** Full live WeChat client walkthrough on a human phone — use clean test contact per demo script.

---

## 8. Seed / demo data decision

| Decision | **Use fresh WeCom customer for demo** |
|----------|----------------------------------------|
| Old `chen_kui_p18` seed | **Ignored** — stale names/labels on Workbench list would confuse |
| `seed_chen_kui_demo.py --target qa` | **Skipped** — script is safe to re-run but not required; fresh WeCom path preferred |
| Risk | Queue shows many smoke/test Claims from deploy smokes; demo should start from **customer WeCom**, not Workbench list |

---

## 9. Logs result

Window: ~3h around hardening run (2026-07-10 UTC).

| Signal | Finding |
|--------|---------|
| Claim-route 500s | **None** in `/api/inbox` + claim filters |
| `claim_end_card_failed_v1` | 2 events — smoke synthetic cases (expected) |
| Status / collision / lane-switch errors | None |
| Duplicate case creation | None observed |
| Qdrant gRPC warmup | ERROR traces on `/readyz` probe — known non-blocking for intake |

---

## 10. Remaining risks

1. **Live End Card on real WeCom customer** — env enabled; synthetic send fails at WeCom API. One human confirmation on demo contact still needed.
2. **Workbench Broker Done click** — API + JS verified; one manual drawer click on fresh Claim before customer session.
3. **Queue noise** — many test/smoke Claims in QA DB; demo must start from WeCom, not stale Workbench rows.
4. **Customer name** — still `微信客户`; not a blocker.
5. **UI list labels** — some rows show legacy copy vs `Claim · 记录中`; API `display_status` is correct.

---

## 11. Final verdict

| | |
|---|---|
| **Workflow + cards + state machine** | **DEMO GO** |
| **WECOM_SLICE_SEND_REPLY on Cloud Run** | **Confirmed** (improved vs P19H-3g audit) |
| **Live End Card to real customer** | **HUMAN-PENDING** (one real-channel send) |
| **Workbench broker_done click** | **HUMAN-PENDING** (one click on fresh Claim) |
| **Overall** | **CONDITIONAL DEMO GO** |

Proceed with Chen demo when operator:

1. Runs demo from **clean WeCom test contact** (Scenes 1–5).
2. Confirms **End Card received** on that contact after Broker Done.
3. Performs **one Workbench Broker Done click** on the demo Claim before the session.

---

## Related

- Audit: `docs/pilot/p19h3g_pilot_readiness_audit_chen_2026_07_10.md`
- Demo script: `docs/pilot/p19h3g_chen_demo_script_2026_07_10.md`
- Launch checklist: `docs/pilot/p19h3g_pilot_launch_checklist_2026_07_10.md`
- Prior deploy smoke: `docs/evidence/p19h3f4_deploy_unified_status_card_text_frame_smoke_2026_07_10.md`
