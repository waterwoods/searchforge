# ADR-003: No Carrier API or Quote Automation in V1

**Date:** 2026-06-20  
**Sprint:** P16 Documentation Freeze  
**Status:** Accepted  
**Authority:** `docs/p16/P16_DECISION_FREEZE_V1.md` §4 (What We Are NOT Building)  
**Supersedes:** None (formalizes existing scope exclusion)

---

## Decision

P16 does not connect to carrier APIs, AMS APIs, or quote engines in V1.

**P16 ends at: Broker Ready Packet.**

P16 does **not** produce:
- A new quote
- A new policy
- A carrier endorsement
- A premium calculation
- A carrier confirmation

---

## What P16 Does (End State)

```
Customer Docs
→ Trusted Packet
→ Broker Action (manual)
```

The broker takes the Trusted Packet and acts in their own AMS or carrier portal. P16's job is done when the broker has a clean, copy-ready packet.

---

## Rules

1. **Broker uses Copy All.** The packet is copied to clipboard. Broker pastes into their AMS or carrier portal manually.
2. **P16 does not calculate premium.** No rate tables. No carrier rating engines. No quote comparison.
3. **P16 does not promise policy is updated.** The product does not tell the customer their policy has changed.
4. **Customer-facing completion language must say:**
   - ✅ "Your request was sent to your broker."
   - ✅ "Your broker will confirm the details with you."
   - ❌ Never: "Your insurance has been updated."
   - ❌ Never: "Your new vehicle is now covered."
   - ❌ Never: "Policy change submitted."
5. **No carrier API keys, tokens, or credentials** are stored or used by P16 in V1.
6. **No AMS integration** (Applied, Hawksoft, QQ Catalyst, etc.) in V1. Broker's AMS is their own system.
7. **No quote engine calls** (EZLynx, Turborater, etc.) in V1.

---

## What Is Explicitly Not Built

| Item | Reason |
|------|--------|
| Carrier API integration (Mercury, Progressive, etc.) | Slow, permission-heavy, carrier-specific |
| AMS write-back | Out of scope; broker's AMS is their own |
| Quote engine (EZLynx, Turborater) | Separate product category; incumbents own this |
| Premium calculation | Requires carrier rate filing access |
| Policy confirmation / endorsement issuance | Requires carrier authority; not a software problem |
| E-signature for policy change | Not needed for packet-delivery model |
| Customer notification of policy change | P16 does not know when carrier confirms |

---

## Rationale

Carrier integration is:

- **Slow to build:** Each carrier has its own API, credentials, certification process, and rate filing access requirements. Mercury's API alone requires a producer appointment and a written agreement.
- **Permission-heavy:** California carriers require licensed producers to access their systems. API access is not self-service.
- **High-risk:** An error in an automated carrier submission could result in the wrong vehicle being added, wrong coverage applied, or compliance exposure.
- **Already served:** EZLynx, Turborater, and carrier portals already handle quoting. P16's early value is not quoting — it is readiness.

**P16's wedge is trust, not automation.** The broker trusts the packet because every field has a source. The broker acts on the packet in their own system. The moment P16 touches the carrier, the broker's professional judgment is bypassed — and with it, the broker's trust in the product.

The pilot question is:

> Does the packet save time and reduce errors?

Not:

> Can the software replace the broker's carrier relationship?

---

## Consequences

- **Demo is controllable.** No carrier credentials needed. No carrier sandbox. Demo works every time.
- **Product stays simple.** The packet is the product. Extraction is the feature.
- **Broker remains professional decision maker.** This preserves the broker relationship and avoids scope that P16 cannot credibly own in V1.
- **Legal exposure is minimized.** P16 never touches a policy. If a claim occurs during an add-car transition, P16 is not in the chain of liability.
- **Future carrier integration is not foreclosed.** After paid usage is established and broker explicitly asks, a read-only carrier API (dec page pull for renewals) is a logical V2 feature.

---

## Reconsideration Trigger

This decision is revisited if:

1. **10-case gate is reached** and Chen Kui explicitly requests carrier integration, OR
2. **A carrier offers a sandbox API** with no certification overhead (unlikely in V1 timeline), OR
3. **A paid customer explicitly requests AMS write-back** as a condition of payment renewal

---

*Related: `ADR_001_REQUEST_READINESS.md` · `ADR_002_NO_TIMELINE_V1.md` · `docs/p16/P16_DECISION_FREEZE_V1.md` §4*
