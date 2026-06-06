# Founder Inspection Notes

**Sprint:** Add-Car Identity + Contact Lite  
**Purpose:** What founder should inspect after this sprint; exact Vercel tests; "good enough for Chen Kui."

---

## 1. What to Inspect After Sprint

- **Contact block:** Open add-car case in Workbench; see Name/Phone or "needed"
- **Extraction:** Send "我是张三，电话 626-555-1234" in add-car flow; confirm name/phone in case
- **broker_next_step:** Quote-ready add-car without contact; broker_next_step mentions contact
- **Still needed:** Add-car with vehicle+zip but no name/phone; still_needed shows name, phone

---

## 2. Exact Vercel Tests (4–6)

1. **Add-car + name/phone in chat:** "我想加车" → "2024 Tesla Model Y 90210 下周提车 我是李四 电话 310-123-4567" — expect name, phone in case
2. **Add-car quote-ready, no contact:** "我想加车" → "2024 BMW X5 90210 下周提车" — expect Quote-ready, Contact needed, broker_next_step mentions contact
3. **Add-car name only:** "我想加车" → "2024 Honda Accord 90210 我姓王" — expect name in collected, phone in still_needed
4. **Workbench contact block:** Create add-car case, open in Workbench — expect Contact section with name/phone or "needed"
5. **Manual edit:** PATCH /api/inbox/cases/{id}/customer with name/phone — expect case shows updated values
6. **Simulations:** Run `PYTHONPATH=. python3 scripts/run_multi_turn_simulations.py` — expect pass

---

## 3. "Good Enough to Show Chen Kui"

- Add-car case has visible contact block
- Name/phone extracted when customer volunteers them
- Broker sees who to call and how
- Quote-ready + contact-needed are clear
- No heavy forms; chat-first flow preserved

---

*End of Founder Inspection Notes*
