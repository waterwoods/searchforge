# Add-Car Identity + Contact Lite Blueprint

**Sprint:** Add-Car Identity + Contact Lite  
**Created:** 2026-03-19  
**Purpose:** Extend add-car Real Intake Lite with lightweight customer identity/contact so the flow feels more like a real insurance intake and less like an anonymous chat demo.

---

## 1. Why Add-Car Still Feels Slightly Fake Today

| Weakness | What it means |
|----------|---------------|
| **Anonymous lead** | Broker gets vehicle + zip + delivery but not who the person is or how to reach them. |
| **No customer identity** | Name and phone are not collected or extracted; case feels like "a vehicle discussion" not "a lead." |
| **Broker follow-up gap** | Broker must re-ask "who are you?" and "how do I call you?" after handoff. |
| **Thin customer trust** | Customer doesn't see that their identity is being captured; feels like a generic chat. |
| **Quote-ready but not contact-ready** | Quote_ready_status exists; contact readiness does not. |

---

## 2. Why Identity/Contact Matters Now

- **Broker trust:** Chen Kui needs to see a real lead with name + phone, not just vehicle data.
- **Trial credibility:** "Real intake" requires at least minimal contact info for follow-up.
- **Commercial value:** Add-car is highest-frequency; making it feel like real lead capture multiplies product value.
- **Handoff realism:** Broker can call or message the customer immediately without re-asking.

---

## 3. What This Sprint Will Strengthen

| Area | Target |
|------|--------|
| Contact fields | Name + phone as minimum; email optional/deferred |
| Chat extraction | When customer says name/phone in chat, populate fields |
| Broker visibility | Contact block in workbench; still-needed when missing |
| broker_next_step | Mention "confirm name/phone" when quote-ready but contact thin |
| Quote + contact clarity | Quote-ready and contact-ready are distinct; both visible |

---

## 4. What This Sprint Intentionally Will NOT Do

- **No full CRM** — no deep customer profile management
- **No long forms** — no multi-step onboarding
- **No OCR** — no document extraction for identity
- **No email requirement** — email is optional or deferred
- **No verification** — no ID verification, no phone validation
- **No split** — chat and structured intake stay integrated

---

## 5. Success Criteria

Add-car feels "real enough for trial" when:

1. Name and phone are collected or clearly still-needed when appropriate
2. Chat can populate name/phone when customer volunteers them
3. Broker sees contact block in workbench (name, phone or "needed")
4. broker_next_step mentions contact when quote-ready but contact missing
5. Quote-ready and contact-ready states are explainable and visible

---

*See also: 02_MINIMAL_CONTACT_FIELD_SPEC.md, 03_QUOTE_READY_CONTACT_READINESS_SPEC.md, 04_BROKER_CONTACT_VISIBILITY_SPEC.md*
