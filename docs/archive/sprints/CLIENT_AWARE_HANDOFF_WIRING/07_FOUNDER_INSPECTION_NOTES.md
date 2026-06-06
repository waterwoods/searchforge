# Founder Inspection Notes

---

## What Founder Should Inspect After This Sprint

1. **API-level A/B variation**
   - `curl -X POST http://localhost:8001/api/inbox/triage -H "Content-Type: application/json" -d '{"text":"我想联系客服","soft_route":"talk_to_agent","client_id":"demo_broker"}'`
   - Check `client_reply_draft` contains "客服团队"
   - Same with `client_id":"chen_kui" → "办公室" or "陈奎办公室"

2. **UI with client param**
   - `/workbench/unified-intake?client=demo_broker` → paste "我想联系客服" → draft should say "客服团队"
   - `/workbench/unified-intake?client=chen_kui` (or no param) → draft should say "办公室"

3. **Add-car handoff**
   - Add-car with enough info: demo_broker → "客服团队会尽快出价"; chen_kui → "办公室会尽快出价"

---

## What Should Now Look More Reusable

- Handoff wording is driven by client config
- No code change to add a new client's handoff phrases
- Same triage logic, different client config

---

## How Founder Should Explain A→B Migration More Confidently

> "The UI changes by client—we already had that. Now the handoff and backend-facing product behavior also change by client. When you add a new broker, you add a folder with handoff_phrases.json. The triage engine loads it. No code change."

---

*End of Notes*
