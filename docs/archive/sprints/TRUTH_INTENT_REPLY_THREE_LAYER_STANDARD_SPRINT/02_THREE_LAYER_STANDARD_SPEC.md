# Three-Layer Standard Spec — Truth → Intent → Reply

**Applies to:** Unified Intake, **Add-Car flagship** first; extend to other lanes via packs.

**Normative rule:** Decisions flow **Truth → Intent → Reply**. If any layer disagrees with a lower layer, **fix the upper layer** (or fix truth if truth was wrong)—never ship contradictory customer-visible behavior.

**Relationship to the two-layer spec:** `TRUTH_LAYER_REPLY_LAYER_INDUSTRIAL_STANDARD_SPRINT/02_TWO_LAYER_STANDARD_SPEC.md` remains valid as **Truth vs Reply** non-overreach rules. This document **adds** the **Intent layer** and the **constraint chain** so “truth-safe but wrong answer” is also a first-class failure mode.

---

## A. Truth Layer

### Purpose

Hold everything the **office, workbench, compliance-minded reviewer, and persistence layer** can treat as **the current case snapshot**: what was extracted, what is still required, lifecycle position, **gates**, and **what actually happened in time** for office visibility.

### Canonical responsibilities

| Area | Responsibility |
|------|----------------|
| Extracted / collected fields | `collected_fields` and domain extras (e.g. contact) as structured understanding. |
| Missing required fields | `still_needed_fields`, `next_best_question`; **empty still-needed is a strong claim**. |
| Lifecycle state | `lifecycle_status` (e.g. `collecting`, `handoff_pending`, post–formal-submit states) aligned with gates and UI step logic. |
| Handoff gate | `handoff_ready` = meets criteria to **invite** handoff / broker action—**not** synonymous with “office already has the durable record” unless formal submit + persistence agree. |
| Formal submit gate | Office-visible persistence (`formal_submit`, `formal_submitted_at`) defines when the office **truly has** the customer-committed Stage-1 record. |
| Office-visible record truth | What is on the **service record** the office can open—not conversational tone alone. |
| Time truth | Immutable first office-visible write vs last activity (`formal_submitted_at` vs `updated_at`); no fine-grained audit claims from thin proxies. |
| Ready / not ready / submitted / verified | **Quote-prep ready** vs **submitted to office** vs **office verified** are distinct; must not be collapsed in structured outputs. |

### Examples (Add-Car)

- `still_needed_fields` contains `name` → structured reality: contact not on record; **ready/handoff copy must not pretend identity is complete**.
- `handoff_pending` and no `formal_submitted_at` → customer must still **formally submit**; “office already has it” is **not** supported.
- `formal_submitted_at` set → office-visible receipt time exists for queue scanning.

### Failure modes

- `handoff_ready` true while critical keys remain missing without a documented product exception.
- Lifecycle or UI step 3 while persistence still describes a **pre-submit** record.
- Mixing **customer-claimed sends** with **office-verified receipt** in structured flags.
- **Truth drift** in customer-visible surfaces: any line (reply, rail, flow explanation) asserting receipt, completeness, or verification without matching truth + persistence.

### Acceptance standard

Any **portal step, workbench column, right-rail section, API field, and simulation state column** that claims progression must be **recomputable** from the same structured fields and persistence flags—**no hidden prose-only state**.

---

## B. Intent Layer

### Purpose

Resolve **what the current customer turn is trying to do**—the **question or job behind the latest message**—in a way that is **bounded, explainable, and stable under long threads**, so the system does not **collapse distinct late-turn needs** into one template family.

### Canonical responsibilities

| Area | Responsibility |
|------|----------------|
| Current-turn job | Classify the **primary job** of the latest user message (possibly with a secondary hint when mixed). |
| Examples of intent families | Supplementing information; **correcting** prior information; asking **timeline/process**; asking **quote/coverage/deductible** detail; **claiming materials sent**; asking whether **office received** the record; urgency without new facts; narrow clarification. |
| Inputs | **Latest turn** (required), **conversation context** (recent turns), **truth-layer state** (hard constraint—not optional context). |
| Bounded labels | Intent is **not** free-form chat understanding; it should map to **reviewable categories** (or explicit “uncertain / needs clarification”) for regression and QA. |
| Avoid collapse | Distinct intents (e.g. “did you get my PDF?” vs “when will someone call?”) must not **routinely** map to the same **reply family** without an explicit, testable reason. |
| Truth as ceiling | Intent resolution **cannot** conclude an outcome that truth forbids (e.g. “confirm office has record” as the job-to-answer when formal submit has not occurred). |

### Examples

- Latest: “资料我昨天就发了”—intent includes **materials-claim**; truth may still show **not office-verified** → answer job: acknowledge send, **verify pending**, no “已核对完成”.
- Latest: “大概多久能出报价？”—intent = **process/timeline**; reply addresses SLA-style guidance **within** truth (stage, handoff state), not a random handoff block.
- Latest: “名字我写错了改一下”—intent = **correction**; truth layer must update structured fields; reply confirms correction path, not generic closure.

### Failure modes

- **Intent collapse:** Many late-turn questions **all** routed to one **generic** handoff/submit/closure family.
- **Intent–truth mismatch:** Resolved intent assumes **receipt** or **completeness** when truth says otherwise.
- **Stale intent:** Answering an **earlier** turn’s topic while ignoring the **latest** question.
- **State–intent mismatch:** Lifecycle says **collecting** but reply behaves like **post-submit reassurance** (or the reverse).

### Acceptance standard

For a given turn, a reviewer can answer **yes** to: “If we strip wording, **what job is the customer asking us to do now**, and is that job **allowed** by truth?” Intent must be **stable enough** to regression-test (named categories or explicit uncertainty).

---

## C. Reply Layer

### Purpose

Render **truth + resolved intent** into **natural, customer-appropriate wording**: acknowledge the **actual** current job, stay **within** facts, and support trust without inventing completion.

### Canonical responsibilities

| Area | Responsibility |
|------|----------------|
| Answer the resolved intent | The reply’s **primary thrust** must match the **Intent layer** outcome for this turn (not only global state). |
| Naturalness | Broker-assistant tone; not raw JSON. |
| Variation without drift | Rotate templates / `zh_alt` only when **truth- and intent-equivalent**. |
| Reassurance | Calm, bounded (“office will verify”) **consistent** with receipt / pending / verification truth. |
| Next steps | Describe customer actions **only** when truth still shows that gap or gate. |

### Examples

- Intent = **office receipt check** + truth = no formal submit → explain **submit** path; do not say “已到办公室”.
- Intent = **timeline** + truth = `handoff_pending` → honest **process** answer + **submit** CTA if appropriate.
- Intent = **correction** → confirm what was updated per truth; do not add **verification-complete** language.

### Failure modes

- **Reply overreach:** “资料齐了”, “办公室已核对完成”, “已正式收到” without truth support (inherits two-layer forbidden table).
- **Truth-safe genericism:** Technically no false atomic claim, but **ignores latest intent** (repeated post-submit templates, contact-gap tail overuse when the question was not contact).
- **Long-thread degradation:** Turns 7–10 **stop responding to the latest question** and replay **generic closure**.

### Acceptance standard

Spot-check: (1) **Would a broker infer any fact from the reply that is false in JSON/state?** (two-layer.) (2) **Does the reply answer what the latest turn was trying to do?** (three-layer.) If either fails, the reply layer failed.

---

## D. Constraint Rules

### D.1 Truth constrains Intent

Intent classification and resolution **must** use truth-layer state as **hard constraints**.

- If **formal submit** has not happened, the **resolved intent** cannot be “office already has the full record” as the **job we answer**.
- If **`still_needed_fields`** is non-empty, intent cannot assume **completeness** for purposes of answering.
- If only **customer-claimed** materials exist, intent cannot justify **office-verified** answer jobs.

### D.2 Intent constrains Reply

Reply generation must:

- **Address** the **resolved current-turn intent** (primary job).
- **Remain** within truth for every factual claim.

**Ordering:** choose **what to say** (Intent), then **how to say it** (Reply) within truth.

### D.3 Reply may not outrun Truth

Same as two-layer spec: reply may phrase, soften, reassure, route empathy; reply **must not** claim stronger facts, skip gating fields, or imply receipt/verification/quote completion prematurely.

---

## E. Forbidden Overreach / Collapse Rules

Use as **test oracles** and copy review gates. These are **additive** to the two-layer forbidden table.

| Category | Forbidden unless |
|----------|------------------|
| **Truth drift** | Reply or rail says office **has** the record when formal submit / persistence truth does not support it. |
| **Intent collapse** | Distinct late-turn intents systematically receive the **same** template family **without** intent-equivalence justification. |
| **Reply overreach** | “资料齐了”, “办公室已核对完成”, “已正式收到”, precise timing from proxies—see two-layer **D** table. |
| **State / intent mismatch** | Lifecycle says **A** but reply behaves as if **B** (e.g. collecting thread gets post-submit reassurance). |
| **Long-thread degradation** | Turns 7–10: reply **does not** engage latest question; only **generic** closure. |
| **Right-rail / reply story split** | Customer reads reply implying X while right-rail truth says Y for the same record snapshot. |

---

## F. Industrial Review Checklist

Use at sprint end, before demos, Role C / live batteries, and regression on long threads.

**Truth**

- [ ] Are **gating fields** present for any **readiness / receipt** claim in UI or reply?
- [ ] Does **lifecycle** justify **step** and **next owner**?
- [ ] Is **office receipt** tied to **formal submit + persistence**, not `handoff_ready` alone?
- [ ] Are **time** labels honest (immutable first office write vs activity)?

**Intent**

- [ ] What is the **resolved current-turn intent** for this message (named category or explicit uncertainty)?
- [ ] Is that intent **allowed** by truth (no impossible jobs)?
- [ ] Are we **not** collapsing distinct intents into one family without cause?

**Reply**

- [ ] Does the reply **answer** the resolved intent, not only global state?
- [ ] If the reply were read alone, would a broker infer **any false fact** vs JSON/state?
- [ ] On turn **≥7**, does the reply still **engage the latest question**?

**Cross-surface**

- [ ] Do **right rail**, **flow explanation**, and **reply** tell the **same story** for the same snapshot?

---

## G. Acceptance criteria (doctrine “live”)

1. Core docs (`UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md` §4.9, `PROJECT_TRUTH_SWITCH.md` §6A) name **Truth, Intent, Reply** and the **constraint chain**.
2. This spec exists with **forbidden failure modes** and **checklist**.
3. Engineering backlog may reference **intent resolution** as a first-class work item (implementation may follow in dedicated sprints).

---

## H. Honest mapping to current Add-Car system (snapshot)

- **Truth:** Implemented via `collected_fields`, `still_needed_fields`, `lifecycle_status`, `handoff_ready`, formal submit / `formal_submitted_at`, persistence in `case_store.py`—and UI helpers such as `isFormalSubmissionToOfficeComplete` in `AddCarRecordSummaryRail.tsx`.
- **Reply:** Template families, stitched lines, `client_reply_draft` paths in `triage.py`, handoff phrase config.
- **Intent:** **Partially** present (markers, mixed-intent notes, `intent_hint`, `_detect_secondary_intent_hint`, latest-snippet summaries)—**not yet** a single explicit, testable **intent resolution artifact** in the API contract for every turn.

**Gap to close later:** Make **resolved intent** as explicit and reviewable as **structured truth**, without breaking hot-swappable packs.
