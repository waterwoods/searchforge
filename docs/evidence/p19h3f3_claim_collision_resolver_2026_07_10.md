# P19H-3f-3 — Claim Collision Resolver

**Date:** 2026-07-10  
**Branch:** `sprint/p16-trust-layer`  
**Sprint:** P19H-3f-3 Claim Collision Resolver

---

## 1. Problem

When a WeCom user already has one or more **unfinished** Claim cases and sends new accident-like content (narrative, explicit「我要理赔」, etc.), the system must **not guess** whether to append to the old Claim or start a new one.

Prior behavior (P19H-3c-R3):
- Text-only broker-confirm prompt (`未完成的理赔记录` + reply 1/2)
- **No** `claim_collision_pending` state
- **No** WeCom button menu
- **No** choice handler — replies `1`/`2`/`3` did not reliably route
- Single recent open Claim + accident narrative **auto-appended** (silent bind risk)

---

## 2. Product principle

1. System cannot guess old vs new accident.
2. Open Claim + ambiguous new accident content → **Collision Resolver Card**.
3. Only explicit「开始新的事故记录」/ choice `2` → create new Claim + **Start Card**.
4. Only explicit「继续上一个事故」/ choice `1` → append to existing Claim.
5.「联系陈总」/ choice `3` → manual handle, no create, no append.
6. Resolver Card ≠ Start Card.
7. Start Card policy, Add Car lane switch, broker_done End Card, raw inbound hidden — all preserved.

---

## 3. Existing behavior (pre-3f-3)

| Function | Role |
|----------|------|
| `resolve_claim_identity()` | Decided append / create / broker_confirm |
| `build_claim_identity_broker_confirm_reply()` | Plain text prompt |
| `ingest_claim_basics_message()` | Returned prompt on `broker_confirm`, no pending state |

**Gaps:** no pending state, no buttons, no choice routing, auto-append on recent single open Claim.

---

## 4. New resolver behavior

**Trigger (Case A/B):** open Claim (basics complete or explicit restart) + collision-triggering input.

**Do not trigger during active basics collection** (same-Claim story fill) unless explicit restart markers.

**Card copy (single open Claim):**

```
【理赔资料收集】
我看到您这边已经有一个未完成的事故记录。
为了避免把两次事故资料混在一起，请选择：
1️⃣ 继续上一个事故，补充资料
2️⃣ 开始新的事故记录
3️⃣ 联系陈总人工处理
```

**Buttons:** `[继续上一个事故]` `[开始新的事故记录]` `[联系陈总]`

**Multiple open Claims:** simplified copy + contact-Chen primary button; choices `1`/`2` blocked with manual-handle reply.

---

## 5. Choice handling

| Choice | Action |
|--------|--------|
| `1` / 继续上一个事故 | Append `trigger_text` to existing Claim; continue-collection reply |
| `2` / 开始新的事故记录 | Create new Claim; emit Start Card; seed timeline with trigger text |
| `3` / 联系陈总 | Manual handle; no create/append |

---

## 6. Pending state (`claim_collision_pending` on case extra bag)

```json
{
  "state": "pending_choice",
  "candidate_claim_ids": ["case_..."],
  "trigger_text": "...",
  "trigger_msg_id": "...",
  "created_at": "...",
  "source": "wecom",
  "reason": "existing_open_claim_plus_new_accident_like_input"
}
```

Stored via `update_claim_collision_pending()` — **no schema migration**.

---

## 7. Idempotency

- Repeated accident narrative while pending → re-send resolver, no new Claim
- Repeated `2` after resolution → idempotent Start Card for same new Claim
- Choice `1` uses `trigger_msg_id` dedup for timeline append

---

## 8. Tests

`tests/test_p19h3f3_claim_collision_resolver.py` — 14 cases covering resolver, choices, idempotency, multiple open, regressions, live `process_kf_msg_or_event` path.

```bash
PYTHONPATH=. python3 -m pytest tests/test_p19h3f3_claim_collision_resolver.py -q
PYTHONPATH=. python3 -m pytest tests/test_p19h3f2_live_add_car_claim_lane_switch.py -q
PYTHONPATH=. python3 -m pytest tests/test_p19h_state_machine_temporal_invariants.py -q
PYTHONPATH=. python3 -m pytest tests/test_p19h3f1_case_boundary_policy.py -q
PYTHONPATH=. python3 -m pytest tests/test_p19h3f1c_start_card_only_intake_policy.py -q
PYTHONPATH=. python3 -m pytest tests/test_p19h3f2_true_end_card_on_broker_done.py -q
PYTHONPATH=. python3 -m pytest tests -q -k "claim"
PYTHONPATH=. python3 -m pytest tests -q -k "h5"
```

All **PASS** locally.

---

## 9. Deploy

| Item | Value |
|------|-------|
| Command | `bash scripts/deploy_paid_pilot.sh` |
| Service | Cloud Run `fiqa-api` |
| GIT_SHA | `49941303d` |
| Revision | Cloud Run `fiqa-api` (2026-07-10 deploy) |
| `/version` | 200 — commit matches |
| `/health/live` | 200 |
| `/readyz` | 200 |

---

## 10. Production smoke

| Smoke | Expected | Result |
|-------|----------|--------|
| A — open Claim + new narrative | Resolver, no new Claim | **PASS** (pytest + `process_kf_msg_or_event`) |
| B — reply `1` | Append to existing | **PASS** (pytest) |
| C — reply `2` | New Claim + Start Card | **PASS** (pytest) |
| D — reply `3` | Manual handle | **PASS** (pytest) |
| E — multiple open | No silent create/append | **PASS** (pytest) |
| F — regressions | Start Card / lane switch / broker_done / H5 | **PASS** (pytest) |
| Cloud health | `/version` `/health/live` `/readyz` | **PASS** (`49941303d`) |

---

## 11. Constraints

- No schema change / no new DB table
- No OCR / ASR / damage AI / fault / coverage / carrier filing / LLM brief
- No silent append or create
- Start Card policy preserved

---

## 12. Known limitations

- Multiple open Claims: no per-Claim picker UI in 3f-3; contact-Chen fallback
- Collision resolver not wired for media-only intake path (text path + slice primary)
- `1`/`2`/`3` text fallback conflicts with guided menu numbers when no pending state (mitigated: only routes when `claim_collision_pending` active)

---

## 13. Next recommended prompt

- Pilot Demo Script / Chen readiness
- Claim → Add Car inverse lane switch (later)

---

## Files changed

- `services/fiqa_api/wecom/claim_identity.py`
- `services/fiqa_api/wecom/claim_basics.py`
- `services/fiqa_api/wecom/reply.py`
- `services/fiqa_api/wecom/intent.py`
- `services/fiqa_api/wecom/slice.py`
- `services/fiqa_api/inbox_triage/case_store.py`
- `tests/test_p19h3f3_claim_collision_resolver.py`
- `tests/test_p19h3c_r3_claim_identity_resolver_foundation.py` (assertion updates)
