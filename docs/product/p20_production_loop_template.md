# P20 Production Loop Template

**Governing SSOT:** `docs/product/p20_product_north_star.md`
**Use:** copy this worksheet into a P20 task, capability contract, or release
review. The governing SSOT controls if this template drifts.

## Reusable prompt header

```text
P20 NORTH STAR

We are optimizing the customer journey, not maximizing feature count.
Build the simplest reliable solution.
Smoothness first; complexity only when proven necessary.

ONE OBJECTIVE:
<one user-facing outcome>

OUT OF SCOPE:
<explicit exclusions>

SUCCESS GATE:
- reliable
- one clear next action
- no P0
- read-after-write consistency
- focused tests pass
- Founder QA prepared

STOP RULE:
Stop when PASS. Record future ideas; do not implement them.
```

## Controlled loop worksheet

- **Loop:** 1 / 2 / 3
- **One objective:**
- **Explicitly out of scope:**
- **Minimum change:**
- **Focused tests:**
- **Founder perspective:**
- **Broker perspective:**
- **Customer perspective:**
- **P0 / high-impact P1 findings:**
- **Future ideas recorded only:**
- **Commit authorized:** YES / NO
- **QA deploy authorized:** YES / NO
- **Founder/manual QA evidence:**

## Scorecard

- Reliability: PASS / CONDITIONAL / FAIL — evidence:
- Simplicity: PASS / CONDITIONAL / FAIL — evidence:
- Smoothness: PASS / CONDITIONAL / FAIL — evidence:
- Business Value: PASS / CONDITIONAL / FAIL — evidence:
- Scope Control: PASS / CONDITIONAL / FAIL — evidence:

Feature count, line count, and architectural cleverness are not success
metrics.

## Hard-gate check

- [ ] Customer/Broker read-after-write consistency
- [ ] One Task / One State / One Next Action
- [ ] One primary CTA per screen
- [ ] No visible engineering jargon
- [ ] No unsupported request type is sendable
- [ ] Idempotency: no duplicate command, event, or timeline entry
- [ ] Visible recovery; no silent fallback, no-op, or infinite loading
- [ ] Founder Form Gate (if any form changed) — see North Star §I
- [ ] Founder Entry and Navigation Gate — see North Star §J
- [ ] Founder/manual QA evidence recorded before Capability Done

Use the exact gate definitions in the governing SSOT; do not reinterpret them
from this abbreviated checklist.

### Founder Form Gate quick check (governing SSOT: North Star §I)

If a customer/broker form changed, confirm before Release:

- [ ] Visible value equals canonical form state
- [ ] Each required field tested independently
- [ ] All required complete → primary CTA enabled
- [ ] Optional / Request More / future fields never block submit
- [ ] No hidden length/format/legacy rule without Business Contract + visible reason
- [ ] Submit runs final validation and shows first invalid field
- [ ] Disabled CTA is never the only error signal
- [ ] Payload uses the normalized values shown to the user
- [ ] Duplicate tap → one command/outcome
- [ ] Accepted submit visible downstream
- [ ] DevTools full-compile + physical-device smoke done
- [ ] A real user can complete it without Cursor guidance

### Founder Entry and Navigation Gate quick check (governing SSOT: North Star §J)

- [ ] Every primary navigation destination renders non-blank content
- [ ] Home from success/result reaches usable Start Claim entry
- [ ] Restored sessions cannot strand users on stale result pages
- [ ] Start New Claim resets only claim-draft state
- [ ] Page shell renders before remote data completes
- [ ] Loading / error / empty states are visible and actionable
- [ ] Tested after fresh launch, submit, resume, Preview reopen
- [ ] Physical-device Preview smoke is a release blocker
- [ ] Blank screen at any point = FAIL

## Loop result

- **Verdict:** PASS / NEXT CONTROLLED LOOP / BLOCKED
- **Reason:**
- **Next action:**

Stop immediately on PASS. Never start the next capability automatically.
After three failed loops with an unresolved P0, record **BLOCKED**.
