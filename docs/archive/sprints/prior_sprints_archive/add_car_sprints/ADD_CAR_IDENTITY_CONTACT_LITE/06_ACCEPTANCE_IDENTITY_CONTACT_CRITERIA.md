# Acceptance / Identity-Contact Criteria

**Sprint:** Add-Car Identity + Contact Lite  
**Purpose:** Practical criteria for reduced fake/demo feel, lightweight contact, broker clarity.

---

## 1. Reduced Fake/Demo Feel

- [ ] Add-car case shows contact block (name, phone or "needed")
- [ ] When customer says name/phone in chat, it appears in case
- [ ] Quote-ready and contact-needed are both visible

---

## 2. Lightweight but Useful Contact Collection

- [ ] Name and phone are minimum fields
- [ ] Email is optional/deferred
- [ ] No long form; chat or single prompt only
- [ ] collected_fields includes name, phone when extracted
- [ ] still_needed_fields includes name, phone when missing (for add-car quote-ready)

---

## 3. Broker Follow-Up Clarity

- [ ] broker_next_step mentions contact when quote-ready but contact missing
- [ ] Broker sees "Name: X" / "Phone: Y" or "Name needed" / "Phone needed"
- [ ] PATCH /customer works for manual entry (existing API)

---

## 4. Acceptable Simplicity for V1

- [ ] Extraction is regex/heuristic (no LLM for contact)
- [ ] No verification (no phone validation, no ID check)
- [ ] Contact block is display + optional edit; no complex UX
- [ ] Add-car simulations pass with contact-lite scenarios

---

*See also: 07_FOUNDER_INSPECTION_NOTES.md*
