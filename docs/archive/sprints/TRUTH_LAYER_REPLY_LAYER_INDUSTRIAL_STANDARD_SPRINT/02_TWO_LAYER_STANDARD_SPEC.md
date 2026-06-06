# Two-Layer Standard Spec — Structured Truth vs Reply Generation

**Applies to:** Unified Intake, **Add-Car flagship** first; same pattern should extend to other lanes via packs.

**Normative rule:** If structured truth and a proposed reply disagree, **fix the reply or the truth**—never ship both as-is.

---

## A. Structured truth layer

### Purpose

Hold everything the **office, workbench, and compliance-minded reviewer** can treat as **the current case snapshot**: what we believe we extracted, what is still required, where the case sits in lifecycle, and what persistence/time actually mean.

### Canonical responsibilities

| Area | Responsibility |
|------|----------------|
| Extracted fields | Maintain `collected_fields` (and domain extras, e.g. extracted contact) as the system’s structured understanding. |
| Missing required fields | Maintain `still_needed_fields` and `next_best_question` when collection continues; **empty still-needed is a strong claim**. |
| Lifecycle state | `lifecycle_status` (e.g. `collecting`, `handoff_pending`, post-submit office states) must match gates and UI step logic. |
| Handoff gate | `handoff_ready` = “meets rule-based / product criteria to **invite** customer handoff or broker action”—**not** synonymous with “office already has the full persisted handoff package” unless formal submit + persistence say so. |
| Formal submit gate | Office-visible persistence (e.g. `formal_submit` on persist, `formal_submitted_at`) defines when the **office truly has** the customer-committed record for Stage 1. |
| Office-visible record truth | What is on the **service record** the office can open—not only conversational tone. |
| Time truth | Distinguish immutable first office-visible write vs last activity; do not present proxies as fine-grained user action audit. |
| Ready vs not ready | **Quote-prep ready** (gating fields satisfied per rules) vs **submitted to office** vs **office verified**—these are different truths and must not be collapsed in structured outputs. |

### Examples (Add-Car)

- Truth layer says: `still_needed_fields` contains `name` → structured reality is “contact not on record.”
- Truth layer says: `handoff_pending` and no formal submit → customer must still complete submit; office may not have a durable row yet.
- Truth layer says: `formal_submitted_at` set → office-visible receipt time exists for queue scanning.

### Failure modes

- `handoff_ready` true while critical keys remain missing **without** a structured exception documented in product rules.
- Lifecycle or UI step 3 while persistence semantics still describe a **pre-submit** record.
- Mixing **customer-claimed** sends with **office-verified receipt** in structured flags.

### Acceptance standard

Any **portal step, workbench column, right-rail section, and simulation state column** that claims progression must be **recomputable** from the same structured fields and persistence flags the API returns—without hidden prose-only state.

---

## B. Reply generation layer

### Purpose

Render the **current structured truth** into **clear, natural language** that answers the user’s latest turn and supports trust—**without inventing stronger facts**.

### Canonical responsibilities

| Area | Responsibility |
|------|----------------|
| Human-readable wording | Choose templates, stitched lines, or LLM-shaped drafts that reflect **current** truth. |
| Latest intent | Acknowledge questions, corrections, urgency, “already sent” claims—in **tone and focus**, not by rewriting facts. |
| Naturalness | Sound like a broker assistant, not a raw JSON dump. |
| Variation without drift | Rotate phrasing (e.g. `zh_alt`) only when **all variants remain truth-equivalent** under the same structured snapshot. |
| Reassurance | Calm, bounded reassurance (“office will verify”) **consistent with** whether we claim receipt, pending submit, or verification-in-progress. |
| Next steps | Describe what the **customer** should do next (e.g. submit, send X) **only** when the truth layer still shows that gap or gate. |

### Examples

- Handoff pending: reply stresses **formal submit** or “送办公室” **after** customer action if persistence requires it—not “已到办公室” unless formal office-visible truth holds.
- Name/phone gap while otherwise ready: reply may add a **truthful** tail that office may confirm contact—aligned with engine patterns that append contact-gap language when `still_needed` includes `name`/`phone`.
- Materials sent: reply can say office **will verify** what was sent—not that verification **completed**.

### Failure modes

- Smooth handoff templates that **sound** like persistence events without matching `formal_submitted_at` / lifecycle.
- Repeating the same handoff block when the user needed **intent-specific** acknowledgment (variety without addressing intent).
- Doc-clarification suffixes that assert “已提交办公室” when submit gate is false.

### Acceptance standard

For any release candidate, spot-check: **if the reply were read in isolation, would a regulator or broker infer any fact that is false in the JSON/state?** If yes, the reply layer failed.

---

## C. Constraint model

1. **Structured truth layer outranks reply generation layer.**
2. Reply may **interpret** (explain gates), **soften** (tone), **route** (empathy + next action), and **phrase** (templates).
3. Reply **must not expand** truth: no new fields, no stronger completion, no office receipt, no verification complete, no audit trail, no precise timing—unless the truth layer (including persistence) already supports it.
4. **Flow explanation** (right rail, §4.7) is **truth-adjacent presentation**: it must follow the same constraint as replies—derived from structured truth + formal submit semantics (see UI helpers that distinguish `handoff_ready` from formal submission complete).

---

## D. Non-overreach rules (forbidden unless supported)

Use as **test oracles** and copy review gates. “Y” = structured + persistence truth must be true before the customer-visible line is allowed.

| Category | Must not say (examples) | Unless (Y) |
|----------|-------------------------|------------|
| Office receipt | “已交办公室 / 资料已到办公室 / 办公室已收到” (and close equivalents) | Office-visible persistence after **formal submit** (or equivalent product-defined office receipt), not merely `handoff_ready`. |
| Completeness | “资料已经齐了 / 没有缺项了” | `still_needed_fields` empty **and** product rules do not require unstated human confirmation for that claim. |
| Office verification | “办公室已核对完成 / 已核实无误” | Truth layer reflects verified status (Stage 2+ capability)—not default in Stage 1 from customer claims alone. |
| Quote readiness | Implies binding quote or carrier-ready package | Gating fields and policy for quote-prep readiness satisfied; no implication of pricing execution. |
| Field-level audit | Implies per-field version history or diff timeline | Such audit exists in data model and is accurate. |
| Submit timing | Exact “您于 HH:MM 提交” from thin proxies | Timestamp is the **correct semantic** (e.g. real formal submit time), not a misleading proxy. |
| Record identity | “同一条记录” when session/case identity is ambiguous | Stable `case_id` / record identity matches the claim. |

---

## E. Industrial review checklist

Use at end of sprints, before demos, and in Role C / live batteries:

- [ ] Are **required gating fields** present for the readiness claim the UI/reply makes?
- [ ] Does **lifecycle** justify the **step** and “who owns next action”?
- [ ] Is **office receipt** language tied to **formal submit + persistence**, not `handoff_ready` alone?
- [ ] Is **submit timing** labeled honestly (immutable first office write vs activity bump)?
- [ ] Does the reply answer **latest user intent** without **exceeding** truth?
- [ ] Do **handoff phrases** have **truth-equivalent alts** only—no stronger claims in one variant?
- [ ] Does the **right rail** agree with the **same** `still_needed_fields` / formal completion the API returns?

---

## Acceptance criteria (for “standard is live”)

1. Core docs (`UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md`, `PROJECT_TRUTH_SWITCH.md`) explicitly name the two layers and subordination.
2. This spec exists and lists **non-overreach** rules and a **checklist**.
3. Engineering backlog may reference this doc ID when fixing known mismatches (implementation is **out of scope** for the sprint that only publishes the standard).
