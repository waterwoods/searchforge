> **HISTORICAL / ARCHIVE — P9 Broker Surface Collapse (2026-05-30)**
> **Read instead:** [`docs/BROKER_ONE_PAGER.md`](../../../BROKER_ONE_PAGER.md), [`docs/BROKER_DEMO_FLOW.md`](../../../BROKER_DEMO_FLOW.md), [`docs/BROKER_TRIAL_PLAYBOOK.md`](../../../BROKER_TRIAL_PLAYBOOK.md)

# Broker Demo Checklist (One Page)

**→ Primary runbook:** `docs/runbooks/BROKER_VALUE_VALIDATION_MEETING_PACK.md` — use for full agenda, scripts, success criteria. This checklist is a one-page summary.

**Runtime path:** Default = 8001. Recovery = `bash scripts/restore_8001_readiness.sh`. See `docs/runbooks/RUNTIME_PATH_STANDARD.md`.

## Pre-Demo (5 min before)

- [ ] Run `bash scripts/demo_pre_checklist.sh`
- [ ] Check `results/demo_pre_checklist/<latest>/CHECKLIST.md`
- [ ] Qdrant env set? Offline pack ready? Backend running?
- [ ] Run `bash scripts/run_demo_local.sh`
- [ ] Open http://localhost:5173/demo
- [ ] Note mode: **Live** (green) or **Offline** (orange)

## Demo Start

- [ ] Status bar shows Live or Offline
- [ ] If Offline: orange banner visible, use only the 5 recommended questions (click, don't type)
- [ ] If Live: can use any question

## 5 Questions (in order)

1. 我刚买了辆新车（加州），最低需要买哪些保险？大概怎么配比较合理？
2. 我的车注册被暂停了（可能是保险问题），我该怎么恢复？需要交多少钱/提交什么材料？
3. 客户问我：怎么查保险公司/经纪人是不是合规？加州官方在哪里能查到？
4. 客户想省钱：哪些因素会影响保费？有哪些常见折扣/优惠？
5. 出险后理赔流程是怎样的？

*(All 5 work in Live and Offline. In Offline, click only — do not type custom questions.)*

## During Demo

- [ ] Show "复制给客户" button
- [ ] Show 建议结论 + 下一步怎么做
- [ ] Show 权威依据 (citations)
- [ ] Avoid: custom typed questions in Offline mode

## If Live Fails

- [ ] **503 embedding_warming:** `bash scripts/restore_8001_readiness.sh`
- [ ] Say: "Let me switch to offline demo mode"
- [ ] Refresh page (F5)
- [ ] Click 5 recommended questions in order
- [ ] Continue script

## Post-Demo

- [ ] Ask: "What would make this most useful for your work?"
- [ ] Send follow-up (see `docs/BROKER_FOLLOWUP_MESSAGE.md`)
