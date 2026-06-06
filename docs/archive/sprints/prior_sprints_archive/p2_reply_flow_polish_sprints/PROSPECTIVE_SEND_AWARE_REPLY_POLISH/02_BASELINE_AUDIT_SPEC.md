# Baseline Audit Spec

## Files to inspect (minimum)

- `services/fiqa_api/inbox_triage/triage.py`

## Questions the audit must answer

1. **Where is prospective-send detected?**  
   - `_is_prospective_send_offer_message()` and `_derive_follow_up_type()` (returns `new_info`, not `already_sent`).

2. **Where are Add-Car customer replies built?**  
   - Turn 1 / rule template: `_build_client_reply_draft()` → add-car branch + `_get_add_car_acknowledgement()`.  
   - Turn 2+ collecting: `_get_next_ask_draft()` → `_get_next_ask_for_add_car()`.  
   - Handoff: `triage_conversation()` builds `handoff_reply` and optional overlays.

3. **Why did replies feel generic?**  
   - No dedicated “yes, you can send …” line; only the next-slot ask or handoff boilerplate.  
   - Short messages could be **echoed** by `_get_add_car_acknowledgement()` (“好的，要不要发你。”), which sounds unnatural.

4. **Safest fix location**  
   - Add `_get_prospective_send_materials_lead()` and prepend when the last customer bubble matches prospective-send.  
   - Stop echoing prospective questions in `_get_add_car_acknowledgement()`.

5. **Broker behavior**  
   - Already gated on `follow_up_type == "already_sent"` for verify-materials `broker_next_step`; prospective-send stays `new_info` — no change required there.

## Secondary bug (audit finding)

- `_get_next_ask_for_add_car()` used substring `发你` for “materials sent”; **“要不要发你”** contains `发你`, which could mis-trigger the “materials sent → hand off” branch. Exclude prospective-send from that substring path.
