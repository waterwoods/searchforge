# Founder Inspection Notes

## What to read in the UI / API response

- `client_reply_draft`: first sentence should **answer** the “要不要发你” style question; remainder should match the usual Add-Car flow (ask next slot or handoff).
- `follow_up_type`: should stay `new_info` for permission-to-send questions; `already_sent` only when the customer states materials were sent.

## Quick API check (local)

With backend on 8001, run `python3 scripts/test_inbox_triage_api.py` after deploy, or hit triage with multi-turn payloads mirroring the three founder cases below.

## Red flags

- Reply starts with “您说材料发过了” when the customer only **asked** whether to send.  
- Reply echoes “好的，要不要发你。” with no real answer.  
- Broker step switches to “Verify materials received” when the customer did not claim send.
