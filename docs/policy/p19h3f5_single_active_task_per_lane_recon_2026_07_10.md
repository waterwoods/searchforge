# P19H-3f-5 — Single Active Task per Lane Recon

**Date:** 2026-07-10  
**Sprint:** P19H-3f-5 Recon  
**Status:** Recon complete — **GO (Hybrid)** recommended  
**Scope:** Claim + Add Car WeCom lanes; no code changes in this sprint

---

## Executive summary

The current system already behaves like **Single Active Task** in several happy paths (one open Claim, ordinary supplement → append; Add Car draft reuse on Start click). The main customer-friction gap is **multiple open Claims**: any inbound message today triggers **Collision Resolver / broker_confirm**, including ordinary supplements that should attach to the newest active Claim.

**Recommendation: GO — implement Single Active Task per Lane (Hybrid).**

- **Customer default:** one implicit active task per lane; ordinary content appends to the **most recently updated** open case.
- **Keep:** Confirm Card on **strong signals** only (new accident, another vehicle, cross-lane).
- **Remove from customer path:** multi-open picker / blanket `broker_confirm` on ordinary text.
- **Add broker-side:** `possible_multi_claim_context` risk flag + workbench correction tools (future).

Product analogy: Walmart Spark Driver — user completes **current task**; exceptions interrupt; backend retains log for ops correction.

---

## 1. Current behavior

### 1.1 Claim identity resolution (`resolve_claim_identity`)

Source of truth: `services/fiqa_api/wecom/claim_identity.py`  
Orchestration: `ingest_claim_basics_message()` in `claim_basics.py`

| Condition | Decision | Rule |
|-----------|----------|------|
| No open Claim for user | `create_new` | ID-A2 |
| 1 open Claim + explicit continuation markers | `append_existing` | ID-A6 |
| 1 open Claim + basics **incomplete** + ordinary text | `append_existing` | ID-A3 (active basics collection) |
| 1 open Claim + basics **incomplete** + explicit restart | `broker_confirm` → Collision Resolver | ID-A7 |
| 1 open Claim + **collision-triggering** text (accident narrative,「我要理赔」, passive markers like 追尾/事故) | `broker_confirm` → Collision Resolver | ID-A7 |
| 1 open Claim + **>72h** since `updated_at` + guided restart | `broker_confirm` | ID-A4 |
| **≥2 open Claims** + **any** ordinary inbound (not explicit new accident) | `broker_confirm` | **ID-A5** |
| **≥2 open Claims** + collision-triggering text | `broker_confirm` (multiple_open flag) | ID-A5 + ID-A7 |
| Explicit「新的事故」/ new accident markers (no collision path first) | `create_new` (direct) | ID-A1 |
| Injury mentioned + single open + would broker_confirm | **Override** → `append_existing` | ID-INJURY |

**Active Claim selection for routing helpers** (`find_active_claim_case_for_basics`): newest `updated_at` among open Claims — same sort as `list_open_claim_candidates_for_basics`.

### 1.2 When multiple open Claims are created

| Path | Mechanism |
|------|-----------|
| Customer explicit new accident (`create_new` / collision choice 2) | `_create_claim_case()` |
| Collision Resolver「开始新的事故记录」| `ingest_claim_collision_new()` |
| Add Car → Claim lane switch confirm | `ingest_claim_lane_switch_confirm()` |
| Prior broker_done Claim still open in storage + new start after terminal phase | New case when no *open* candidates remain |
| System/ops never closed duplicate Claims | **Backend accumulation** — not customer-intended |

There is **no hard limit** of one open Claim per `wecom_external_userid`. Multiple open Claims are a **data state**, not a product choice shown to the customer until they send the next message.

### 1.3 When append is blocked (Claim)

Append is blocked whenever `identity_decision.action == "broker_confirm"`:

1. **Multiple open Claims** — even for benign supplement text (e.g.「对方保险卡照片」) → Collision Resolver or multi-open dead-end.
2. **Collision-triggering input** with one open Claim whose basics are **complete** (or explicit restart during incomplete basics).
3. **Stale open Claim** (>72h) + guided restart markers.
4. **Active `claim_collision_pending`** — repeat prompt until customer chooses 1/2/3.
5. **WeCom images** — `media_intake.py` quarantines when identity is `broker_confirm` (Tier B ack, no bind).

Explicit continuation markers bypass collision triggers (`is_explicit_continuation`).

### 1.4 Multiple open Claim customer behavior today (P19H-3f-3 Collision Resolver)

| Customer action | Current behavior |
|-----------------|------------------|
| Ordinary supplement (no strong new-accident signal) | **Interrupted** — `broker_confirm` / resolver card |
| Accident-like narrative | Resolver card; if ≥2 open → **only「联系陈总」** button; choices 1/2 → `claim_collision_multiple_open` |
| Choice 1「继续上一个事故」| Append trigger text to **single** candidate only; blocked if ≥2 open |
| Choice 2「开始新的事故记录」| Create new Claim + Start Card; blocked if ≥2 open |
| Choice 3「联系陈总」| Manual handle; no append/create |
| Status request | Status Card for **newest** open Claim (`find_active_claim_case_for_basics`) — no multi-open note today |

Copy reference: `build_claim_collision_resolver_menu_payload(multiple_open=True)` — simplified card, effectively a **picker dead-end** pushing customer to broker.

### 1.5 Add Car lane — multiple active tasks

| Mechanism | Behavior |
|-----------|----------|
| `find_open_add_car_case_by_external_userid()` | Returns **first** open add_car match in store scan (attachment path) |
| `find_open_add_car_cases_for_progress()` | Returns **all** open, sorted newest-first |
| `create_or_attach_draft_case_for_start_click()` | Reuses existing draft unless `is_explicit_add_car_restart()` |
| Explicit restart markers | `重新加车`, `再加一辆车`, `新加一辆车`, etc. (`RESTART_ADD_CAR_PHOTO_MARKERS`) → **allows second case** |
| Progress Card | Shows **newest** case; if `open_case_count > 1`, tail: 「如果您同时办理多台车，请联系陈总。」 |
| Add Car collision resolver | **None** — no Confirm Card for「另一辆车」today (restart markers re-trigger H5 Start) |

**Conclusion:** Add Car **can** produce multiple open cases, but day-to-day UX already **defaults to one draft** + append. Multi-car is broker-tail only, not a customer picker.

### 1.6 Cross-lane behavior (preserved today)

| Transition | Behavior |
|------------|----------|
| Add Car active + explicit Claim start | Lane-switch Confirm Card (`build_claim_lane_switch_menu_payload`) — no silent switch |
| Add Car active + injury + Claim start | Safety path; may bypass lane-switch block |
| Claim → Add Car explicit | High-confidence `add_car` → new draft / H5 Start (no silent switch) |
| Secondary topic during Add Car | `secondary_topic_deferred` unless Claim interrupt rules win |

### 1.7 Pre-formal-task guardrails (unchanged, must keep)

- **Holding ack** (`ingest_claim_holding_ack`) — passive accident text, no open Claim → no formal case.
- **Start Card / injury menu** — formal Claim begins after guided start or lane-switch confirm.
- **Random photo before start** — media unassigned;「我要理赔」prompt only (`test_10` in collision suite).

---

## 2. Problems with multi-open picker / blanket Collision Resolver

| Problem | Impact |
|---------|--------|
| **Customer manages cases** | Resolver asks which Claim — backend object model exposed to WeChat user |
| **Ordinary supplement blocked** | ID-A5 fires on *any* text when ≥2 open — breaks「继续发照片/补充对方保险」 |
| **Multiple-open dead-end** | Choices 1/2 blocked → only「联系陈总」— user stuck mid-flow |
| **Over-trigger on narrative tokens** | `is_collision_triggering_input` matches 事故/追尾/被撞 in text that may still be same-Claim story |
| **Spark Driver mismatch** | Driver app never asks「which delivery batch?» mid-photo upload |
| **Broker work pushed to customer** | Duplicate Claim cleanup is ops work — should not be customer picker |

---

## 3. Why Single Active Task per Lane is simpler

| Principle | Customer experience |
|-----------|---------------------|
| One implicit **current** Claim | User keeps talking; system appends |
| One implicit **current** Add Car | Draft reuse + phase2 append |
| Strong signal → **one** Confirm Card (3 options) | Interrupt only when language clearly indicates new task or lane change |
| Multi-open → broker flag | Chen sees warning; can merge/close/move — user not blocked |
| Status / Progress | Always scoped to **active** (newest) task + gentle footnote |

Aligns with existing sort key (`updated_at` desc) already used for Status Card and progress.

---

## 4. Proposed routing rules (minimal viable policy)

### 4.1 Claim lane

```
IF no open Claim:
  guided start / high-confidence claim_intake → existing start paths (Holding ack, Start Card, etc.)

IF open Claim(s) exist:
  LET active = newest open Claim (by updated_at)

  IF status request:
    → Status Card for active
    IF count(open) > 1: footnote on card (see copy §6)

  IF explicit new-accident strong signal:
    → Confirm Card (continue current / start new / contact broker)
    → NOT multi-case picker

  IF cross-lane (Add Car active + Claim start):
    → existing lane-switch Confirm Card (unchanged)

  IF collision-triggering AND basics complete AND NOT explicit continuation:
    → Confirm Card (same 3-way — replaces blanket resolver for this case)

  ELSE ordinary claim text/photo:
    → append to active
    IF count(open) > 1: set broker risk flag possible_multi_claim_context
```

**Remove:** ID-A5 blanket `broker_confirm` on ordinary supplement when multiple open.

**Keep collision resolver machinery** but narrow triggers to strong-signal + post-basics collision narrative — not every multi-open message.

### 4.2 Add Car lane

```
IF open Add Car draft exists AND NOT explicit restart:
  → append / progress / phase2 (current behavior)

IF explicit another-vehicle signal (再加一辆车, 另外一辆车, 重新加车, …):
  → Confirm Card:
    1. 继续当前加车
    2. 开始另一辆车
    3. 联系陈总

IF multiple open Add Car (backend state):
  → default active = newest; append ordinary content
  → broker flag possible_multi_add_car_context (symmetric)
  → Progress tail already warns (keep)
```

### 4.3 Cross-lane (unchanged)

- Add Car → Claim: Confirm required  
- Claim → Add Car: Confirm required  
- No silent lane switch

---

## 5. Strong signal list

### 5.1 New Claim / another accident

| Signal | Notes |
|--------|-------|
| 新的事故 / 新事故 / 另一次事故 | Already in `EXPLICIT_NEW_ACCIDENT_MARKERS` |
| 不是上次那个 / 不是同一个事故 | **Add** |
| 今天又撞了 / 重新开一个 | **Add** |
| 重新理赔 | Existing |
| another accident / new accident | Existing |
| 我要理赔 / 开始理赔 | Collision trigger when basics complete — keep Confirm, not auto-new |

**Not strong signals (default append):** 事故时间地点描述, 对方保险, 照片, 进度/状态, 补充一下, 继续

### 5.2 Another Add Car vehicle

| Signal | Source |
|--------|--------|
| 再加一辆车 / 新加一辆车 / 另外一辆车 | `RESTART_ADD_CAR_PHOTO_MARKERS` (+ extend) |
| 重新加车 / 重新开始加车 | Existing |
| 第二辆车 / 另一台车 | **Add** |

### 5.3 Cross-lane

| Signal | Lane switch |
|--------|-------------|
| 我要理赔 / 出事故了 / injury | Add Car → Claim (existing) |
| 我要加车 / 新车要加保 | Claim → Add Car Confirm (**tighten** if today auto-starts) |

---

## 6. Customer-facing copy examples

### 6.1 Ordinary append (single or multi-open backend)

> 收到，已记到您当前这份事故记录里。  
> 您可以继续发照片或补充说明。

### 6.2 Status Card footnote (multiple open, gentle)

> 我会先按**最近这份**事故记录为您整理进度。  
> 如果不是同一个事故，请回复「新的事故」。

### 6.3 Confirm Card — Claim (strong signal)

```
【请确认】
您是要继续刚才那份事故记录，还是开始一份新的事故记录？

[继续当前事故]  [开始新的事故记录]  [联系陈总]

提醒：这只是资料收集，不代表已经向保险公司正式报案。
```

### 6.4 Confirm Card — Add Car (another vehicle)

```
【请确认】
您是要继续当前这辆车的加车资料，还是开始另一辆车？

[继续当前加车]  [开始另一辆车]  [联系陈总]
```

### 6.5 Broker-side only (not shown as picker)

Workbench tag: `possible_multi_claim_context`  
Activity: 「系统：该客户有 N 份未完成事故记录；最近消息已并入 case_xxx。请核对是否重复。」

---

## 7. Broker-side warning / correction strategy

**This recon does not implement** — recommended minimal backlog:

| Action | Purpose |
|--------|---------|
| **Close / Archive** | Remove stale open Claims from active set |
| **Mark Duplicate** | Link duplicate case_ids; suppress customer-facing ambiguity |
| **Move message/photo** | Reassign latest timeline event or attachment to another Claim |
| **Merge duplicate Claim** | Combine `known_facts`, `claim_timeline`, attachments into canonical case |
| **Workbench banner** | When `possible_multi_claim_context` or `count(open_claims)>1` |
| **Set active Claim** (broker) | Optional: pin customer’s active case without customer picker |

Existing workbench primitives: `workbench_tags`, `merge_review_required`, `conflict_state`, `claim_case_brief`, unassigned WeCom photo queue.

---

## 8. Risks

| Risk | Mitigation |
|------|------------|
| Wrong-Claim append when customer meant new accident | Strong-signal Confirm; footnote on Status; broker flag |
| Silent merge of two real accidents | Broker review flag + timeline preserved per case |
| Regression on P19H-3f-3 safety (no guess on narrative) | Keep Confirm for post-basics collision-triggering text |
| Add Car wrong-vehicle append | Add Car Confirm on restart markers (already partially exist) |
| `find_open_add_car_case_by_external_userid` returns arbitrary first | Align with newest-first sort (small fix) |
| Media mis-bind | Keep Tier B quarantine only for strong-signal ambiguity, not multi-open alone |
| Explicit new accident → `create_new` without Confirm | Consider routing ID-A1 through Confirm for consistency |

---

## 9. Tests needed

### 9.1 Proposed acceptance tests (implement with policy change)

| # | Scenario | Expected |
|---|----------|----------|
| 1 | Single active Claim + ordinary supplement | append, no Confirm |
| 2 | Single active Claim +「新的事故」| Confirm Card |
| 3 | Multiple open Claims + ordinary supplement | append to newest + `possible_multi_claim_context` |
| 4 | Multiple open Claims +「新的事故」| Confirm Card (not picker dead-end) |
| 5 | Status request, multiple open | Status Card for active + gentle note |
| 6 | Add Car ordinary phase2 info | append |
| 7 | Add Car「再加一辆车」| Confirm Card |
| 8 | Add Car → Claim explicit | Lane-switch Confirm (existing) |
| 9 | Claim → Add Car explicit | Confirm Card |
| 10 | Random photo before Start | no formal task (existing) |

### 9.2 Existing tests likely to **change**

| File | Test | Change |
|------|------|--------|
| `test_p19h3c_r3_claim_identity_resolver_foundation.py` | `test_04_multiple_open_claims_broker_confirm` | Expect `append_existing` + flag |
| same | `test_07_claim_basics_path_no_silent_newest_wins` | Ordinary「我要理赔」may differ |
| `test_p19h3f3_claim_collision_resolver.py` | `test_09_multiple_open_claims_no_silent_append_or_create` | Append to newest; Confirm only on strong signal |
| `test_p19h3d_wecom_claim_image_binding.py` | `test_03_multiple_open_claims_no_silent_bind` | Bind to newest active with broker flag |
| `test_p19h3f3_claim_collision_resolver.py` | `test_01`…`02` | Keep if post-basics collision narrative |

### 9.3 Tests to **keep unchanged**

- Lane switch Add Car ↔ Claim (`test_11`, `test_p19h21_*`)
- Injury safety override
- Holding ack / no formal case before start
- broker_done End Card (`test_12`)
- Explicit continuation append (`test_14`)

---

## 10. Recommendation

| Option | Verdict |
|--------|---------|
| **KEEP** current Collision Resolver as-is | **No** — multi-open blanket interrupt is too heavy for customers |
| **GO** Single Active Task per Lane | **Yes** — primary customer model |
| **HYBRID** | **Selected** — default append + narrowed Confirm Card + broker flags |

### Final: **GO (Hybrid)**

1. Implement Single Active Task per Lane for **customer routing**.  
2. **Retire** multi-open customer picker / ID-A5 blanket `broker_confirm`.  
3. **Reuse** Collision Resolver UI as the **Confirm Card** for strong signals only (single-open + multi-open).  
4. **Add** `possible_multi_claim_context` (and Add Car symmetric flag) on case/workbench.  
5. **Defer** broker merge/move UI to next workbench slice.

### Affected files (implementation slice)

| File | Change |
|------|--------|
| `services/fiqa_api/wecom/claim_identity.py` | Remove/replace ID-A5; add active-append + flag signal |
| `services/fiqa_api/wecom/claim_basics.py` | Wire flag; narrow `_emit_collision_resolver` triggers |
| `services/fiqa_api/wecom/reply.py` | Status footnote; simplify multi-open Confirm copy |
| `services/fiqa_api/wecom/media_intake.py` | Bind to newest when multi-open + ordinary media |
| `services/fiqa_api/inbox_triage/case_store.py` | Persist `risk_flags` / workbench tag helper |
| `services/fiqa_api/wecom/active_case_bridge.py` | Add Car Confirm routing for restart markers |
| `services/fiqa_api/wecom/add_vehicle_progress.py` | Optional Confirm before second draft |
| `services/fiqa_api/inbox_triage/claim_workbench_display.py` | Surface multi-open warning in brief |
| `tests/test_p19h3c_r3_*`, `test_p19h3f3_*`, `test_p19h3d_*` | Update per §9 |

### Implementation size estimate

**Small–medium** — mostly `resolve_claim_identity` + ingest branches + copy; no schema migration (JSON flags like `claim_collision_pending`).

---

## Appendix A — Audit answers (prompt §2)

1. **When are multiple open Claims created?** — Collision choice 2, explicit `create_new`, lane-switch confirm, broker not closing duplicates; not from Holding ack or raw photos.  
2. **When is append blocked?** — `broker_confirm`: multi-open (any text), collision-triggering with complete basics, stale+restart, pending collision state, media Tier B.  
3. **Multiple open behavior?** — Resolver / contact-broker dead-end; no silent append; Status uses newest only.  
4. **Add Car multiple active?** — Possible via explicit restart markers; otherwise one draft; progress uses newest.  
5. **Collision resolver over-interrupt?** — **Yes** for multi-open ordinary traffic; **appropriate** for post-basics new-accident narrative on single open.  
6. **Tests affected?** — See §9.2.  
7. **Safety to retain?** — No silent lane switch; injury override; no formal case before start; no coverage/carrier promises; broker_done terminal; media quarantine on true ambiguity.

---

## Appendix B — Evidence

- Code audit: `claim_identity.py`, `claim_basics.py`, `slice.py`, `intent.py`, `reply.py`, `case_store.py`, `claim_workbench_display.py`
- Prior art: `docs/evidence/p19h3f3_claim_collision_resolver_2026_07_10.md`
- Test baselines: `tests/test_p19h3c_r3_claim_identity_resolver_foundation.py`, `tests/test_p19h3f3_claim_collision_resolver.py`

---

*End of recon — STOP*
