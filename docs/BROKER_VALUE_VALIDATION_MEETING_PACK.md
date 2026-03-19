# Broker Value-Validation Meeting Pack

**Primary runbook** for the California Auto Insurance Broker Assistant value-validation session (e.g., 陈魁). Single entry point: agenda, scripts, success criteria, next-step logic.

---

## 1. Pre-Meeting (5 min before)

1. Run `bash scripts/demo_pre_checklist.sh`
2. Check result: "Use Live path" or "Use Offline path"
3. Run `bash scripts/run_demo_local.sh` if not already running
4. Open http://localhost:5173/demo
5. See `docs/ANDY_2MIN_BEFORE_DEMO.md` for the 2-min checklist

---

## 2. Agenda & Question Order

| # | Question | Time | Broker use |
|---|----------|------|------------|
| 1 | 我刚买了辆新车（加州），最低需要买哪些保险？大概怎么配比较合理？ | 3 min | 新车投保：权威答复 + 官方链接 |
| 2 | 我的车注册被暂停了（可能是保险问题），我该怎么恢复？需要交多少钱/提交什么材料？ | 3 min | 注册恢复：DMV 流程 + 材料 |
| 3 | 客户问我：怎么查保险公司/经纪人是不是合规？加州官方在哪里能查到？ | 3 min | 合规查询：insurance.ca.gov |
| 4 | 客户想省钱：哪些因素会影响保费？有哪些常见折扣/优惠？ | 2 min | 续保挽留：省钱与折扣 |
| 5 | 出险后理赔流程是怎样的？ | 2 min | 理赔指导：步骤与材料 |

**All 5 work in Live and Offline.** In Offline, click only — do not type custom questions.

**Optional long-tail** (if time): SR-22, why suspended, collision/comprehensive — see `docs/BROKER_LONGTAIL_MEETING_SUBSET.md`.

---

## 3. Opening Script (1 min)

**Say:** "This is a California auto insurance assistant for brokers. It helps you answer common client questions quickly, using official sources — DMV, California Department of Insurance, and insurer sites. You can copy the answer and links directly to WeChat. Questions in Chinese or English both work."

**Do:** Open http://localhost:5173/demo. Point to: 加州汽车保险经纪助手 · 帮经纪快速回答客户问题，附官方 / 权威来源链接，可直接发微信.

---

## 4. Fallback Transition (if Live fails)

**Say:** "Let me switch to our offline demo mode. We keep pre-saved answers for the most common questions so the demo can run even when the live system is unavailable."

**Do:** Refresh the page → Wait for orange banner → Click the 5 recommended questions in order → Continue from Q1.

See `docs/BROKER_DEMO_FALLBACK_SCRIPT.md` for full fallback steps.

---

## 5. Closing & Feedback Questions (1 min)

**Say:** "The system is designed to reduce your lookup time and give you authoritative answers you can share with clients. We're iterating based on broker feedback."

**Ask:**
1. "Compared to how you usually answer these questions, does this tool save you time?"
2. "Could you copy the answer and send it to a client with minimal editing?"
3. "Would you use this in your real day-to-day work?"
4. "What would make this most useful for your work?"
5. "What customer questions do you get most often that this tool doesn't cover?"

**Post-demo:** Send follow-up via `docs/BROKER_FOLLOWUP_MESSAGE.md`. Use `docs/broker_value_feedback_form.md` to record results.

---

## 6. Success Criteria

| Criterion | Pass | Fail |
|-----------|------|------|
| **Saves time** | 明显节省 or 有一点节省 | 差不多 or 更慢 |
| **Usable answer** | 可以直接发 or 需要小改 | 需要大改 or 不能用 |
| **Would use again** | 会经常用 or 偶尔会用 | 可能不会用 or 肯定不会用 |

---

## 7. Next-Step Decision Logic

| Outcome | Condition | Action |
|---------|-----------|--------|
| **Value confirmed** | All 3 criteria pass | Propose pilot; send follow-up |
| **Value partial** | 2 of 3 pass | Address gaps; schedule second session |
| **Value weak** | 1 or 0 pass | Document gaps; no pilot push |

---

## Reference

| Doc | Purpose |
|-----|---------|
| `docs/ANDY_QUICK_START.md` | How to run demo, ports, recovery |
| `docs/ANDY_2MIN_BEFORE_DEMO.md` | 2-min pre-demo checklist |
| `docs/BROKER_DEMO_OPERATOR_RUNBOOK.md` | Quick reference for running the demo |
| `docs/BROKER_DEMO_SCRIPT_15MIN.md` | Full demo script with timing |
| `docs/BROKER_DEMO_FALLBACK_SCRIPT.md` | Offline mode steps |
| `docs/broker_value_feedback_form.md` | Feedback capture form |
| `docs/BROKER_FOLLOWUP_MESSAGE.md` | Post-demo message template |
