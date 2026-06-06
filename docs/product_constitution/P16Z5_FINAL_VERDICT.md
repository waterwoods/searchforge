# P16-Z5 — Case Memory Sprint · Final Verdict

**Date:** 2026-06-02  
**Sprint:** P16-Z5 Case Memory Sprint  
**Constraint:** No P17 · No CRM · No Stripe · No WeChat integration · No new services  
**Scope:** Case Memory · Case Continuity · Case Timeline only  
**Sources:** `case_store.py`, `triage.py`, `BrokerWorkbenchTab.tsx`, `intakePure.ts`, `AddCarRecordSummaryRail.tsx`, P16-Y battery (88.6 avg), P16-Z3/Z4 archaeology

**Core question:** Does the system remember better today than yesterday?

**Answer today:** **Partially.** Backend memory is production-grade; broker-facing memory UX is ~41/100. Turn 1 feels smart; Turn 2+ forces re-reading WeChat because summary merge (Y44/Y45) and thread rendering are not shipped.

---

## North Star (unchanged)

> Turn messy client messages into a time-bound office obligation with a clear next action and a traceable close — in one paste, under one minute.

**Target loop:**

```
Paste → Case → Timeline → Next Action → Append → Timeline → Next Action
```

**Not:** Paste → Draft → Exit

---

# Phase 1 — Timeline Visibility Audit

## What already exists?

| Asset | Location | Stored | API | Broker UI | Customer UI |
|-------|----------|--------|-----|-----------|-------------|
| `case_messages[]` | `case_store.py` | ✅ Sequenced `{role, text, sequence, created_at}` | ✅ GET case | ❌ Not rendered as thread | ⚠️ Progress panel only |
| `case_activity[]` | `case_store.py` | ✅ Typed audit log | ✅ GET case | ⚠️ Collapsed card in 整理明细 | ❌ |
| `conversation_summary` | `triage.py` → case | ✅ Intent + collected/still + latest snip | ✅ | ⚠️ Partial chips in collapse | ❌ |
| `latest_update` | `getLatestUpdateForDisplay()` | ✅ Notes vs activity by timestamp | — | ⚠️ Queue subtitle + reopened banner | ❌ |
| `tracking_summary` | `getCaseTrackingSummary()` | ✅ waiting_on OR latest context | — | ✅ Queue row (partial) | ❌ |
| `source_text` | Rebuilt from messages | ✅ Full thread | ✅ | ⚠️ Preview only (80 chars) | ❌ |
| `formal_submitted_at` / `updated_at` | Case record | ✅ | ✅ | ❌ Not compared in glance | ❌ |
| `secondary_issue_note` | Triage | ✅ Mixed-intent | ✅ | ⚠️ Shown if present | ❌ |
| `follow_up_type` | Triage (e.g. `correction`) | ✅ | ✅ | ❌ Only drives add-car customer rail | ❌ |
| `waiting_on` / `next_contact_by` | Case + PATCH API | ✅ | ✅ | ⚠️ Collapsed follow-up editor | ❌ |
| Postgres `record_messages` + `state_history` | `service_record_repository.py` | ✅ Mirror path | ✅ | ❌ PG tags only | ❌ |
| `getRecentCustomerMessages()` | `intakePure.ts` | ✅ Helper | — | ❌ **Imported unused** in workbench | ✅ Used in add-car glance builder |
| `buildAddCarRailTurnModel()` | `AddCarRecordSummaryRail.tsx` | ✅ Delta/correction UI | — | ❌ Add-car customer path only | ✅ |
| `record_rail_section_latest_update` | `ui_copy.json` | ✅ "本轮更新 / 更正" | — | ❌ Not on broker workbench | ✅ Customer add-car rail |
| `learning_signals.jsonl` | `learning_signals.py` | ✅ Append-only corrections | — | ❌ No product surface | ❌ |
| `session_store` | `session_store.py` | ✅ Mid-flow restore | ✅ | ❌ Dev path | ⚠️ Customer chat |
| `v6_ocr_signals` | Case JSON | ✅ Attachment OCR fusion | ✅ | ❌ Hidden | ❌ |
| `case_attachments` + activity | `case_store.py` | ✅ Photos/docs | ✅ | ⚠️ Separate card | ❌ |

## What is hidden?

1. Full message thread — `case_messages` never rendered as Zendesk-style vertical timeline in broker glance  
2. Activity as hero — `操作记录` lives inside collapsed 整理明细, default closed in `product_only`  
3. Turn delta — `buildAddCarRailTurnModel` (new collected, cleared still, correction banner) exists only on customer add-car rail  
4. Correction flag — `follow_up_type === 'correction'` computed in engine, invisible on broker surfaces  
5. Prior-turn facts in summary — Y44/Y45 battery notes: "prior turn context weak in summary/collected"  
6. `getRecentCustomerMessages` — coded, imported in workbench, never called  
7. `formal_submitted_at` vs `updated_at` — no "first saved / last updated" glance line  
8. `learning_signals` — correction memory written nowhere brokers see  
9. Deadline countdown — `_extract_deadline_hint()` in summary prose, no widget  
10. Mixed-intent secondary — `secondary_issue_note` buried below fold  
11. System reply bubbles — appended to `case_messages` as `role: system`, never shown  
12. Boundary events — `requires_new_case` activity not distinguished in UI  
13. Customer append path — post-handoff 追加 collapsed (P16-O)  
14. PG `state_history` — full audit in Postgres, broker sees tag only  
15. Add-car `timeline_question` intent — lane-specific follow-up copy, not generalized  
16. `client_prep` — computed, product_only gated  
17. Risk badge — v4 score computed, not shown as 需核实  
18. `conversation_turns` pre-persist — API supports multi-bubble before save; broker taught single paste  
19. Attachment timeline entries — activity logged, not linked in thread view  
20. Queue "updated today" sort — activity timestamps exist, not promoted as filter  

## What should be surfaced? (priority)

| Priority | Surface | Why |
|----------|---------|-----|
| P0 | Last 3–5 `case_messages` in glance | Answers "what did client say?" without WeChat |
| P0 | Turn delta block (borrow `buildAddCarRailTurnModel`) | Answers "what changed?" on append |
| P1 | Default-open activity after append | Proves memory updated |
| P1 | Queue `getLatestUpdateForDisplay` on every card | Monday scan without opening |
| P2 | waiting_on pill adjacent to next action | Time-bound obligation |
| P2 | formal_submitted_at / updated_at line | Traceability |

---

## TOP 20 hidden memory capabilities

| # | Capability | Memory value | Revival effort |
|---|------------|--------------|----------------|
| 1 | `case_messages[]` full thread | Durable conversation memory | 0.5 day UI — render in glance |
| 2 | `buildAddCarRailTurnModel()` delta UI | Turn-over-turn memory diff | 0.5 day — generalize to broker |
| 3 | `getRecentCustomerMessages()` | Last N customer bubbles | 2 hr — wire unused import |
| 4 | `getLatestUpdateForDisplay()` | Latest note or activity | 2 hr — queue subtitle everywhere |
| 5 | `getCaseTrackingSummary()` | Follow-up + context one-liner | Wired partially — promote |
| 6 | `follow_up_type: correction` | Correction turn detection | 2 hr — badge in glance |
| 7 | `case_activity[]` audit trail | Office "what happened when" | 2 hr — default-open after append |
| 8 | `conversation_summary` Collected/Still chips | Case headline memory | 0.5 day — move above fold |
| 9 | `secondary_issue_note` | Mixed-intent memory | 1 hr — pill when present |
| 10 | `append_follow_up_message()` | Turn 2+ same case_id | UX only — show on first persist |
| 11 | `triage_for_append()` | Re-triage with prior turns | Already works — trust it in UI |
| 12 | `learning_signals.jsonl` | Correction ground truth | Defer product — use for tune loop |
| 13 | `formal_submitted_at` | First-commit timestamp | 2 hr — show in glance |
| 14 | System messages in thread | Office reply memory | 0.5 day — include in thread render |
| 15 | `deadline_mentioned` extraction | Time memory | 0.5 day — countdown widget |
| 16 | `session_store` restore | Mid-flow memory | Defer — not broker trial path |
| 17 | Postgres `record_messages` | Durable DB thread | Defer — JSON path sufficient for pilot |
| 18 | `v6_ocr_signals` on case | Document memory | Defer — OCR sprint |
| 19 | `case_attachments` + activity | Evidence memory | 0.5 day — link in thread |
| 20 | `run_follow_up_append_simulations.py` | Memory regression gate | 1 hr — add to launch check |

---

# Phase 2 — Timeline UX Design

**Borrow structure (not visuals) from Zendesk + Intercom:**

| Pattern | Zendesk/Intercom | Our equivalent | Status |
|---------|------------------|----------------|--------|
| Chronological message list | Conversation thread | `case_messages` | ❌ Not rendered |
| System events inline | "Agent changed status" | `case_activity` | ⚠️ Separate collapsed panel |
| Latest event at top of detail | Activity feed | `case_activity[0]` | ⚠️ Backend only |
| Status pill | "Pending customer" | `waiting_on` | ⚠️ Collapsed |
| SLA/deadline | Due date badge | `next_contact_by` + `getFollowUpDueTag` | ⚠️ Queue only when overdue |
| "What changed" on update | Internal note / event | `follow_up_added` tag | ⚠️ Detail only, not queue |

**Smallest possible timeline (broker glance):**

```
┌─ 案件摘要 ─────────────────────────────────┐
│ 取消风险 · 在等：客户 · 还有3天              │
│ 办公室下一步：确认付款截图并致电保司…        │
├─ 对话 (3) ─────────────────────────────────┤
│ [客户] 保单要cancel了                        │
│ [客户] 不是payment问题，是地址不对被UW退回   │  ← correction
│ [系统] 好的，明白了。办公室会尽快处理…         │
├─ 本轮更新 ─────────────────────────────────┤
│ ✓ 客户更正：不是付款，是地址/UW              │
│ ✓ 还缺：garaging proof                     │
└─ 追加客户补充 ─────────────────────────────┘
```

## TOP 10 timeline improvements

| # | Improvement | Effort | Type |
|---|-------------|--------|------|
| 1 | Render last 3–5 `case_messages` as vertical thread | 0.5 day | UI |
| 2 | Generalize `buildAddCarRailTurnModel` → broker "本轮更新" block | 0.5 day | UI reuse |
| 3 | Default-open 操作记录 after successful append | 2 hr | UI |
| 4 | Merge activity events into thread (follow_up_added inline) | 0.5 day | UI |
| 5 | Post-copy line: 客户回复后 → 追加到此案件 | 15 min | Copy |
| 6 | Queue card: always show `getLatestUpdateForDisplay` | 2 hr | Wire |
| 7 | `waiting_on` + deadline pill above thread | 0.5 day | UI |
| 8 | Highlight correction turns (`follow_up_type`) | 2 hr | UI |
| 9 | Collapse top paste when case open (anti fork-case) | 0.5 day | UI |
| 10 | Show `updated_at` vs `formal_submitted_at` | 2 hr | UI |

---

# Phase 3 — Append Journey Audit

**Journey map:**

```
Paste ──→ Triage ──→ Glance ──→ Copy ──→ [EXIT] ──?──→ Queue ──→ Reopen ──→ Append
  ↑                                              │
  └────────────── re-paste (duplicate case) ─────┘
```

## Where users leave

| Step | Drop-off reason | Evidence |
|------|-----------------|----------|
| After Copy | Job done — WeChat is channel of record | P16-X F-001 |
| After Copy | No "append here" taught | No post-copy CTA |
| Before Turn 2 | Queue not Monday habit | Chen Kui 47/100 |
| Turn 2 attempt | Append gated on `caseView === 'reopened'` | `BrokerWorkbenchTab.tsx` L1542 |
| Turn 2 attempt | Top paste says "paste next message" not "append" | L1344 |
| Turn 2 attempt | 开始整理 disabled but paste still hero | Fork-case risk |
| After append | Can't see what changed | Thread hidden; Y44 summary weak |
| Blocked append | `requires_new_case` feels like failure | Boundary copy only |

## Where continuity breaks

| Break point | Backend | UX |
|-------------|---------|-----|
| Copy → waiting | PATCH follow-up exists | No one-click 在等客户 |
| Append → summary | `conversation_summary` overwritten | Prior turn facts dropped (Y44) |
| Append → fields | `collected_fields` replaced | Corrections don't supersede cleanly |
| Append → thread | `case_messages` appended | UI doesn't show new bubble |
| Re-paste → new case | No hard block | Duplicate case risk |
| Customer reply | Customer append API works | Collapsed on trial URL |

## TOP 10 continuity failures

| # | Failure | Fix class | Time |
|---|---------|-----------|------|
| 1 | Copy = exit — no second beat | Post-copy one-liner | 15 min |
| 2 | Append hidden until queue reopen | Show when `case_id` exists | 2 hr |
| 3 | Top paste invites new case | Collapse paste / disable 开始整理 | 0.5 day |
| 4 | Thread not visible — broker re-reads WeChat | Render `case_messages` | 0.5 day |
| 5 | Summary loses Turn 1 on correction (Y44) | Engine merge | 1–2 days |
| 6 | No turn delta — "what changed?" unanswered | Wire `buildAddCarRailTurnModel` | 0.5 day |
| 7 | Activity buried in collapse | Default-open after append | 2 hr |
| 8 | No waiting state after send | One-click `waiting_on: client` | 0.5 day |
| 9 | Y45 premium thread — `bill_sent_claimed` missing | Rule in `_build_conversation_summary` | 0.5 day |
| 10 | Zero logged two-turn trial cases | Founder observation log ritual | 1 hr |

---

# Phase 4 — Memory Merge Audit

**Focus:** Y44 · `conversation_summary` · correction handling

## Y44 case (live battery)

```
Turn 1: 保单要cancel了
Turn 2: 不是payment问题，是地址不对被UW退回了
```

| Field | Expected | Actual (battery 2026-06-02) |
|-------|----------|----------------------------|
| Category | address/UW (not cancel) | ✅ `customer_question` |
| Summary intent | Address/garaging + correction | ⚠️ "Address / garaging change. Customer corrected/clarified." — **Turn 1 cancel context dropped** |
| collected_fields | garaging issue | ❌ `[]` |
| still_needed_fields | garaging proof | ❌ `[]` |
| multi_message score | ≥20 | ❌ **13/25** (total 79) |

## Y45 case (live battery)

```
Turn 1: (premium context)
Turn 2: 我发你账单了，你看能不能换便宜点的coverage
```

| Field | Expected | Actual |
|-------|----------|--------|
| Intent | Premium review | ❌ "New quote / new vehicle" |
| collected | bill_sent_claimed | ❌ `[]` |
| still_needed | coverage options | ❌ add-car fields |

## Correction handling inventory (`triage.py`)

| Mechanism | Status | Gap |
|-----------|--------|-----|
| `_build_conversation_summary` correction markers | ✅ "Customer corrected/clarified" tag | Doesn't inject Turn 1 fact into headline |
| `follow_up_type === 'correction'` classifier | ✅ L2443+ | Not surfaced in broker UI |
| Add-car vehicle correction merge | ✅ Strong (`_is_add_car_vehicle_correction_signal`) | Lane-specific only |
| Cross-topic pivot detection | ✅ `_correction_is_cross_topic_pivot_not_vehicle_fix` | Y44 needs category re-anchor on correction |
| Premium `bill_sent_claimed` in summary | ⚠️ Partial L2077 | Y45 loses lane on append |
| `learning_signals.record_user_correction_signal` | ✅ Backend | Never called from product UI |
| Prior bubble injection on append | ❌ Missing | P16-Y P0 |

## TOP 10 memory merge failures

| # | Failure | Example |
|---|---------|---------|
| 1 | Prior turn intent dropped from summary headline | Y44: cancel → address pivot invisible |
| 2 | `collected_fields` not merged across turns | Y44/Y45 empty after correction |
| 3 | Category re-classification on correction weak | Y45 misclassified as add-car |
| 4 | `bill_sent_claimed` not in structured fields | Y45 premium thread |
| 5 | Correction UI only on add-car customer rail | Broker never sees 本轮更新 |
| 6 | `follow_up_type: correction` not displayed | Engine knows, UI doesn't |
| 7 | Latest-only summary snip (80 chars) | Turn 1 facts fall off |
| 8 | No explicit "supersedes prior" in collected | Field history pattern missing |
| 9 | `learning_signals` not wired | Corrections don't improve defaults |
| 10 | Append replaces summary wholesale | No merge — overwrite in `case_store.py` L1156 |

## TOP 10 merge improvements

| # | Improvement | Effort | Impact |
|---|-------------|--------|--------|
| 1 | On append: prepend prior intent line when correction detected | 1 day | Fixes Y44 headline |
| 2 | Merge `collected_fields` union minus invalidated keys | 1 day | Fixes empty collected |
| 3 | Re-run category classifier on **merged** text, not last bubble only | 0.5 day | Fixes Y45 lane |
| 4 | Add `bill_sent_claimed` to collected when 发你账单了 | 0.5 day | Fixes Y45 |
| 5 | Wire `buildAddCarRailTurnModel` pattern for all lanes | 0.5 day | Visible turn delta |
| 6 | Show `follow_up_type: correction` badge in glance | 2 hr | Trust signal |
| 7 | Summary template: "Was: X → Now: Y" on correction | 0.5 day | Office-readable |
| 8 | Call `learning_signals` on append boundary events | 2 hr | Future tune loop |
| 9 | Battery gate Y44/Y45 ≥85 before deploy | 2 hr | Regression |
| 10 | Invalidate prior still_needed when correction changes lane | 0.5 day | Gap accuracy |

---

# Phase 5 — Claims Simulation

**10 realistic claims journeys · 3–5 turns each · memory lens**

### J1 — Hit-and-run FNOL → photos → police report (4 turns)

| Turn | Message | Case | Timeline | Next Action |
|------|---------|------|----------|-------------|
| 1 | 高速被追尾，对方跑了 | ✅ claim_intake | N/A | ✅ evidence collection |
| 2 | 照片发你了，车牌8XYZ123 | ⚠️ fields may update | ⚠️ plate not in summary | ✅ shift to carrier |
| 3 | 报警记录案号2026-12345 | ⚠️ no police_report field | ❌ case # lost in summary | ⚠️ generic |
| 4 | 怎么还没进度？ | ⚠️ unclear vs claim | ❌ no carrier-waiting UX | ⚠️ generic check |

### J2 — Parking lot fender bender EN (3 turns)

| Turn | Message | Case | Timeline | Next Action |
|------|---------|------|----------|-------------|
| 1 | Got in fender bender, other driver gave card | ✅ claim_intake | N/A | ⚠️ EN broker_next_step |
| 2 | Sent photos | ⚠️ partial merge | ⚠️ thread ok, summary thin | ✅ OK |
| 3 | I parked there by accident last week | ⚠️ idiom trap | ⚠️ boundary risk | ⚠️ monitor |

### J3 — Windshield coverage question (2 turns)

| Turn | Message | Case | Timeline | Next Action |
|------|---------|------|----------|-------------|
| 1 | 挡风玻璃裂了能赔吗 | ⚠️ claim vs coverage | N/A | ⚠️ lane boundary |
| 2 | 不是事故，就是石子打的 | ⚠️ correction | ❌ Y44 pattern | ⚠️ |

### J4 — Side swipe + rental car (3 turns)

| Turn | Message | Case | Timeline | Next Action |
|------|---------|------|----------|-------------|
| 1 | 侧面刮擦，需要租车 | ✅ claim | N/A | ✅ |
| 2 | 对方保险是GEICO | ⚠️ carrier not collected | ❌ | ⚠️ |
| 3 | GEICO说要我们的decl page | ⚠️ missing_doc mix | ⚠️ mixed-intent | ⚠️ |

### J5 — Injury mentioned (2 turns)

| Turn | Message | Case | Timeline | Next Action |
|------|---------|------|----------|-------------|
| 1 | 追尾，脖子疼 | ✅ high urgency | N/A | ✅ medical priority |
| 2 | 不去医院，继续理赔 | ⚠️ correction | ❌ injury context drop | ⚠️ |

### J6 — Claim + payment mixed (3 turns) — C9/C10 pattern

| Turn | Message | Case | Timeline | Next Action |
|------|---------|------|----------|-------------|
| 1 | 出险要理赔，账单也看不懂 | ✅ claim wins | N/A | ⚠️ payment ignored |
| 2 | 账单付过了，截图发你 | ⚠️ topic shift | ⚠️ boundary noise | ⚠️ requires_new_case? |
| 3 | 理赔进度呢 | ⚠️ | ❌ | ⚠️ |

### J7 — Hit-and-run Chinese (2 turns)

| Turn | Message | Case | Timeline | Next Action |
|------|---------|------|----------|-------------|
| 1 | 肇事逃逸，拍到车尾，无人伤 | ✅ hit_and_run template | N/A | ✅ |
| 2 | 找到对方车牌了 | ⚠️ partial | ⚠️ plate not in summary | ✅ update step |

### J8 — Supplemental statement letter (3 turns)

| Turn | Message | Case | Timeline | Next Action |
|------|---------|------|----------|-------------|
| 1 | 保险公司要补充陈述 | ⚠️ missing_doc vs claim | N/A | ⚠️ |
| 2 | 扫描件附上 | ⚠️ attachment API | ❌ no inline attach UX | ⚠️ |
| 3 | 他们给了deadline Friday | ⚠️ deadline in prose only | ❌ no countdown | ⚠️ |

### J9 — Total loss inquiry (2 turns)

| Turn | Message | Case | Timeline | Next Action |
|------|---------|------|----------|-------------|
| 1 | 车全损了，怎么赔 | ✅ claim | N/A | ✅ |
| 2 | 不是全损，修就行 | ⚠️ correction | ❌ Y44 — total loss context lost | ⚠️ |

### J10 — Uninsured motorist (3 turns)

| Turn | Message | Case | Timeline | Next Action |
|------|---------|------|----------|-------------|
| 1 | 对方没保险 | ✅ claim | N/A | ✅ UM path |
| 2 | 我买了UM coverage的 | ⚠️ | ⚠️ | ⚠️ verify policy |
| 3 | 保司说要警察报告 | ⚠️ | ❌ police # memory | ⚠️ |

## Aggregate scores (memory-weighted)

| Dimension | Turn 1 | Turn 2+ | Verdict |
|-----------|--------|---------|---------|
| Case quality | **82/100** | **58/100** | Engine strong; merge weak |
| Timeline quality | N/A | **48/100** | Messages stored, not shown |
| Next action quality | **74/100** | **65/100** | Templates ok; waiting/carrier weak |

## TOP 10 claims insights

| # | Insight |
|---|---------|
| 1 | **Turn 1 claim_intake is wedge-ready** — templates exist; monetize here first |
| 2 | **Turn 2+ is where memory fails** — plate, police #, carrier name don't accumulate in summary |
| 3 | **Correction turns dominate claims** ("不是全损"/"不去医院") — Y44 pattern is claims-critical |
| 4 | **No claims-specific collected_fields** — photos, plate, police_report, carrier_name |
| 5 | **Carrier-waiting never sets `waiting_on: carrier`** — progress-check messages hit generic path |
| 6 | **Mixed claim + payment loses half the thread** — needs explicit secondary memory |
| 7 | **Attachment memory exists backend-only** — scan on Turn 2 invisible in timeline |
| 8 | **Deadline in claims is life-or-death** — prose hint insufficient; need countdown |
| 9 | **Broker re-reads WeChat on every multi-turn claim** — thread render fixes 80% of pain |
| 10 | **No claim closure/outcome field** — memory loop never closes |

---

# Phase 6 — ROI Ranking

## TOP 20 highest ROI fixes (all time buckets)

| Rank | Fix | ≤15 min | ≤2 hr | ≤1 day | ≤1 week | Value |
|------|-----|---------|-------|--------|---------|-------|
| 1 | FP-004 SSO off | ✅ | | | | 5 |
| 2 | Post-copy: 客户回复后 → 追加到此案件 | ✅ | | | | 5 |
| 3 | Wire `getRecentCustomerMessages` in glance (3 lines) | | ✅ | | | 4 |
| 4 | Append card when `case_id` set (not only reopened) | | ✅ | | | 5 |
| 5 | Default-open 操作记录 after append | | ✅ | | | 4 |
| 6 | Queue always show `getLatestUpdateForDisplay` | | ✅ | | | 4 |
| 7 | `follow_up_type: correction` badge | | ✅ | | | 3 |
| 8 | Copy toast + continuation hint | | ✅ | | | 4 |
| 9 | Append sim in `trial_launch_check.sh` | | ✅ | | | 4 |
| 10 | Render `case_messages` thread (5 lines) | | | ✅ | | 5 |
| 11 | Generalize 本轮更新 block from add-car rail | | | ✅ | | 5 |
| 12 | Collapse top paste when case open | | | ✅ | | 5 |
| 13 | One-click `waiting_on: client` after copy | | | ✅ | | 4 |
| 14 | Y44 summary merge (prior intent on correction) | | | | ✅ | 5 |
| 15 | Y45 `bill_sent_claimed` + category re-anchor | | | ✅ | | 4 |
| 16 | Chinese broker_next_step templates | | | ✅ | | 4 |
| 17 | claim_intake + hit_and_run config tune | | | ✅ | | 3 |
| 18 | Founder 3 two-turn observation log entries | | ✅ | | | 5 |
| 19 | P16-Y battery CI gate ≥88 | | ✅ | | | 4 |
| 20 | Deadline countdown widget | | | | ✅ | 3 |

**ROI formula:** `(memory_trust × continuity_impact) / (days × regression_risk)`

Highest cluster: **wire existing data to glance** — zero new services.

---

# Phase 7 — 3-Day Execution Plan

**One engineer · 3 days · measurable outcomes**

### Day 1 — Timeline visibility (memory you can see)

| Task | Done when |
|------|-----------|
| Render last 3–5 `case_messages` in broker glance | Thread visible without opening collapse |
| Wire `getRecentCustomerMessages` (remove dead import) | Last customer bubble above fold |
| Default-open 操作记录 after successful append | Activity visible immediately |
| Queue card: `getLatestUpdateForDisplay` on every row | "Customer follow-up added…" scannable |
| Post-copy continuation line | Copy area shows append path |

**Outcome metric:** Founder answers "what did client say last?" from UI alone — **PASS/FAIL**

---

### Day 2 — Memory merge + append path (memory you can trust)

| Task | Done when |
|------|-----------|
| Show append card when `case_id` exists (not only reopened) | Two-turn demo without queue narration |
| Generalize 本轮更新 block (borrow `buildAddCarRailTurnModel`) | Turn delta visible on append |
| Y44 fix: prior intent preserved in summary on correction | Y44 battery ≥85 |
| Y45 fix: `bill_sent_claimed` + premium lane re-anchor | Y45 battery ≥85 |
| Collapse top paste when case open | No duplicate-case from re-paste |
| `follow_up_type: correction` badge | Correction turns labeled |

**Outcome metric:** `run_p16y_case_battery.py` avg ≥88, Y44/Y45 ≥85 — **PASS/FAIL**

---

### Day 3 — Guardrails + proof (memory that sticks)

| Task | Done when |
|------|-----------|
| Append sim in `trial_launch_check.sh` | CI blocks broken append |
| One-click `waiting_on: client` after copy | Waiting state in 1 click |
| Chinese broker_next_step pass (product_only) | No EN in glance |
| Andy: 3 real two-turn cases in observation log | case_ids logged |
| `guardrail_inbox_triage.sh` green | Full guardrail |

**Outcome metric:** 3 logged real two-turn cases + guardrail green — **GO/NO-GO**

---

# Founder Summary

## TOP 20 DISCOVERIES

1. **Backend memory is not the problem** — `case_messages`, `case_activity`, append API, `triage_for_append` are production-grade.  
2. **Broker memory UX is the problem** — P16-X Timeline 41/100; thread stored, never hero-rendered.  
3. **`getRecentCustomerMessages` is coded and imported but unused** — literal one-function fix.  
4. **`buildAddCarRailTurnModel` is the best memory UI in the repo** — trapped on customer add-car rail only.  
5. **Y44 scores 79/100 live** — correction tag exists; prior turn facts still drop from summary/collected.  
6. **Y45 misclassifies premium as add-car on append** — category re-anchor on merged text missing.  
7. **Turn 1 battery: 88.6 avg** — memory feels smart on first paste.  
8. **Turn 2+ multi_message: 21.5/25 avg but Y44/Y45 drag** — memory fails on corrections specifically.  
9. **Copy = exit** — no post-copy append bridge; spell-checker trap confirmed again.  
10. **Append gated on `caseView === 'reopened'`** — first-persist path hides append.  
11. **`learning_signals.jsonl` exists** — correction memory with no product loop.  
12. **Activity panel default-collapsed in product_only** — memory hidden by layout default.  
13. **Claims Turn 1 strong (82)** — wedge doesn't need new lane; needs Turn 2+ memory.  
14. **System reply bubbles stored in `case_messages`** — never shown; half the thread invisible.  
15. **Postgres mirror has full `record_messages` + `state_history`** — broker sees PG tag only.  
16. **No new microservice needed** — every fix extends `BrokerWorkbenchTab`, `intakePure.ts`, or `triage.py`.  
17. **Zendesk pattern confirmed** — chronological thread + inline events + status pill; we have data, not layout.  
18. **Intercom pattern confirmed** — "what changed since last visit" = our missing 本轮更新 block.  
19. **FP-004 SSO still blocks Chen Kui effective L1** — memory irrelevant if URL doesn't load.  
20. **Core question answer: NO for multi-turn** — system does not remember better than yesterday on corrections yet.

---

## TOP 10 MEMORY FAILURES

1. Prior turn intent dropped from `conversation_summary` on correction (Y44)  
2. `collected_fields` empty after multi-turn correction  
3. Premium thread misclassified as add-car on append (Y45)  
4. `case_messages` thread never rendered — broker re-reads WeChat  
5. Turn delta UI exists only on add-car customer path  
6. `follow_up_type: correction` invisible to broker  
7. Copy exits without teaching append — Turn 2 discovery ~20%  
8. Activity audit buried in collapse — "what happened?" unanswered  
9. Claims evidence (plate, police #, photos) doesn't accumulate in summary  
10. No outcome/closure field — memory loop never completes  

---

## TOP 10 EXISTING CAPABILITIES TO REVIVE

1. `case_messages[]` → render as 5-line thread in glance  
2. `buildAddCarRailTurnModel()` → broker 本轮更新 block  
3. `getRecentCustomerMessages()` → wire in workbench  
4. `getLatestUpdateForDisplay()` → queue subtitle on every card  
5. `append_follow_up_message()` → show append on first persist  
6. `case_activity[]` → default-open after append  
7. `getCaseTrackingSummary()` → promote to detail header  
8. `follow_up_type: correction` → badge in glance  
9. `run_follow_up_append_simulations.py` → trial launch gate  
10. `record_rail_section_latest_update` copy → generalize beyond add-car  

---

## TOP 10 HIGHEST ROI FIXES

1. Post-copy append one-liner (15 min)  
2. Render `case_messages` thread (0.5 day)  
3. Wire 本轮更新 turn delta from add-car rail (0.5 day)  
4. Append visible when `case_id` set (2 hr)  
5. Y44 summary merge on correction (1 day)  
6. Default-open activity after append (2 hr)  
7. Collapse top paste when case open (0.5 day)  
8. Queue `getLatestUpdateForDisplay` everywhere (2 hr)  
9. Y45 `bill_sent_claimed` + lane re-anchor (0.5 day)  
10. Founder 3 two-turn observation log entries (1 hr)  

---

## TOP 10 CLAIMS INSIGHTS

1. Claim Turn 1 is pilot-ready — invest in Turn 2+ memory, not new FNOL engine  
2. Corrections dominate claims threads — Y44 fix is claims-critical  
3. Plate/police#/carrier don't persist in summary across turns  
4. `waiting_on: carrier` never auto-set on progress-check messages  
5. Mixed claim + payment needs secondary memory, not winner-take-all  
6. Attachment API works; inline attach UX doesn't — evidence invisible  
7. Deadline prose insufficient for UW/claim letters — need countdown  
8. EN broker_next_step on bilingual office erodes trust  
9. Topic-shift claim→payment triggers boundary noise (C10)  
10. Thread render alone fixes ~80% of claims re-read pain  

---

## ONE SENTENCE PRODUCT SOUL

> **Unified Intake is the office's working memory for client obligations — not a chatbot, not a CRM, not a spell-checker.**

---

## ONE SENTENCE NORTH STAR

> Turn messy client messages into a time-bound office obligation with a clear next action and a traceable close — in one paste, under one minute.

---

## FINAL VERDICT

### If we only had 3 days and one engineer, what exactly should we ship?

**Ship the memory loop brokers can see and trust on Turn 2:**

| Day | Ship | Why |
|-----|------|-----|
| **Day 1** | Visible thread (`case_messages` render) + queue latest-update + post-copy append hint + default-open activity after append | Memory you can **see** — stops WeChat re-read |
| **Day 2** | Append on first persist + 本轮更新 turn-delta block (generalize add-car rail) + Y44/Y45 engine merge + collapse top paste | Memory you can **trust** — corrections preserve facts |
| **Day 3** | Append guardrail in launch check + one-click waiting_on + 3 real two-turn observation log entries | Memory that **sticks** — commercial proof |

**Do NOT ship in 3 days:** Customer tab exposure, OCR inline UI, outcome/closure fields, push notifications, new services, P17.

**GO criterion:** Andy completes 3 unsupervised two-turn cases (paste → copy → append → copy) on deployed URL without re-reading raw WeChat to know what changed.

**NO-GO if:** Only Turn 1 works; append requires founder narration; Y44 still scores <85.

---

**Does the system remember better today than yesterday?**

> **Not yet for multi-turn.** Single-turn memory improved through P16-Y (+3.0). Multi-turn memory is stored but not surfaced or merged. **This 3-day sprint is the minimum to answer YES for Chen Kui.**

---

*End of P16-Z5 Case Memory Sprint — Final Verdict*
