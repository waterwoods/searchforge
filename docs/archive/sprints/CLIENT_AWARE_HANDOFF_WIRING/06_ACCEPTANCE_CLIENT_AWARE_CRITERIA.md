# Acceptance / Client-Aware Criteria

---

## Practical Criteria

| Criterion | Pass | Fail |
|-----------|------|------|
| **client_id in triage path** | TriageRequest accepts client_id; triage_conversation receives it | Not passed |
| **Handoff phrases by client** | get_handoff_phrases(client_id) loads from configs/clients/{id}/ | Hardcoded path |
| **A/B API variation** | POST triage with client_id=demo_broker returns different client_reply_draft than chen_kui | Same draft for both |
| **Reduced hardcoding** | No "陈奎办公室" in fallback when client config loaded | "陈奎" in generic fallback |
| **Reuse story** | Founder can say "handoff and backend behavior change by client" | Only UI changes |
| **A→B migration** | New client = new folder + handoff_phrases.json | Code changes required |

---

## Acceptable to Defer

- client_id on persisted cases
- triage_for_append client-aware (use env default for now)
- add-car-rules API client-aware
- broker_next_step / client_prep client-specific

---

*End of Criteria*
