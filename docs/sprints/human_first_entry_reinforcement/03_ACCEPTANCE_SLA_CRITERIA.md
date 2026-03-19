# Human-First Entry Flow Reinforcement — Acceptance / SLA Criteria

**Sprint**: Human-First Entry Flow Reinforcement + Redeploy  
**Created**: 2026-03-15

---

## 1. Answer-First Quality

| Criterion | Pass | Fail |
|-----------|------|------|
| "我才买了一个2026年的丰田花冠，我想问一下，大约半年的保费是多少？" | System acknowledges quote request, asks for zip (or next missing field) | "内容不够完整" or generic "请提供更多信息" |
| "这个英文 notice 说 payment failed，我现在怎么办？" | Acknowledges payment issue, asks for notice/screenshot | Generic fallback |
| "我上周已经发过了，怎么还在追材料？" | Acknowledges "发过了", offers to verify | Generic "请提供更多信息" |
| "刚撞了，对方跑了，我现在先干嘛？" | Acknowledges accident + hit-and-run, asks for plate/photos | Generic fallback |

---

## 2. Next-Missing-Info Quality

| Criterion | Pass | Fail |
|-----------|------|------|
| Add-car with year+model | Asks for zip (or delivery/driver) only | Asks for 5+ fields at once |
| Add-car with year only | Asks for model and zip | Asks for everything |
| Payment with notice | Acknowledges, asks for payment proof if needed | Repeats same ask |

---

## 3. Button Starter Usefulness

| Criterion | Pass | Fail |
|-----------|------|------|
| Click "获取报价" with empty input | System immediately returns first quote reply | User must type; nothing happens |
| Click "报事故" with empty input | System immediately returns first claim reply | User must type |
| Click any button | Conversation starts; user sees first system message | Button only sets tag; no reply |

---

## 4. Live Case Summary Usefulness

| Criterion | Pass | Fail |
|-----------|------|------|
| During intake | Summary card shows intent, collected, still needed | No summary; or summary empty |
| After each turn | Summary updates with new fields | Summary static or wrong |
| Visibility | Clearly labeled (主题 / 已收集 / 还需) | Unclear or hidden |

---

## 5. Acceptable Startup Responsiveness

| Criterion | Pass | Fail |
|-----------|------|------|
| First click to first reply | < 5 s perceived (warm) | > 8 s perceived |
| Cold start | Documented; cause identified | Unknown; no diagnosis |
| Recommendation | Clear next optimization direction | No recommendation |

---

## 6. What Counts as Still Too Generic or Too Slow

- Generic "信息不完整" / "内容不够完整" when intent is clear
- Asking 5 fields at once
- Button click does nothing until user types
- No visible structure during intake
- First reply > 8 s perceived (warm path)

---

*See also: Product Blueprint, Execution Outline, Reinforcement Checklist*
