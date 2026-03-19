# Human Front Door + Talk-to-Agent — Founder Demo / Inspection Notes

**Sprint:** Human Front Door + Talk-to-Agent Sprint  
**Created:** 2026-03-15

---

## 1. What the Founder Should Inspect After Deployment

| Area | Inspect | Pass/Fail |
|------|---------|-----------|
| Welcome | "今天有什么可以帮您？" + reassurance line | |
| Buttons | 6 buttons including "联系人工" | |
| Examples | "不确定说什么？点这里看示例" or clearer | |
| Talk-to-Agent | Click "联系人工" → immediate handoff | |
| Case Summary | Humanized labels (年份, 车型, 邮编) | |
| Handoff card | "办公室会尽快处理，有结果会联系您" | |
| Header | No "Unified Intake" in customer view if possible | |

---

## 2. Scenarios That Best Show the Improved Front Door

| # | Scenario | What to Check |
|---|----------|---------------|
| 1 | Land on page, read welcome | Feels welcoming, not prototype-like |
| 2 | Click "联系人工" | Immediate handoff, no form |
| 3 | Click "报价", type "2024 BMW X5" | Progressive ask, human tone |
| 4 | Reach handoff | "办公室会尽快处理" visible |
| 5 | Check Case Summary during intake | "年份、车型" not "year, make_model" |

---

## 3. Customer Feelings to Check

| Feeling | How to Verify |
|---------|---------------|
| Understood | System acknowledges before asking |
| Reassured | "办公室会尽快处理" / "我们会尽快帮您" |
| Not trapped | "联系人工" visible and works |
| Connected to office | Handoff says "转给办公室" / "办公室会跟进" |

---

## 4. Production URL

- **Vercel:** Check alias (e.g. ui-smoky-beta.vercel.app or main)
- **Path:** /workbench/unified-intake
- **Tab:** Customer Entry (default)

---

## 5. Quick Checklist

- [ ] Welcome card has reassurance line
- [ ] 6 buttons, "联系人工" visible
- [ ] Click "联系人工" → handoff in one step
- [ ] Case Summary shows humanized labels
- [ ] Handoff card says "办公室会尽快处理"
- [ ] Examples more prominent
- [ ] No "Unified Intake" or internal jargon in customer view

---

*See also: Product Blueprint, UX Design Spec*

---

## Sprint Report Summary (2026-03-15)

**Redeploy:** Success. https://ui-smoky-beta.vercel.app. Alias updated.

**Founder block:** Biggest improvement = 6th button "联系人工" + immediate handoff; welcome says "您的消息会直接转给办公室"; Case Summary "年份、车型、邮编". Biggest weakness = URL and "Unified Intake" header. Talk to Agent clear? Yes. Inspect: /workbench/unified-intake → Customer Entry.
