# Add-Car Commercial Flow Hardening Blueprint

**Sprint:** Add-Car Commercial Flow Hardening  
**Created:** 2026-03-20  
**Purpose:** Why add-car deserves full-module hardening, why commercially, what to strengthen, what to defer.

---

## 1. Why Add-Car Deserves Full-Module Hardening

Add-car is the **highest-frequency, highest-value scenario** in the broker standard package. Chen Kui and other brokers do this daily. If add-car feels like a demo, the whole product feels like a demo. If add-car feels like a real office tool, the product earns trust.

| Prior Sprint | What It Delivered |
|--------------|-------------------|
| ADD_CAR_QUOTE_EXCELLENCE | Ask-next quality, correction handling, broker summary, broker_next_step |
| ADD_CAR_IDENTITY_CONTACT_LITE | Name + phone; contact-ready vs quote-ready |
| ADD_CAR_ATTACHMENT_READY_LITE | Upload support; materials received vs optional |
| WORKBENCH_HANDOFF_PROFESSIONALIZATION | 3–5 second scan; key signals above fold; broker_next_step quality |

**What’s missing:** These sprints built pieces. No single sprint owned the **full commercial flow** from customer entry through broker follow-up. Gaps remain at seams: contact + attachment interaction, readiness combinations, broker scan-at-a-glance, weak-point fix discipline.

---

## 2. Why Commercially

| Commercial Driver | Add-Car Impact |
|-------------------|----------------|
| **First paid pilot** | Add-car is scenario #1 in the standard package; must be flagship |
| **Broker trust** | Chen Kui needs to see: real lead, real materials, real next step — not a chat toy |
| **Trial credibility** | "Good enough to show as flagship" = add-car end-to-end feels like real intake |
| **Office usability** | Broker opens case → understands in 3–5 seconds → knows exactly what to do |
| **No rework** | Broker should not re-ask for vehicle, zip, contact, or materials already provided |

---

## 3. What to Strengthen

| Area | Target |
|------|--------|
| **End-to-end flow** | Entry → intake → field completion → attachment → quote-ready → handoff → broker follow-up — coherent, documented |
| **Readiness completeness** | Need more / Almost ready / Quote-ready; contact and attachment as separate signals; all combinations defined |
| **Broker workbench usability** | 3–5 second scan; above fold; quote-ready, contact, attachment, correction; broker_next_step always actionable |
| **Weak-point fix queue** | Fix-now, fix-next, acceptable-for-trial, defer — prioritized, no scope creep |
| **Commercial feel** | Realism, coherence, office usability, scope discipline |

---

## 4. What to Defer

| Deferred | Reason |
|----------|--------|
| **OCR / document extraction** | Risky; not reliable; scope creep |
| **Carrier quote engine** | Out of scope; broker runs quote manually |
| **Full CRM** | Not part of standard package |
| **Multi-tenant / auth** | First pilot is single broker |
| **Email/WeChat integration** | Paste-only for V1 |
| **Mandatory attachment** | Chat-only must work; uploads are accelerators |
| **Coverage tiers / limits** | Deferred to V2 |

---

## 5. Success Criteria (High Level)

Add-car is **commercially hardened** when:

1. **Full flow is spec’d** — Customer entry through broker follow-up; no undocumented seams
2. **Readiness combinations are clear** — Quote-ready + contact + attachment; all states defined
3. **Broker sees everything above fold** — Quote-ready, contact, attachment, correction, broker_next_step
4. **Weak points are prioritized** — Fix-now vs acceptable-for-trial vs defer
5. **Founder can show add-car as flagship** — 4–6 flows demoable; no awkward moments; "good enough to show Chen Kui"

---

*See also: 02_ADD_CAR_END_TO_END_FLOW_SPEC.md, 03_ADD_CAR_READINESS_COMPLETENESS_SPEC.md, 05_ADD_CAR_WEAK_POINT_FIX_QUEUE_SPEC.md*
