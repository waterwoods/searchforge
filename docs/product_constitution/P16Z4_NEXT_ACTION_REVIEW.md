# P16-Z4 Phase 4 — Next Action Review

**Date:** 2026-06-02  
**Sprint:** P16-Z4 Case Continuity Sprint  
**Question:** Can the office know what to do next?  
**Fields:** `broker_next_step`, `still_needed_fields`, `waiting_on`, `client_prep`, `client_reply_draft`

---

## Current state

### `broker_next_step`

| Aspect | Status |
|--------|--------|
| Generated every triage/append | ✅ |
| Category templates (cancel, claim, add-car, payment, …) | ✅ Config-driven |
| P16-Y Office Actionability | **25/25 ceiling** |
| Chinese specificity | **Partial** — EN fragments in product_only glance |
| Append boundary prefixes | ✅ Injected on new_issue/borderline |
| Customer-visible on post-handoff | ❌ Removed per P16-O (correct for customer) |

**Verdict:** Office *can* know next step on **Turn 1**. On **Turn 2+**, step updates but user may not return to see it.

### `still_needed_fields` / `collected_fields`

| Aspect | Status |
|--------|--------|
| 20+ missing-info patterns (P16-Y) | ✅ |
| Glance 已收集 / 还缺 chips | ✅ Broker workbench |
| Cancel notice / SR-22 / policy gaps | ✅ Wedge strong |
| Multi-turn merge on correction | ❌ Y44/Y45 |
| `bill_sent_claimed` premium thread | ❌ Y45 |
| Deadline in structured fields | **Partial** — often prose only |

**Verdict:** Single-turn gap clarity is **strong**. Multi-turn erodes trust.

### `waiting_on` / `next_contact_by`

| Aspect | Status |
|--------|--------|
| API + persistence | ✅ |
| Chinese labels (`humanizeWaitingOn`) | ✅ |
| Defaults on create: `none` | ✅ |
| Prominent after copy | ❌ |
| Queue sort by waiting client | ⚠️ Count exists; not primary sort |
| Integration with `broker_next_step` | ❌ Not auto-linked |

**Verdict:** Office *can* set waiting state — but **must hunt** for follow-up editor. Not part of default workflow.

---

## Three-audience model (P16-Z2)

| Audience | Field | Office knows? |
|----------|-------|---------------|
| Office | `broker_next_step` | Yes Turn 1; maybe Turn 2+ |
| Customer | `client_reply_draft` | Yes if broker copies |
| System | `waiting_on`, `urgency` | Data exists; UX weak |

---

## Can the office know what to do next? — Scenario table

| Scenario | Next action clear? | Blocker |
|----------|-------------------|---------|
| Cancel + lapse notice Turn 1 | ✅ Yes | — |
| Add-car missing VIN | ✅ Yes | — |
| Claim FNOL photos | ✅ Yes | claim_intake templates |
| Client sends correction Turn 2 | ⚠️ Partial | Summary merge |
| New vehicle on append | ⚠️ Blocked | requires_new_case UX |
| Premium “already paid” thread | ⚠️ Weak | bill_sent_claimed gap |
| After copy, broker leaves | ❌ No | No waiting state cue |

---

## TOP 10 next-action improvements

| # | Improvement | Value | Effort |
|---|-------------|-------|--------|
| 1 | Chinese-only `broker_next_step` in product_only glance | Trust | 0.5 day config/copy |
| 2 | Post-copy: suggest `waiting_on: client` + one-click save | Continuity | 0.5 day UI |
| 3 | Queue row: Chinese 下一步 only (60 char) | Monday scan | 2 hr |
| 4 | Link 还缺 → `broker_next_step` (same card, no scroll) | Clarity | 2 hr layout |
| 5 | P16-Y P0 summary merge — gaps persist on correction | Multi-turn | 1–2 days engine |
| 6 | `bill_sent_claimed` for premium/payment threads | Y45 | 0.5 day rules |
| 7 | Category template tune for claim_intake (photo checklist) | Claims wedge | 0.5 day config |
| 8 | Show `manual_followup_needed` as visible badge | Honesty | 1 hr |
| 9 | Append refresh: animate/highlight changed `still_needed` | Turn 2 signal | 0.5 day UI |
| 10 | Blocklist generic broker_next_step phrases | L4 polish | 0.5 day config |

---

## Do NOT build

- New NextActionService
- CRM task lists
- Zendesk-style macro builder UI
- LLM-only next step (rules path is production default)

---

*End of P16-Z4 Phase 4*
