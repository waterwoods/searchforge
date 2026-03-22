# Add-Car Broker Workbench Usability Spec

**Sprint:** Add-Car Commercial Flow Hardening  
**Purpose:** What broker sees in 3–5 seconds; above fold; quote-ready/contact/attachment/correction; broker_next_step.

---

## 1. What Broker Should Understand in 3–5 Seconds

| Item | Must See | Where |
|------|----------|-------|
| Case focus | Add car quote | Above fold |
| Quote-ready status | Quote-ready / Almost ready / Need more | Above fold |
| Contact | Name, phone — or "needed" | Above fold |
| Attachment | Present or not | Above fold |
| Correction | If customer corrected | Near next step |
| One clear next step | broker_next_step | Above fold |
| Collected / Still needed | Chips | Above fold |

---

## 2. What Must Appear Above the Fold

1. **Case focus tag** — Add car quote
2. **Quote-ready status** — Tag with color (green/gold/orange)
3. **Contact block** — Name, phone or "Name needed" / "Phone needed"
4. **Attachment presence** — PaperClip icon + count or "Materials received" / "Optional"
5. **Correction badge** — When customer corrected vehicle/zip/driver
6. **Your next move** — broker_next_step, bold, labeled "您的下一步"
7. **Collected / Still needed chips** — Green/orange

---

## 3. broker_next_step by Add-Car State

| State | broker_next_step pattern |
|-------|--------------------------|
| quote_ready + contact + attachment | "Run quote for {vehicle}. Materials received. Confirm delivery/driver with client before binding." |
| quote_ready + contact + no attachment | "Run quote for {vehicle}. Confirm delivery/driver with client before binding. Registration/dec page optional." |
| quote_ready + contact needed + attachment | "Run quote for {vehicle}. Materials received. Confirm name and phone for follow-up." |
| quote_ready + contact needed + no attachment | "Run quote for {vehicle}. Confirm delivery/driver. Confirm name and phone for follow-up. Registration/dec page optional." |
| almost_ready | "Collect {still_needed}. Then run quote." |
| need_more | "Ask for {missing}." |

**Concrete vehicle when available:** "Run quote for 2024 Tesla Model Y (zip 90210)" not "Run quote for collected vehicle."

---

## 4. Quote-Ready / Contact / Attachment / Correction Display

| Element | Treatment |
|---------|-----------|
| quote_ready_status | Tag with color; "Quote-ready" / "Almost ready" / "Need more" |
| contact | Block: "张三 · 555-1234" or "Name needed" / "Phone needed" |
| attachment | "📎 1" or "Materials received" / "Registration/dec page optional" |
| correction | Badge: "Customer corrected vehicle/zip/driver" — use latest |
| broker_next_step | Bold, larger font |

---

## 5. Queue Card Scan (List View)

Broker should prioritize from the list without opening every case. Queue cards must show:

| Signal | On Card |
|--------|---------|
| Case focus | ✓ |
| Quote-ready tag | ✓ (when add-car) |
| Contact status | ✓ (complete / needed) |
| Attachment badge | ✓ (count or none) |
| Correction badge | ✓ (when applicable) |
| broker_next_step preview | ✓ (truncated) |

---

## 6. What Should Be Secondary

- Full conversation (below fold or collapsible)
- Client prep
- Draft reply (editable but not primary scan target)
- Lifecycle status (tag, not primary)

---

## 7. What Should NOT Require Extra Clicking

- What the customer said last
- Whether they corrected something
- Whether contact is missing
- What is still needed
- What to do next

---

*See also: WORKBENCH_HANDOFF_PROFESSIONALIZATION_TRIAL_HARDENING/02_BROKER_SCAN_CASE_READABILITY_SPEC.md, 04_BROKER_NEXT_STEP_QUALITY_SPEC.md*
