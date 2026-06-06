# Fix-Now Decision Spec

**Sprint:** Founder / Broker Trial Execution Sprint  
**Created:** 2026-03-20

---

## 1. How to choose what to fix

1. List issues from Loop 1 with backbone tags (Page / Flow / State / Handoff).  
2. Mark **trust** impact: none / low / medium / high.  
3. Mark **effort**: trivial / small / medium / large.  
4. Select only items where **trust ≥ medium** and **effort ≤ small**, unless trivially blocking (e.g. broken API contract).

---

## 2. Worth fixing immediately

- Validation or API behavior that **lies to the operator** (false pass/fail).  
- Persistence / append path inconsistent with documented guardrails.  
- `broker_next_step` systematically vague in a **high-frequency** scenario (Add-Car, missing doc, payment).  
- Customer-visible copy that reads **demo-internal** on a primary path.

---

## 3. Leave alone (even if imperfect)

- Edge-case wording on rare intents.  
- Missing fields that broker would always confirm verbally.  
- Features explicitly out of scope (OCR, rating, CRM).  

---

## 4. Stop rule

After **one or two** fix-now items, return to retest. No third fix unless a regression appears.

---

*End of Fix-Now Decision Spec*
