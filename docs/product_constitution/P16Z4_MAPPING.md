# P16-Z4 Phase 6 — Zendesk / Intercom / Stripe Mapping

**Date:** 2026-06-02  
**Sprint:** P16-Z4 Case Continuity Sprint  
**Benchmarks:** Zendesk Timeline, Intercom Follow-up, Stripe Simplicity  
**Rule:** Map against **current repo** — no greenfield

---

## Zendesk Timeline → SearchForge

| Zendesk pattern | Our equivalent | % built |
|-----------------|----------------|---------|
| Ticket comment thread | `case_messages[]` | **90%** |
| Internal notes | `case_notes[]` | **85%** |
| Audit events | `case_activity[]` | **90%** |
| Status history | `lifecycle_status`, `case_status` | **80%** |
| Agent-facing timeline UI | Broker activity collapse | **40%** |
| Customer-visible history | `UserCaseListProgressPanel` | **50%** |
| SLA breach events | `urgency` + deadline in summary | **60%** |
| @mentions / assignments | — | **0%** (out of scope) |

---

## Intercom Follow-up → SearchForge

| Intercom pattern | Our equivalent | % built |
|------------------|----------------|---------|
| Snooze / waiting | `waiting_on`, `next_contact_by` | **85%** |
| Handoff summary | `conversation_summary` | **80%** |
| Fin → human | `handoff_ready`, customer_question lane | **75%** |
| Same-conversation append | `append_follow_up_message` | **90%** |
| New conversation for new topic | `requires_new_case` boundary | **85%** |
| Operator queue | Broker case queue | **70%** |
| In-app return when customer replies | — | **10%** |
| Proactive “waiting on you” | — | **5%** |

---

## Stripe Simplicity → SearchForge

| Stripe pattern | Our equivalent | % built |
|----------------|----------------|---------|
| One primary action per screen | 复制客户草稿 | **75%** Turn 1 only |
| Receipt-style confirmation | P16-O post-submit card | **80%** customer |
| Minimal fields | Paste-first | **90%** |
| Clear next step on success | Post-copy bridge | **15%** |
| No dashboard clutter | product_only mode | **70%** |
| Progress feels inevitable | 3-step empty state (P16-M) | **40%** |

---

## Cross-map: North Star stages

| Stage | Zendesk | Intercom | Stripe lesson | SearchForge |
|-------|---------|----------|---------------|-------------|
| Case | Ticket | Conversation | — | `save_case` ✅ |
| Timeline | Comments | Thread | — | `case_messages` ✅ UX ❌ |
| Next Action | Macros | Suggested reply | Primary CTA | `broker_next_step` ✅ |
| Follow-up | Snooze | Waiting | Success copy | `waiting_on` ✅ UX ❌ |

---

## TOP 20 ideas already ~70% implemented

| # | Idea | % | Revive how |
|---|------|---|------------|
| 1 | Same-case customer follow-up append | 90% | Post-copy CTA |
| 2 | Office audit trail | 90% | Default-open activity |
| 3 | Message-level case thread | 90% | Render `case_messages` |
| 4 | Handoff summary for operator | 80% | Promote `conversation_summary` |
| 5 | Waiting on client/carrier | 85% | One-click after copy |
| 6 | New-issue boundary (don’t pollute case) | 85% | Better blocked UX |
| 7 | Category-specific next actions | 80% | Chinese config tune |
| 8 | Copy-to-channel draft | 80% | Already primary |
| 9 | Multi-turn triage before persist | 75% | Customer tab expose |
| 10 | Session restore mid-intake | 75% | Document for assistant |
| 11 | Attachment on case | 75% | Broker upload CTA |
| 12 | Claim FNOL templates | 75% | Config polish |
| 13 | Urgency-driven response window | 70% | `getResponseWindow` in glance |
| 14 | Queue with case preview | 70% | Chinese 下一步 only |
| 15 | Follow-up PATCH without re-triage | 85% | Promote in UI |
| 16 | Append re-triage refreshes gaps | 80% | Highlight delta |
| 17 | Formal submit timestamp | 80% | Show in glance |
| 18 | Guardrail append batteries | 70% | CI gate |
| 19 | My Requests progress | 70% | Week 3 customer |
| 20 | product_only surface reduction | 70% | P16-M batch |

---

## Explicitly NOT mapped (P17 / out of sprint)

- Zendesk triggers webhooks
- Intercom Fin autonomous resolution
- Stripe billing portal
- Multi-tenant assignment
- Email/push return triggers

---

*End of P16-Z4 Phase 6*
