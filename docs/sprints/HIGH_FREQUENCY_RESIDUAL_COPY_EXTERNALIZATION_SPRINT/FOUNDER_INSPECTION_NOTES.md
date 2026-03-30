# Founder Inspection Notes

## What to spot-check in the demo UI or CLI

1. **Add-car + price anxiety** (中文): Ask for a ballpark premium mid–quote collection.  
   - Chen Kui: should still sound like **办公室核算**.  
   - SoCal: should say **本所** / formal desk language, not the Chen caveat sentence.

2. **Premium / payment + “我发过了”**: Message that mentions **驾照/材料** and **发过了**.  
   - SoCal: closing tail should reference **本所核对**, not **我这边帮你核对**.

3. **Add driver / bundling** (中文): Short questions.  
   - SoCal: should match the **事务所** tone from `reply_overrides.json`.

4. **Flagship add-car**: Full slots in one message → **handoff**.  
   - Confirm timing copy still matches each client pack (unchanged from prior sprints).

## What not to worry about in this sprint

- Broker-only fields (`broker_next_step` English) and marker tuning.
- LLM-generated drafts when `LLM_GENERATION_ENABLED=1` (this sprint validates **rule path**).

## Red flags

- SoCal draft containing **办公室按车型** or **our office will run the numbers** on the add-car price caveat path.
- Add-car handoff regressions (no handoff when quote-ready, or wrong category).
