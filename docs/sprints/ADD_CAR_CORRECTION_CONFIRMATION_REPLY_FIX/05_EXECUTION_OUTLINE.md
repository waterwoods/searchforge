# Execution Outline

1. **Audit** — Trace add-car client draft: `_build_client_reply_draft` → `_get_add_car_acknowledgement` → `_extract_add_car_vehicle_concrete`; trace multi-turn `triage_conversation` → `_get_next_ask_for_add_car`.
2. **Root cause** — Merged vs last-bubble confusion + overly strict correction regex + zh spacing + thin year-only ack.
3. **Implement** — Helper for merged/last; defensive last-bubble parse; broader correction patterns gated on vehicle tokens; concrete-before-year; rules + fallbacks copy.
4. **Scenarios** — Add ACE17, ACE18; keep ACE13–16.
5. **Validate** — Guardrail + multi-turn + ACE runner (all green).
6. **Report** — Founder-facing before/after, deploy note, 中文三问.

**Budget:** ~30–45 minutes focused loop (audit → implement → simulate → retest → summarize).
