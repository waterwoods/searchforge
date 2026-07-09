# P19H-3f-4 — Unified Status Card + Text Frame Style

**Date:** 2026-07-10  
**Branch:** `sprint/p16-trust-layer`  
**Type:** WeCom copy + routing — no schema, no deploy

---

## 1. Goal

Unify WeCom system messages into clear, bounded **text-frame cards** so customers recognize formal status information (not casual chat). Add deterministic **Claim Status Card** and status-request routing.

---

## 2. Card taxonomy

| Internal name | Customer title | Purpose |
|---------------|----------------|---------|
| Start Card / 开始卡 | 【事故记录已开始 ✅】 | Formal Claim workflow start |
| Status Card / 状态卡 | 【当前状态】 | Progress / received / missing / next step |
| Confirm Card / 确认卡 | 【请确认】 | Add Car → Claim lane switch |
| Collision Resolver / 事故选择卡 | 【请选择事故记录】 | Continue / new / contact broker |
| End Card / 结束卡 | 【陈总已确认 ✅】 | `broker_done` collection phase end |

---

## 3. Text frame style

Helper: `frame_wecom_card(title, body_lines, footer_lines=None)` in `services/fiqa_api/wecom/reply.py`

```
━━━━━━━━━━━━
【标题】

正文段落…

下一步：
…

提醒：
…
━━━━━━━━━━━━
```

Applied to Start, Status, Confirm, Collision Resolver, and End cards. C1 stage-complete uses the same frame with title 【事故信息已记录 ✅】.

---

## 4. Claim Status Card behavior

- Builder: `build_claim_status_card_reply(case, display=None)`
- Data: `claim_phase`, `build_claim_case_brief()` → `key_facts`, `highlights`, `missing_info`, `evidence_received`, `next_best_question`
- Sections: 状态 / 客户 / 事故时间·地点 / 已收到 / 还缺 / 下一步 / 提醒
- Missing fields show **待确认**, not blank
- `broker_done`: 状态 = 陈总已确认 / 收集阶段已结束

---

## 5. Status request behavior

Intent helper: `is_claim_status_request()` in `intent.py`

Triggers (examples): 进度 · 状态 · 现在到哪了 · 理赔进度 · 看一下状态

| Condition | Reply |
|-----------|--------|
| Active Claim | Status Card |
| No active Claim | No-active guidance + suggest「我要理赔」 |
|「我要理赔」| Explicit start (not status) |
|「看看这个」| Not status |

Routing: `should_route_claim_status_request` → `ingest_claim_status_request` in `slice.py` (before holding / guided basics).

After `basics_complete`: framed C1 stage-complete card (once). Photo ack stays short; mentions reply「状态」.

---

## 6. Updated card copy examples

**Start Card** — framed; retains 陈总办公室 / 有没有受伤 / 不代表已经向保险公司正式报案.

**Status Card** — 【当前状态】+ 已收到 / 还缺 / 下一步.

**Confirm Card** — 【请确认】+ 开始事故记录 / 继续加车.

**Collision Resolver** — 【请选择事故记录】+ 继续上一个事故 / 开始新的事故记录 / 联系陈总.

**End Card** — 【陈总已确认 ✅】+ 收集阶段已结束 disclaimer.

---

## 7. Tests

`tests/test_p19h3f4_unified_status_card.py`

Also run regression:

- `test_p19h3f3_claim_collision_resolver.py`
- `test_p19h3f2_*`
- `test_p19h3f1_case_boundary_policy.py`
- `test_p19h3f1c_start_card_only_intake_policy.py`

---

## 8. Constraints

- No schema / DB table changes
- No WeCom template card
- No OCR / ASR / damage AI
- No fault / liability / coverage / carrier filing
- No LLM brief
- Start Card / End Card / Collision decision logic unchanged

---

## 9. Known limitations

- Enterprise WeCom template card deferred
- Add Car Status Card out of scope (Add Vehicle progress card unchanged)
- Status Card after every photo intentionally not sent (short ack only)

---

## 10. Next recommended prompt

1. **P19H-3f-4 deploy smoke** — verify framed cards on live WeCom
2. **Pilot Demo Script / Chen readiness** — operator walkthrough with unified card language
