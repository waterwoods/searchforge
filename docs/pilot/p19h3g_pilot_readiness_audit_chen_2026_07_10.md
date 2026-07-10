# P19H-3g — Chen Pilot Readiness Audit

**Date:** 2026-07-10  
**Branch:** `sprint/p16-trust-layer`  
**Production commit:** `a425fa461` · Cloud Run `fiqa-api-00190-989`  
**Workbench URL:** https://ui-smoky-beta.vercel.app/workbench/unified-intake  
**Auditor scope:** Read-only code + evidence + live API + pytest (no feature work)

---

## Executive verdict

| Verdict | **CONDITIONAL GO** |
|---------|---------------------|
| Meaning | Ready for Chen pilot demo **if** operator accepts known env gaps below. Core workflow (Start → Record → Status → Collision → Broker Done → End Card) is shipped and test-green. |

**Do not HOLD** for workflow logic. **Do HOLD live WeCom End Card send** until `WECOM_SLICE_SEND_REPLY` is confirmed on Cloud Run for the demo customer channel — preview copy is verified; live send currently logs `claim_end_card_failed_v1`.

---

## Product positioning (confirmed)

This is a **WeChat-native Broker Intake Copilot** — record collection and broker handoff memory. It is **not** a claim system, CRM, carrier filing system, or liability/coverage engine.

Customer-facing cards consistently say: *这不代表已经向保险公司正式报案* / *不代表结案或赔付*.

---

## A. Customer WeCom UX

Evidence: `docs/evidence/p19h3f4_*`, `services/fiqa_api/wecom/reply.py`, deploy smoke A–F.

| Dimension | Score | Notes |
|-----------|-------|-------|
| Start Card clear | **5/5** | Framed `【事故记录已开始 ✅】`; injury question; 陈总办公室 intro; disclaimer |
| Status Card clear | **5/5** | Framed `【当前状态】`; 状态 / 已收到 / 还缺 / 下一步 / 提醒 |
| Confirm Card clear | **5/5** | Framed `【请确认】`; Add Car → Claim lane switch; 开始事故记录 / 继续加车 |
| Collision Resolver clear | **5/5** | Framed `【请选择事故记录】`; 3 explicit choices + buttons |
| End Card clear | **5/5** | Framed `【陈总已确认 ✅】`; 收集阶段已结束; no carrier-filing language |
| Customer understands record-only (not filing) | **5/5** | Disclaimer on Start, Status, Confirm, Collision, End, C1 cards |
| No confusing English/technical wording | **4/5** | Main cards Chinese; minor English in C1 tail (`claim 已正式提交`) and legacy `_INTENT_REPLIES` paths not used in formal Claim flow |
| Message length acceptable | **4/5** | Status Card can be long on small screens when many fields populated; still scannable via sections |
| User knows next step | **5/5** | Every framed card has 下一步 or injury/menu buttons |

**Section average: 4.7 / 5**

---

## B. Broker Workbench UX

Evidence: `claim_workbench_display.py`, P19H-3f-1c visibility smoke, P19H-3f-2 broker_done smoke.

| Dimension | Score | Notes |
|-----------|-------|-------|
| Default queue = formal work only | **5/5** | `filter_broker_workbench_cases` excludes `wecom_media_intake` |
| Raw inbound hidden | **5/5** | Default API + UI filter; debug via `include_raw_inbound=true` only |
| Claim row label clear | **5/5** | `Claim · 记录中` / `Broker Review` / `已确认 / 已交接` |
| Claim Case Brief useful | **4/5** | Deterministic brief: key_facts, evidence, confidence; no LLM |
| Highlights useful | **4/5** | Up to 5 broker-safe highlights (injury, missing, evidence) |
| Missing info visible | **5/5** | `missing_info` + Status Card 还缺 mirror same logic |
| Broker next step visible | **4/5** | `next_best_question` in brief; drawer shows display status |
| Broker Done action clear | **5/5** | Button + copy `陈总已确认 / 结束收集`; idempotent |
| Understand case in ~10 seconds | **4/5** | Strong when story + photos present; weaker when customer name is `微信客户` |

**Section average: 4.6 / 5**

---

## C. State machine safety

Evidence: `docs/p19h_state_machine_temporal_audit_2026_07_10.md`, pytest batteries, deploy smokes.

| Dimension | Score | Notes |
|-----------|-------|-------|
| Random text/photo does not create Claim | **5/5** | → `wecom_media_intake` or holding ack |
| Explicit `我要理赔` starts Claim | **5/5** | Start Card ceremony + formal case |
| Add Car → Claim needs Confirm Card | **5/5** | `lane_switch_pending`; no claim until confirm |
| Existing Claim + new accident → Collision Resolver | **5/5** | No silent append/create; PG extra persistence fixed (`a425fa4`) |
| Broker Done is manual only | **5/5** | Workbench `POST broker-done` only |
| End Card only after broker_done | **5/5** | `mark_claim_broker_done` → End Card |
| Status request does not create Claim | **5/5** | `is_claim_status_request` routes to Status Card or no-active guidance |
| Duplicate callbacks/messages no duplicate cases | **5/5** | msg_id dedup + idempotent Start/broker_done |

**Section average: 5.0 / 5**  
**Residual (non-blocking):** Claim → Add Car inverse lane switch untested (row 10); post-`broker_done` inbound photo policy undocumented (row 23).

---

## D. Pilot ops readiness

Evidence: live curl 2026-07-10, deploy smokes, QA gate.

| Dimension | Score | Notes |
|-----------|-------|-------|
| Deploy revision known | **5/5** | `a425fa461` / `fiqa-api-00190-989` |
| health/readyz pass | **5/5** | `/health/live` 200; `/readyz` 200, `intake_path_ready: true` |
| QA gate acceptable | **4/5** | Core API + Cloud SQL PASS; demo seed names/tags FAIL (known, non-core) |
| Cloud SQL persistence OK | **5/5** | Collision/lane-switch/end-card state round-trips via `service_records.extra` |
| Logs clean enough | **4/5** | No claim-route 500s in smokes; expected `claim_end_card_failed_v1` when send disabled |
| WECOM_SLICE_SEND_REPLY status known | **3/5** | **Not set on Cloud Run** — live WeCom send skipped; preview verified |
| Demo seed data clean enough | **3/5** | Stale `chen_kui_p18` names on API page; fine for **fresh WeCom customer** demo |
| Rollback plan exists | **4/5** | Prior revision `fiqa-api-00189-bmg` (`e1aed6068`); see checklist |

**Section average: 4.1 / 5**

---

## E. Product value (Chen pilot lens)

| Dimension | Score | Notes |
|-----------|-------|-------|
| Saves Chen time | **4/5** | Brief + highlights vs scrolling WeChat |
| Reduces repeated customer questions | **4/5** | Status Card answers 进度/还缺/下一步 |
| Reduces lost WeChat materials | **4/5** | Photos bound to active Claim timeline |
| Better follow-up memory | **4/5** | Timeline + brief persist in Cloud SQL |
| Professional enough for customers | **4/5** | Unified text-frame cards; not template-card polish |

**Section average: 4.0 / 5**

---

## Verification run (this audit)

```text
GET /version     → commit a425fa461
GET /health/live → 200 ok
GET /readyz      → 200 intake_path_ready true

pytest test_p19h3f4_unified_status_card.py     → 14 passed
pytest test_p19h3f3_claim_collision_resolver.py → 14 passed
pytest test_p19h3f2_true_end_card_on_broker_done.py → 16 passed
pytest -k claim                                 → all passed
pytest -k h5                                    → all passed
```

---

## Top 5 blockers

1. **`WECOM_SLICE_SEND_REPLY` not enabled on Cloud Run** — End Card (and any reply path gated on send env) will not reach customer WeChat; preview only. Confirm env + customer channel binding before promising live End Card to Chen.
2. **Human-pending Workbench drawer click** — API + JS bundle verified; operator should click `broker_done` once on real device before customer-facing demo.
3. **Demo seed stale on QA list page** — Old `chen_kui_p18` rows may confuse if demo starts from Workbench queue instead of fresh WeCom message. Prefer **live WeCom customer path** for demo.
4. **Customer name shows `微信客户`** — Status Card and Brief work without name extraction; Chen may need WeChat nickname manually for multi-customer days.
5. **Inverse lane switch untested** — Active Claim + `我要加车` not in test matrix; low frequency but could surprise mid-demo if triggered.

---

## Top 5 nice-to-have (post-pilot or parallel)

1. QA seed refresh: `PYTHONPATH=. python3 scripts/seed_chen_kui_demo.py --target qa`
2. Customer display name from WeCom profile / first self-intro
3. Browser automation for drawer `broker_done` click in deploy smoke
4. Explicit test for idle `看看这个` ambiguous text (row 2)
5. Enterprise WeCom template card (deferred by design)

---

## What NOT to build before pilot

- Schema / new DB tables
- OCR / ASR / damage AI
- Fault / liability / coverage / carrier filing
- LLM-generated brief
- WeCom template card
- Frontend redesign / new broker dashboard
- Multi-industry / complex permissions
- Identity merge system
- Auto-close or auto broker_done

---

## Pre-demo decision matrix

| Question | Answer |
|----------|--------|
| Frontend changes needed before Chen demo? | **No** — Workbench broker_done + Claim brief already on `ui-smoky-beta` |
| Customer name extraction needed? | **No** (nice-to-have; defaults to 微信客户) |
| Performance work needed? | **No** — pilot volume is low; no scale blocker observed |
| WeCom template card needed? | **No** — text-frame cards sufficient for pilot |
| Seed cleanup needed? | **Recommended, not blocking** — use fresh WeCom customer for scripted demo; clean QA queue if showing Workbench list first |

---

## GO / CONDITIONAL GO / HOLD

| | |
|---|---|
| **Workflow + tests + cards** | **GO** |
| **Live WeCom End Card send on Cloud Run** | **HOLD until send env confirmed** |
| **Overall pilot demo recommendation** | **CONDITIONAL GO** |

Proceed with Chen demo using the 5-scene script when operator:
1. Confirms WeCom send path for demo external_userid (or accepts preview-only End Card with verbal explanation).
2. Runs demo from **customer WeCom → Workbench** (not stale seed queue).
3. Performs one manual Workbench `broker_done` click before customer session.

---

## Related

- Demo script: `docs/pilot/p19h3g_chen_demo_script_2026_07_10.md`
- Launch checklist: `docs/pilot/p19h3g_pilot_launch_checklist_2026_07_10.md`
- Evidence: `docs/evidence/p19h3f4_deploy_unified_status_card_text_frame_smoke_2026_07_10.md`
