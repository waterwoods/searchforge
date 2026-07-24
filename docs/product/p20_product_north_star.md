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
6. **Submit validates.** Clicking submit runs final validation, does not call
   the API when invalid, identifies the exact first invalid field, and focuses
   or scrolls to it.
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
8. **Typed failures.** Error messages distinguish local validation, request not
   sent, transport, domain/TLS/config, timeout, authentication/configuration,
   server validation, and server internal errors. Retry is offered only when it
   is safe and useful; completed values remain intact.
9. **Accepted-but-lost recovery.** Accepted-but-response-lost recovers via
   idempotent retry / receipt without creating a duplicate command outcome.
10. **Downstream verify.** Every real-device submission is verified on the
    authoritative downstream surface.
11. **Safe device diagnostics.** Prototype/QA evidence records the secret-free
    request URL, method, start/end timestamps, HTTP status or transport
    `errMsg`/`errno`, safe error code, command/idempotency identity, whether the
    backend received it, and whether exactly one downstream outcome exists.
12. **No unverified guarantee.** User copy must not promise that retry cannot
    duplicate an outcome until persistent-store replay and downstream
    exactly-once behavior are verified end to end.

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
2. **Home routing (P29 Service Home).** Capsule / operational Home is the
   product entrance (Home ≠ Task Home):
   - Capsule Home / `pages[0]` Start Claim redirects to **Service Home**
     (must not clear an active resume token first).
   - **If** an active case/token exists → Service Home shows
     **继续处理当前报案** (primary) → Entry → Task Home.
   - **Else** → Service Home shows **开始报案** → Start Claim form
     (`?entry=form`).
   `pages[0]` remains Start Claim for Build Gate packaging.
3. **Start New Claim vs Home.** Explicit「开始新的报案」with an active case
   shows the One Active Case policy (continue / contact broker) and must
   **not** clear the resume token or create a second Active Case. Empty-state
   Start Claim (no active case) opens the form. Home with an active case must
   **not** clear the token.
4. **No stale-result stranding.** Restored sessions cannot permanently strand
   users on stale Submit Result / receipt pages with no path to a fresh entry
   or Task Home.
5. **Scoped Start New Claim reset.** Start New Claim resets only claim-draft
   resume state, not unrelated identity or API config.
6. **Shell before network.** Page shell renders before remote data completes;
   the Start Claim form must not wait on an API response to appear.
7. **Visible recovery.** Loading, error, and empty states are visible and
   actionable (clear Chinese copy + retry or safe way back).
8. **Navigation matrix.** Navigation is tested after fresh launch, successful
   submit, background/resume, and Preview reopen.
9. **Physical Preview blocker.** Physical-device Preview smoke is a release
   blocker for entry/Home paths.
10. **Blank = FAIL.** Blank screen at any point = automatic FAIL.

Regression origin: (1) restored Submit Result Home opened a blank Start Claim
body; (2) P26A Founder QA — capsule Home with an active Camry token cleared
resume and stranded the customer on「开始报案」instead of Task Home. This gate
makes both classes permanent blockers.

### J2. Three Permanent Customer Flow Gates (P26G)

**SSOT for this gate. Every future customer workflow feature must pass all three.**

**Invariant:** NORMAL CUSTOMER INTAKE MUST NOT REQUIRE A BROKER ACTION TO
CONTINUE. Broker actions may request clarification, replacement evidence,
exceptional documents, or reopen completed tasks — they must not unlock
accident story, date, location, injury, vehicle/VIN, insurance card, or
required accident photos.

| Gate | Question | Hard FAIL if |
|------|----------|--------------|
| **1. First-Time Customer** | Can a completely new customer complete normal intake with zero broker actions? | Broker Request More / QR is required to see or complete default tasks |
| **2. Return-Later** | Can the same customer exit and continue the same case without rescanning? | Ordinary continuation requires a new QR; resume token/session is ignored or unsafe |
| **3. Exceptional Follow-Up** | Can Broker add a special request without replacing/hiding/corrupting default intake? | Default and broker-requested tasks overwrite each other; completed work returns to pending |

**Task source contract:** every customer-facing task carries `task_source`
(`system_default` | `broker_requested`). Display text is not the source
identifier. Constitution owns the merged plan; clients do not invent checklists.

**Resume contract:** first valid entry binds and persists a server-validated
resume token; later app entry resolves the same active case → Task Home.
Do not trust `active_case_id` from local storage alone. QR remains valid for
first binding, new device, expired session, broker deep link, or a distinct
new claim — not for every ordinary continuation.

**User Journey Contract template** (required before any new task type is
production-ready): Who initiates? When visible? Default / conditional /
broker-requested? Who completes? What canonical fact/evidence completes it?
Broker confirmation required? Return-later behavior? Refresh/re-entry?
Timeline event? Constitution output? Broker view? Security boundary?

### K. Mini Program Build Gate

**SSOT for this gate. All checklists and rules reference this section; do not
duplicate a conflicting copy.**

This gate executes **before** Founder Form Gate (§I), Founder Entry and
Navigation Gate (§J), and physical-device QA. If it fails, Release stops
immediately — do not proceed to Form/Navigation/device QA.

**Permanent Preview contract:** Preview package must always behave like the
release package. Never allow page filtering, component filtering, hidden
compile conditions, stale Preview tokens, a missing first page, or
`wx://not-found`.

Automated command (from `miniapp/`):

```bash
npm run build:gate
```

Repo-root equivalent: `node scripts/validate_miniapp_build_gate.mjs`

The gate must verify at minimum:

1. `app.json` page registration is valid and `pages[0]` is Start Claim
   (capsule Home entry; active-case redirect to Service Home is enforced in
   Start Claim / `startClaimEntry` — see §J Home routing).
2. Every registered page exists on disk (`.ts` / `.json` / `.wxml` / `.wxss`).
3. Every `usingComponents` path exists.
4. Filename casing matches exactly.
5. Required page and component files exist.
6. Preview package contains Start Claim.
7. Preview package contains Entry.
8. Preview package contains Receipt.
9. `ignoreDevUnusedFiles == false` (and `ignoreUploadUnusedFiles == false`).
10. `lazyCodeLoading` uses the approved value (field omitted — never
    `requiredComponents`).
11. Compile condition is clean (`project.config.json` `condition: {}`; private
    first path is Start Claim when present).
12. No stale token is baked into a compile-condition launch query.
13. AppID is the real Mini Program AppID (not `touristappid`).
14. `apiProfile` is `qa` for Preview.
15. Request合法域名 host matches the committed QA API host
    (`fiqa-api-g7zatxrycq-uw.a.run.app`); WeChat admin must whitelist this host
    before physical Preview.
16. Preview preflight passes.

Regression origin: physical Preview Remote Debug showed
`<body id="wx://not-found"></body>` because `ignoreDevUnusedFiles=true`
filtered required page code out of the Preview package. This gate exists to
make that packaging class a permanent blocker.

**Founder sequence after Build Gate PASSes:**

1. Clear DevTools cache (全部清除).
2. Full compile.
3. Generate a new Preview QR.
4. Confirm Remote Debug connects.
5. Confirm Start Claim renders (not `wx://not-found`).
6. Run Founder Form Gate (§I).
7. Run Founder Entry and Navigation Gate (§J).
8. Complete physical-device QA.

## Required Cursor behavior

For every P20 implementation, release, or capability-review task, Cursor must:

1. Read this North Star and
   `docs/product/p20_production_loop_template.md` before implementation.
2. State one user-facing objective and what is explicitly out of scope.
3. Use the Production Loop and run no more than three automated loops.
4. Enforce **Mini Program Build Gate (§K)** before Form (§I), Navigation (§J),
   or physical Preview QA (`cd miniapp && npm run build:gate`).
5. Evaluate the final diff against the five-part scorecard and hard release
   gates.
6. Refuse to mark Capability Done without recorded Founder/manual QA evidence.
7. Recommend **Auto** by default.
8. Escalate to **Grok 4.5** only for a genuine cross-system blocker.
9. Use **GPT-5.6 Terra Medium** only for architecture or Blueprint decisions.
10. Never use subagents unless the founder explicitly changes this rule.
11. Stop when the release gate passes; record future ideas without
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
