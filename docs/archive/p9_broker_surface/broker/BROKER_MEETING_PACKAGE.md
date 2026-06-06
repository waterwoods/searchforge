> **HISTORICAL / ARCHIVE — P9 Broker Surface Collapse (2026-05-30)**
> **Read instead:** [`docs/BROKER_ONE_PAGER.md`](../../../BROKER_ONE_PAGER.md), [`docs/BROKER_DEMO_FLOW.md`](../../../BROKER_DEMO_FLOW.md), [`docs/BROKER_TRIAL_PLAYBOOK.md`](../../../BROKER_TRIAL_PLAYBOOK.md)

# Broker Meeting Package — 15-Min Demo

Consolidated package for the California Auto Insurance Broker Assistant demo.

**→ Primary runbook:** `docs/runbooks/BROKER_VALUE_VALIDATION_MEETING_PACK.md` — use this for the 陈魁 value-validation session.

## Opening (1 min)

**Say:** "This is a California auto insurance assistant for brokers. It helps you answer common client questions quickly, using official sources — DMV, California Department of Insurance, and insurer sites. You can copy the answer and links directly to WeChat. Questions in Chinese or English both work."

**Do:** Open http://localhost:5173/demo. Point to: 加州汽车保险经纪助手 · 帮经纪快速回答客户问题，附官方 / 权威来源链接，可直接发微信.

---

## Demo Sequence (12 min)

| # | Question | Time | Broker use |
|---|----------|------|------------|
| 1 | 我刚买了辆新车（加州），最低需要买哪些保险？大概怎么配比较合理？ | 3 min | 新车投保：权威答复 + 官方链接 |
| 2 | 我的车注册被暂停了（可能是保险问题），我该怎么恢复？需要交多少钱/提交什么材料？ | 3 min | 注册恢复：DMV 流程 + 材料 |
| 3 | 客户问我：怎么查保险公司/经纪人是不是合规？加州官方在哪里能查到？ | 3 min | 合规查询：insurance.ca.gov |
| 4 | 客户想省钱：哪些因素会影响保费？有哪些常见折扣/优惠？ | 2 min | 续保挽留：省钱与折扣 |
| 5 | 出险后理赔流程是怎样的？ | 2 min | 理赔指导：步骤与材料 |

**For each:** Click the question → Show 建议结论, 下一步怎么做, 权威依据 → Demo 复制给客户.

---

## Fallback Transition (if Live fails)

**Say:** "Let me switch to our offline demo mode. We keep pre-saved answers for the most common questions so the demo can run even when the live system is unavailable."

**Do:** Refresh the page → Wait for orange banner → Click the 5 recommended questions in order → Continue from Q1.

---

## Closing (1 min)

**Say:** "The system is designed to reduce your lookup time and give you authoritative answers you can share with clients. We're iterating based on broker feedback."

**Ask:** "What would make this most useful for your day-to-day work? Any questions or scenarios we should add?"

---

## Post-Demo Follow-Up

Use the template in `docs/BROKER_FOLLOWUP_MESSAGE.md`.

---

## Success Criteria & Next Steps

See `docs/runbooks/BROKER_VALUE_VALIDATION_MEETING_PACK.md` §6–7 for:
- Success criteria (saves time / usable / would use)
- Next-step decision logic (value confirmed / partial / weak)

---

## Reference

- **Demo script (full):** `docs/BROKER_DEMO_SCRIPT_15MIN.md`
- **Fallback script:** `docs/BROKER_DEMO_FALLBACK_SCRIPT.md`
- **Quick start:** `docs/ANDY_QUICK_START.md`
- **2-min checklist:** `docs/ANDY_2MIN_BEFORE_DEMO.md`
- **Troubleshooting:** `docs/ANDY_IF_SOMETHING_GOES_WRONG.md`
