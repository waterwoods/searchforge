# Human-First Entry Flow — Acceptance / SLA Criteria

**Sprint**: Human-First Entry Flow + Startup Latency Audit  
**Created**: 2026-03-15

---

## 1. What Counts as "Answered the Real Ask"

| Criterion | Pass | Fail |
|-----------|------|------|
| User says "我才买了一个2026年的丰田花冠，我想问一下，大约半年的保费是多少？" | System says it understands quote request and asks for zip (or next missing field) | System says "内容不够完整" or generic "请提供更多信息" |
| User says "刚出事故了" | System acknowledges accident, asks for photos/other driver info | Generic fallback |
| User says "付款失败了" | System acknowledges payment issue, asks for notice/screenshot | Generic fallback |

---

## 2. What Counts as "Only Asks Next Missing Information"

| Criterion | Pass | Fail |
|-----------|------|------|
| Add-car with year+model | Asks for zip (or delivery/driver) only | Asks for 5+ fields at once |
| Add-car with year only | Asks for model and zip | Asks for everything |
| Payment with notice | Acknowledges, asks for payment proof if needed | Repeats same ask |

---

## 3. What Counts as "Button Is a Real Starter"

| Criterion | Pass | Fail |
|-----------|------|------|
| Click "获取报价" with empty input | System immediately returns first quote reply | User must type; nothing happens |
| Click "报事故" with empty input | System immediately returns first claim reply | User must type |
| Click any button | Conversation starts; user sees first system message | Button only sets tag; no reply |

---

## 4. What Counts as "Live Summary Is Useful"

| Criterion | Pass | Fail |
|-----------|------|------|
| During intake | Summary card shows intent, collected, still needed | No summary; or summary empty |
| After each turn | Summary updates with new fields | Summary static or wrong |
| Office-side | conversation_summary reflects same structure | Inconsistent |

---

## 5. What Counts as "Latency Still Too Slow"

| Criterion | Pass | Fail |
|-----------|------|------|
| First click to first reply | < 3 s perceived (warm) | > 5 s perceived |
| Cold start | Documented; cause identified | Unknown; no diagnosis |
| Recommendation | Clear next optimization direction | No recommendation |

---

## 6. Anti-Patterns to Avoid

- Generic "信息不完整" when intent is clear
- Asking 5 fields at once
- Button click does nothing until user types
- No visible structure during intake
- Bluffing when uncertain

---

*See also: Product Blueprint, UX Spec, Execution Outline*
