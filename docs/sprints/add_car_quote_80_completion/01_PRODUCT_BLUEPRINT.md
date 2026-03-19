# Add-Car Quote 80% Completion — Product Blueprint

**Sprint:** Add-Car Quote 80% Completion Sprint  
**Date:** 2026-03-16  
**Scope:** SearchForge → Chen Kui Insurance Unified Entry — Add-Car Quote flow only

---

## 1. Why Add-Car Quote Needs to Be Upgraded Now

The founder has identified a critical product truth: **the Add-Car Quote flow is too short (2–3 turns), too demo-like, and not rich enough to reflect real business needs.**

Today:
- It does not yet feel like a serious business flow
- It is not yet strong enough to hand over to Chen Kui and assistants for real use
- Making it configurable too early would expose an immature flow

The correct sequence is:
1. **First** make Add-Car Quote itself much stronger
2. Bring it to roughly **80% realistic completion**
3. **Then** make that mature flow configurable for business users

This sprint is Step 1.

---

## 2. Why the Old 2–3 Turn Flow Is Not Enough

| Current Reality | Problem |
|-----------------|---------|
| Typically 2–3 customer turns before handoff | Real offices often need 4–6 logical steps to prepare a usable quote |
| Collects: year, model, zip, delivery, driver, VIN | Missing: insurance status, additional drivers, coverage direction, new-purchase context |
| Handoff threshold: (year+model or VIN) + (zip or delivery or driver) | Too permissive — zip alone is often not enough for a good quote |
| First-turn template lists 6 items at once | Overloads user; doesn't guide step-by-step |
| No "next best question" for insurance status | Office can't tell new customer vs add-to-existing without asking |
| No "additional drivers" branch | Common real-world case; office has to chase later |

---

## 3. What "80% Completion" Means

**80% completion** = the flow feels like what a real small insurance office would do before preparing a quote or handing off to the office. It is:

- **Richer:** Knows and can collect 7–8 logical information categories (not necessarily all every time)
- **Smarter:** Asks the next best question; continues naturally; does not hand off too early
- **More useful:** The resulting case gives the broker enough to act without excessive back-and-forth
- **Not enterprise:** Not a full underwriting engine; not every edge case; not configurable yet

**Concrete 80% bar:**
- Flow supports ~7–8 logical steps (zip, vehicle, new-purchase, insurance status, additional drivers, driver profile, coverage direction, handoff)
- Not every run needs every step — system asks next best missing info
- Handoff happens at a meaningful point (enough for office to quote or escalate)
- 4–5 turns typical for partial-info entry; 1–2 turns when user gives full info upfront

---

## 4. What This Sprint Will and Will Not Do

| Will Do | Will NOT Do |
|---------|-------------|
| Strengthen default Add-Car flow depth | Build a configurable flow builder |
| Add insurance_status and additional_drivers slots | Add full underwriting logic |
| Improve next-best-question order | Support every carrier's custom fields |
| Extend handoff threshold when useful | Make flow configurable per client |
| Add coverage_preference (light touch) | Integrate with carrier quote APIs |
| Improve first-response quality | Change other flows (remove-car, claim, etc.) |

---

## 5. Success Criteria (High Level)

- Add-Car Quote feels **much closer** to real office intake
- Flow continues **longer** when useful (4–5 turns for partial info)
- Handoff happens at a **meaningful** point, not too early
- Case summary is **more useful** for broker
- No regression on existing scenarios (inbox triage, multi-turn sims)

---

*See also: 02_ADD_CAR_FLOW_DESIGN_SPEC.md, 03_CONVERSATION_SLOT_COLLECTION_SPEC.md*
