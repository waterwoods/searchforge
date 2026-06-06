# P16-Z4 Phase 9 — 7-Day Execution Plan

**Date:** 2026-06-02  
**Sprint:** P16-Z4 Case Continuity Sprint  
**Constraint:** No P17 · No platform · No CRM · No Stripe · No WeChat integration · No new services  
**Goal:** Paste → Case → Timeline → Next Action → Append → Timeline → Next Action

**One engineer · 7 days**

---

## North Star for this sprint

Ship the **continuity loop** brokers can complete without training:

> 整理 → 复制发出 → 客户回复 → **同案追加** → 再复制 → **看得见变了什么**

---

## Day-by-day plan

### Day 1 — Access + copy bridge (unblock)

| Task | Owner | Done when |
|------|-------|-----------|
| FP-004 SSO off + redeploy Preview | Founder + Eng | Cold URL loads |
| Post-copy continuation line under 复制客户草稿 | Eng | Copy matches P16-X #1 |
| Copy toast with hint | Eng | Toast shows on copy |
| Auto-scroll to case detail after triage | Eng | Glance visible without hunt |

**Exit:** Andy completes Turn 1 on cold URL.

---

### Day 2 — Append discoverability

| Task | Owner | Done when |
|------|-------|-----------|
| Show append card when `currentCase.case_id` set (not only reopened) | Eng | Append visible after first persist |
| Collapse/hide 快速体验 when case open | Eng | P16-M #2 |
| Disable or tooltip 开始整理 when case open | Eng | P16-M #19 |
| `requires_new_case` friendly copy + 开新案 link | Eng | Clear blocked path |

**Exit:** Two-turn demo without Andy narrating queue.

---

### Day 3 — Timeline visibility

| Task | Owner | Done when |
|------|-------|-----------|
| Render last 3–5 `case_messages` in glance | Eng | Thread visible |
| Default-open 操作记录 after successful append | Eng | Activity visible |
| Queue row: `getLatestUpdateForDisplay` subtitle | Eng | "Customer follow-up added…" on card |
| Highlight `follow_up_added` on queue | Eng | Visual delta |

**Exit:** Assistant can answer "what changed?" from UI alone.

---

### Day 4 — Next action + waiting

| Task | Owner | Done when |
|------|-------|-----------|
| Chinese-only `broker_next_step` in product_only (config pass) | Eng | No EN in glance |
| Post-copy prompt: 保存「在等客户」one-click (PATCH follow-up) | Eng | waiting_on set in 1 click |
| Queue row Chinese 下一步 (60 char) | Eng | Monday scan works |
| Link 还缺 chips adjacent to broker_next_step | Eng | Single card scan |

**Exit:** Chen Kui knows what to do AND who we're waiting on.

---

### Day 5 — Engine: summary merge

| Task | Owner | Done when |
|------|-------|-----------|
| P16-Y P0: inject prior customer bubble into append summary | Eng | Y44 battery ≥ 85 |
| Run `run_p16y_case_battery.py` — no regression | Eng | Avg ≥ 88 |
| Optional: `bill_sent_claimed` rule for Y45 | Eng | Premium thread gap closed |
| claim_intake Chinese template tune | Eng | C1–C4 sim improved |

**Exit:** Multi-turn correction preserves facts in summary.

---

### Day 6 — Guardrails + founder proof

| Task | Owner | Done when |
|------|-------|-----------|
| Add append sim step to `trial_launch_check.sh` | Eng | CI blocks broken append |
| Andy: 3 real two-turn cases in observation log | Founder | Logged case_ids |
| Chen Kui supervised: 1 cancel + 1 claim two-turn | Founder | Witnessed append |
| `bash scripts/guardrail_inbox_triage.sh` green | Eng | Full guardrail |

**Exit:** Commercial evidence, not demo-only.

---

### Day 7 — Buffer + ship verdict

| Task | Owner | Done when |
|------|-------|-----------|
| Fix regressions from Days 1–6 | Eng | Guardrail green |
| Sticky copy (if time) P16-M #14 | Eng | Nice-to-have |
| Update `REALITY_VALIDATION_CHECKLIST.md` continuity section | Eng | Docs match ship |
| P16Z4 founder review | Founder | GO/NO-GO for unsupervised Week 2 |

**Exit:** GO if 3 two-turn real cases logged; NO-GO if only Turn 1.

---

## Must ship (non-negotiable)

1. Post-copy continuation + append on first persist  
2. Paste collapse when case open  
3. `case_messages` or activity visible after append  
4. Summary merge (Y44)  
5. FP-004 off  
6. One real two-turn observation log entry  

## Should ship

7. waiting_on one-click  
8. Chinese broker_next_step  
9. Append in trial_launch_check  

## Can wait (post 7-day)

- Customer tab on trial URL  
- OCR inline image UI  
- Outcome/closure fields  
- Push/email return triggers  

## Never (this sprint)

- P17 platform  
- New CaseIntelligenceService  
- CRM fields  
- Stripe billing UI  

---

## Success metrics

| Metric | Before | Target |
|--------|--------|--------|
| P16-X Cap 5 Lifecycle | 53 | **62+** |
| Append discoverability (founder rating) | Low | High without narration |
| Two-turn real cases logged | 0 | **≥ 3** |
| Y44 battery score | 67 | **≥ 85** |
| Chen Kui solo Turn 2 (est.) | 20% | **65%** |

---

## Files likely touched

| Area | Files |
|------|-------|
| UI | `BrokerWorkbenchTab.tsx`, `intakePure.ts`, `clientConfig.ts` |
| Engine | `triage.py` (`_build_conversation_summary`, append path) |
| Config | Category templates, `claim_intake` |
| Scripts | `trial_launch_check.sh`, observation log |
| Docs | `REALITY_VALIDATION_CHECKLIST.md` |

---

*End of P16-Z4 Phase 9*
