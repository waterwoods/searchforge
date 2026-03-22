# Quote-Ready + Contact Readiness Spec

**Sprint:** Add-Car Identity + Contact Lite  
**Purpose:** Define how quote-ready interacts with missing contact info; what states are visible.

---

## 1. Quote-Ready vs Contact-Ready

| State | Meaning |
|-------|---------|
| **quote_ready** | Vehicle + zip + (delivery OR driver) — office can run quote |
| **contact_ready** | Name + phone collected — broker can follow up |
| **quote_ready + contact missing** | Can run quote; broker should confirm name/phone before or after |

---

## 2. Can a Case Be Quote-Ready Without Name/Phone?

**Yes.** Quote-ready is about vehicle data. Contact is about follow-up.

- Case can be quote_ready and still have still_needed: ["name", "phone"]
- Broker can run quote; broker_next_step says "Confirm name/phone for follow-up" or similar

---

## 3. States to Display

| Combination | Display |
|-------------|---------|
| quote_ready + name + phone | Quote-ready, Contact complete |
| quote_ready + name only | Quote-ready, Phone needed |
| quote_ready + phone only | Quote-ready, Name needed |
| quote_ready + neither | Quote-ready, Contact needed |
| almost_ready | Almost ready (vehicle+zip, missing delivery/driver) |
| need_more | Need more (vehicle or zip missing) |

---

## 4. What Broker Should Do When Quote Data Sufficient but Contact Thin

- **Run quote** — vehicle data is enough for office pricing
- **Note contact needed** — broker_next_step: "Run quote. Confirm name/phone for follow-up."
- **Ask on next touch** — If customer replies, ask for name/phone then

---

## 5. Readiness Logic (V1)

- **quote_ready_status:** Unchanged (quote_ready | almost_ready | need_more)
- **contact_ready:** Derived: (customer_name or name in collected) AND (customer_phone or phone in collected)
- **contact_needed:** When quote_ready or almost_ready and not contact_ready

---

*See also: 04_BROKER_CONTACT_VISIBILITY_SPEC.md*
