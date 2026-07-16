# P20 Product North Star

**Status:** governing P20 product-development standard
**Authority:** product principles, evaluation scorecard, Production Loop, and release gates for every P20 capability and release
**Applies to:** design, implementation, review, QA, and release work  
**Operational worksheet:** `docs/product/p20_production_loop_template.md`

## North Star

“We are optimizing the customer journey, not maximizing the feature count.

Build the simplest system that reliably solves the user’s problem.

Smoothness first. Complexity only when proven necessary.”

Chinese product interpretation:

“我们优化的是用户旅程，不是功能数量。

先做最简单、能稳定解决问题的系统。

先保证丝滑；只有真实需求证明必要时，才增加复杂度。”

Feature count, line count, and architectural cleverness are not success
metrics.

## Permanent product rules

1. **One Task.** One screen should have one primary task.
2. **One Next Action.** A new user should know the next step within 5–10
   seconds.
3. **Smallest Working Solution.** Do not build future features before real
   customer demand proves they are necessary.
4. **Complexity Stays Inside.** Tokens, projections, versions, events,
   workflow states, and engineering terminology must not be exposed in normal
   product UI.
5. **Main-Chain First.** Every capability must make the main Broker/Customer
   journey shorter, clearer, or more reliable.
6. **No Unsupported Choices.** The product must never let a Broker request
   something the Customer cannot fully complete.
7. **Read-After-Write Guarantee.** Any accepted Customer submission must
   become visible in the authoritative Broker detail projection for the same
   case, request group, and request item.
8. **Capability Done Means User Done.** Code, tests, and deploy are
   insufficient without end-to-end Founder/manual QA.

## Standard P20 Production Loop

Each loop has exactly one narrow user-facing objective:

1. Define one narrow user-facing objective.
2. Implement the minimum change.
3. Run focused correctness/reliability tests.
4. Evaluate from Founder, Broker, and Customer perspectives.
5. Fix only P0 and high-impact P1 issues.
6. Commit and deploy to QA.
7. Perform Founder/manual QA.
8. Stop or run the next controlled loop.

Loop controls:

- Maximum three automated loops.
- Each loop has exactly one objective.
- Future feature ideas are recorded only.
- Never start the next capability automatically.
- Stop immediately when the release gate passes.
- Three failed loops with an unresolved P0 means **BLOCKED**.
- A P1 that an existing capability or reliability contract makes
  release-required is high-impact for this loop; the Production Loop does not
  waive a stricter existing gate.
- Commit, deployment, or external mutation occurs only when the current task
  explicitly authorizes it. The loop describes sequencing; it does not grant
  permission.

## Evaluation scorecard

Every capability and release review must evaluate:

1. **Reliability.** Can the main chain succeed consistently with one
   deliberate user action?
2. **Simplicity.** Can a first-time user understand the next step in 5–10
   seconds?
3. **Smoothness.** There is no guessing, duplicate action, unexplained
   waiting, or manual-refresh ritual.
4. **Business Value.** Does this reduce work or communication for the Broker
   or Customer?
5. **Scope Control.** Did the implementation avoid unproven future features?

Record each dimension as **PASS**, **CONDITIONAL**, or **FAIL**, with evidence.
A release cannot pass if any hard gate below fails, regardless of its
scorecard result.

## Permanent hard release gates

### A. Customer/Broker read-after-write consistency

An accepted Customer submission must match the authoritative Broker detail
projection for:

- the same case;
- the same request group;
- the same request item;
- the same submitted value or evidence;
- the same aggregate outcome;
- consistent workflow state; and
- consistent timeline.

### B. One Task / One State / One Next Action

The changed journey has one user task, one authoritative state, and one clear
next action.

### C. One primary CTA per screen

Secondary and recovery actions may exist but must not compete with the primary
CTA.

### D. No visible engineering jargon

Normal product UI must not expose:

- Cap3B or other internal capability labels;
- raw case IDs;
- aggregate versions;
- internal workflow names; or
- token or event IDs.

### E. No unsupported request type is sendable

A Broker cannot send a request type unless the supported Customer journey can
fully complete it.

### F. Idempotency

Retry, resume, or duplicate interaction creates:

- no duplicate command;
- no duplicate event; and
- no duplicate timeline entry.

### G. Recovery

- Every failure gives a visible recovery action.
- There is no silent fallback.
- There are no apparent no-op buttons.
- Loading always terminates; there is no infinite loading.

### H. Founder/manual QA before Capability Done

Capability Done requires recorded end-to-end Founder/manual QA evidence for
the supported journey. Automated tests, merged code, and deployment do not
substitute for this evidence.

### I. Founder Form Gate

**SSOT for this gate. All checklists and rules reference this section; do not
duplicate a conflicting copy.**

Every customer- or broker-facing form (Start Claim, intake, Request More draft,
review, and any future form) must pass all of the following before Release. Any
failure is a release blocker.

1. **Visible = canonical.** The value the user sees must equal the canonical
   form state used for validation and payload.
2. **Independent required fields.** Each required field is tested independently.
3. **Complete → enabled.** Filling all required fields enables the primary CTA.
4. **Optional never blocks.** Optional, Nice to Have, Request More, and future
   fields never block submission.
5. **No hidden rules.** No hidden length, format, or legacy validation rule may
   exist without (a) a Business Contract justification and (b) a visible
   field-level explanation.
6. **Submit validates.** Clicking submit runs final validation and surfaces the
   first invalid field (focus/scroll or explicit message).
7. **CTA is not the only signal.** A disabled CTA must never be the only error
   communication; a visible reason is always available.
8. **Normalized payload.** The payload contains the normalized values shown to
   the user.
9. **Single-flight.** Duplicate taps create exactly one command/outcome.
10. **Downstream visible.** An accepted submit is visible in the authoritative
    downstream surface (read-after-write, gate A).
11. **Device smoke.** DevTools full-compile and physical-device smoke are
    required before Release.
12. **User-completable.** A form is not Done until a real user can complete it
    without Cursor guidance.

Regression origin: the Start Claim submit button stayed disabled because hidden
artificial minimum-length gates (description ≥ 10, location ≥ 3) rejected valid
Business Contract Must Have values such as `被车后装` and `路口`, with no visible
explanation. This gate exists to make that class of failure a permanent blocker.

#### Founder State-to-Payload Gate (within §I)

**Same SSOT section — do not duplicate a conflicting copy elsewhere.**

Every customer/broker form must also pass:

1. **Visible = canonical.** Visible field value equals canonical form state.
2. **Canonical = payload.** Canonical state equals the normalized submit payload.
3. **One validator.** CTA enablement, missing-field hint, and final submit share
   one validator over the same current values.
4. **Latest input on submit.** Submit immediately after typing uses the latest
   input (flush/blur/canonical merge — not a stale `this.data` snapshot).
5. **Draft → canonical.** Draft restoration populates canonical state, not
   display-only fields.
6. **Sibling preservation.** One field update cannot erase sibling fields.
7. **Device input events.** Physical-device input/composition/blur paths are
   covered by tests or Founder smoke.
8. **Typed failures.** Error messages distinguish local validation, transport,
   domain/TLS/config, timeout, server validation, and server internal errors.
9. **Accepted-but-lost recovery.** Accepted-but-response-lost recovers via
   idempotent retry / receipt without creating a duplicate command outcome.
10. **Downstream verify.** Every real-device submission is verified on the
    authoritative downstream surface.

Regression origin: Start Claim showed populated fields and an enabled CTA while
a stale missing-field banner still listed 事故经过/时间/地点, then submit failed
with a generic “网络不稳定” mapping that hid transport/config detail. This
sub-gate makes visible↔canonical↔payload drift and opaque network errors
permanent blockers.

### J. Founder Entry and Navigation Gate

**SSOT for this gate. All checklists and rules reference this section; do not
duplicate a conflicting copy.**

Every customer Mini Program entry, Home, and post-submit navigation path must
pass all of the following before Release. A blank screen at any point is an
automatic FAIL and a release blocker.

1. **Non-blank destinations.** Every primary navigation destination renders
   non-blank content (form shell, loading, error, or actionable empty state).
2. **Home from success/result.** Home from success/result pages reaches a
   usable customer entry state (Start Claim form shell visible immediately).
3. **No stale-result stranding.** Restored sessions cannot permanently strand
   users on stale Submit Result / receipt pages with no path to a fresh entry.
4. **Scoped Start New Claim reset.** Start New Claim / Home resets only
   claim-draft resume state, not unrelated identity or API config.
5. **Shell before network.** Page shell renders before remote data completes;
   the Start Claim form must not wait on an API response to appear.
6. **Visible recovery.** Loading, error, and empty states are visible and
   actionable (clear Chinese copy + retry or safe way back).
7. **Navigation matrix.** Navigation is tested after fresh launch, successful
   submit, background/resume, and Preview reopen.
8. **Physical Preview blocker.** Physical-device Preview smoke is a release
   blocker for entry/Home paths.
9. **Blank = FAIL.** Blank screen at any point = automatic FAIL.

Regression origin: after a restored Submit Result (`提交结果` /
`已提交给陈总`), tapping the top-left Home control reached Start Claim
(`开始报案`) with a completely blank body — no fields, loading, error, or
retry — blocking Founder Form QA. This gate exists to make that class of
failure a permanent blocker.

## Required Cursor behavior

For every P20 implementation, release, or capability-review task, Cursor must:

1. Read this North Star and
   `docs/product/p20_production_loop_template.md` before implementation.
2. State one user-facing objective and what is explicitly out of scope.
3. Use the Production Loop and run no more than three automated loops.
4. Evaluate the final diff against the five-part scorecard and hard release
   gates.
5. Refuse to mark Capability Done without recorded Founder/manual QA evidence.
6. Recommend **Auto** by default.
7. Escalate to **Grok 4.5** only for a genuine cross-system blocker.
8. Use **GPT-5.6 Terra Medium** only for architecture or Blueprint decisions.
9. Never use subagents unless the founder explicitly changes this rule.
10. Stop when the release gate passes; record future ideas without
    implementing them or starting the next capability.

## Relationship to existing contracts

This standard adds a product and release acceptance layer; it does not replace
the Workflow & Timeline Blueprint, capability contract framework, runtime
truth, or deployment authorization rules.

When documents differ:

1. `docs/CURRENT_PRODUCT_SHAPE.md` remains runtime and deployment truth.
2. The Workflow & Timeline Blueprint remains canonical for internal workflow,
   command, event, state, and projection semantics.
3. This document governs customer-journey optimization, scope control,
   scorecard evaluation, hard release gates, and Capability Done.
4. The capability framework and roadmap consume these gates by reference and
   may add stricter capability-specific checks.
5. A task-specific instruction may narrow scope or withhold commit/deploy
   permission. It cannot waive a hard release gate unless the founder records
   an explicit product decision.
