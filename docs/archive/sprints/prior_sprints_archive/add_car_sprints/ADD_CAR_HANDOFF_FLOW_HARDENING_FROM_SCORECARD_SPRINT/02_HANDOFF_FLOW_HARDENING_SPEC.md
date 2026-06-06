# Handoff + flow hardening spec (scorecard-driven)

## Weakest gaps (from scorecard + final report)

### HANDOFF (~3/5)

- **Tone / length:** Draft acknowledgements and some stitched lines could feel **procedural or repetitive** (e.g. stacked “收到 / 好的”).
- **Already-sent / materials-sent:** Strong logic exists; copy could better signal **office verification** and **no need to resend everything** without sounding like a bot checklist.
- **Same-case append:** Continuity strings were correct but could more explicitly anchor **“this add-car record”** for trust.

### FLOW (~3/5)

- **Chat-shaped center of gravity:** Labels help, but **post-submit** copy could state more clearly that the **task has moved to the office queue** (customer vs office division of labor).
- **Step track:** Step names could read more like **intake milestones** than generic progress.

## Target HANDOFF qualities

- **Received:** First clause acknowledges **materials or request is in** (not a long echo).
- **Office-real:** **核对 / 出价 / 联系** owned by the office; customer role is **wait + correct if needed**.
- **Short:** Fewer stacked pleasantries; one clear promise of **follow-up**.
- **Already-sent natural:** “We’ll verify what’s on file; don’t resend the bundle unless we ask.”

## Target FLOW qualities

- After submit: obvious **handoff** (“转交办公室 / office queue”), not “another chat reply.”
- Flow track: **开始报送 → 收齐要点 → 转交办公室** reads as **one task** with three gates.

## This sprint will not

- Redesign the thread UI, add new states, or fix workbench parity (separate STATE sprint).
- Guarantee LLM path parity with rules.

## Acceptance criteria

- [ ] Chen Kui **add-car handoff** phrase remains **office-branded** and **handoff_ready** behavior unchanged.
- [ ] **Materials-sent** and **clarification follow-up** stitched lines are **shorter** and **less repetitive**.
- [ ] **Append** continuity for add-car references **ongoing office follow-up** on **this** add-car line.
- [ ] **Portal** default copy for closure processing + flow steps reinforces **task + office ownership** without new UI components.
- [ ] `bash scripts/guardrail_inbox_triage.sh` passes (or any failure is documented as pre-existing).
