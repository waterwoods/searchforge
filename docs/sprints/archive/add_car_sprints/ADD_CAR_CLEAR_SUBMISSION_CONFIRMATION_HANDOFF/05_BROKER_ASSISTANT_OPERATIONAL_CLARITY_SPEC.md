# Broker / Assistant Operational Clarity Spec

## Assistant (draft) behavior

- `client_reply_draft` at Add-Car handoff remains **short** (per triage style rules).
- Sprint tightens **handoff_phrases.add_car** so the draft explicitly signals **formal submission to the office**, not casual acknowledgment.

## Broker workbench

- No change required to case list semantics; structured fields already power broker scan.
- Customer-side confirmation **reduces** “did you get my VIN?” re-messages by showing **field-level** receipt tags.

## Boundaries

- **Same case append** remains the lane for corrections; copy continues to steer away from mixing unrelated issues.
- **New issue** flow unchanged; sprint does not weaken boundary messaging.

## Trust chain

Customer sees tags → broker sees same fields in case → office acts. **One request = one case thread** is preserved.
