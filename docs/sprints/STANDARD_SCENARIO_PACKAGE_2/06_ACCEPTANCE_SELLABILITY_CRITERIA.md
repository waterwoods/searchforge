# Acceptance / Sellability Criteria — Package 2.0

**Sprint:** Standard Scenario Package 2.0

---

## 1. Package Coherence

- [ ] All 5 chosen scenarios follow the same detect → ask → enough? → hand off skeleton
- [ ] Handoff phrases consistent (add_car, remove_car, other_received, other_corrected)
- [ ] Summary format consistent across scenarios

---

## 2. Scenario Strength

- [ ] Add-car: Summary shows "Collected: year, model, zip" when present
- [ ] Missing document: Summary shows "Client says sent" when applicable; broker_next_step mentions verify
- [ ] Renewal: Summary shows "policy/bill sent" when client sends
- [ ] Payment: Summary shows "client says sent/screenshot" when applicable; broker_next_step mentions verify
- [ ] Talk to Agent: Draft contains 陈奎 or 联系 or 办公室

---

## 3. Later-Turn Realism

- [ ] Clarification question → answer first, then hand off
- [ ] Already sent → warmer handoff ("好的，收到了")
- [ ] Correction → other_corrected handoff
- [ ] No generic "please provide more context" for clear intent

---

## 4. Handoff Usefulness

- [ ] broker_next_step is one operational sentence
- [ ] When "client says sent", broker_next_step includes verify/confirm
- [ ] collected_fields and still_needed_fields accurate for workbench chips

---

## 5. Office Usability

- [ ] Broker can infer "what to do next" from broker_next_step
- [ ] Broker can infer "what was collected" from collected_fields
- [ ] Broker can infer "what to verify" when client says sent/paid

---

## 6. Reduced Broker Follow-Up

- [ ] After handoff, broker would likely ask fewer manual follow-up questions than before
- [ ] Summary + broker_next_step + chips give enough context

---

## 7. Acceptable to Defer

- Remove-car (already strong)
- Claim first notice (lower frequency)
- Billing clarification as standalone
- New platform features

---

*End of Acceptance / Sellability Criteria*
