# Founder Inspection Notes

## What to spot-check in the UI or API

1. **Single bubble:** `VIN 我可以先发你截图吗`  
   - Draft should **invite** sending the screenshot (可以…先发我), **not** “您是说发过了吗？”.

2. **Single bubble:** `截图要不要先发你`  
   - May still be categorized **unclear** if there is no add-car anchor — that is acceptable **if** the draft does **not** assert they already sent.

3. **Quote-ready + permission:** `加车，2024 Nissan Altima，95123，下周提车。VIN 我可以先发你截图吗`  
   - Expect **permission lead** + **driver ask** (not a giant full-slot paragraph).

4. **True send:** `…材料发你微信了`  
   - Expect **office verify / quote** tone (`您说材料发过了…` or equivalent handoff).

## Broker trust lens

- **Worst failure mode:** sounding like the client already sent something when they only asked permission.  
- **This sprint removes the main mechanical cause** (loose markers + substring 发你).

## API smoke

```bash
curl -s -X POST http://localhost:8001/api/inbox/triage \
  -H 'Content-Type: application/json' \
  -d '{"text":"VIN 我可以先发你截图吗"}' | jq '.client_reply_draft, .issue_category'
```

Restart backend after pulling code so `triage.py` is loaded.
