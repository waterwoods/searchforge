# P16-Z24 Before / After Comparison

| Metric | Before | After | Delta |
|--------|--------|-------|-------|
| Average case quality | 96.6 | 96.6 | +0.0 |
| Route accuracy | 100.0% | 100.0% | +0.0% |
| Need WeChat % | 0.0% | 0.0% | +0.0% |
| Broker confidence | 100.0 | 100.0 | +0.0 |
| Minutes saved/case | 6.2 | 6.2 | +0.0 |

## Cases with largest quality lift

Aggregate score unchanged (96.6) — improvements are **first-turn routing** and **Chinese broker readability**, not final-slot extraction.

| Case | Before | After | Change |
|------|--------|-------|--------|
| AC07 turn 1 | `general_inquiry` | `add_car` + vehicle extracted | First-turn routing fixed |
| AC20 broker step | English materials verify | 联系客户补齐车架号、提车日期、主驾驶人 | Chinese office step |
| AC11/AC12 broker step | Generic English | 联系客户补齐年份、车型、车架号、邮编 | Chen Kui-readable |
| AC05 handoff | English Run quote… | 联系客户补齐姓名、电话，然后出报价 | Chinese office step |

## Cases with largest quality lift (score)

- **AC01:** 97 → 97 (+0)
- **AC02:** 97 → 97 (+0)
- **AC03:** 100 → 100 (+0)
- **AC04:** 95 → 95 (+0)
- **AC05:** 100 → 100 (+0)