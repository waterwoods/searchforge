# Customer Entry — Founder Demo / Inspection Notes

**Sprint:** Customer Entry True Multi-Turn Repair + Guardrail Sprint

---

## 1. What to Inspect After Deployment

| Check | How |
|-------|-----|
| **First-turn quote/add-car** | Send "加车" or "想加一辆新车" — system should ask for year/model/zip, NOT immediately show handoff |
| **First-turn payment** | Send "付款失败了" — system should ask for notice/screenshot if not provided |
| **First-turn missing-doc** | Send "还缺什么材料" — system should ask for item/sent status |
| **Button starter** | Click "新车报价" with empty input — system should start flow and ask for next thing |
| **Talk to Agent** | Click "联系人工" or send "我要找人工" — system should hand off immediately (exception) |

---

## 2. Scenarios That Prove True Multi-Turn

| Scenario | User says/clicks | Expected |
|----------|------------------|----------|
| Add-car | "加车" | Reply asks for year, model, or zip. No handoff card. Input stays available. |
| Add-car turn 2 | "2024 Tesla Model Y, 94102" | Handoff. "报价资料已收集，办公室会尽快出价." |
| Payment | "付款失败了" | Reply asks for notice or screenshot. No immediate handoff. |
| Payment turn 2 | "截图发你了" | Handoff. |
| Button starter | Click "新车报价" | Reply: "好的，我来帮您看新车报价。先把年份和车型发我..." |

---

## 3. What Would Indicate the Bug Still Exists

- First message "加车" → immediate "办公室会尽快处理" / handoff card
- Input hidden or "done" state after first reply when more info is needed
- No second-turn flow possible (conversation ends after one exchange)

---

## 4. Quick Verification Commands

```bash
# Backend health
curl -s http://localhost:8001/health/ready | jq .

# Multi-turn simulation (handoff timing)
PYTHONPATH=. python3 scripts/run_multi_turn_simulations.py --verbose

# Guardrail
bash scripts/guardrail_inbox_triage.sh
```

---

*End of founder inspection notes*
