# P16 Customer First Constitution Review

**Sprint:** P16-CUSTOMER-FIRST-CONSTITUTION-P0  
**Date:** 2026-06-07  
**Subject:** `P16_CUSTOMER_FIRST_CONSTITUTION.md`  
**Method:** Four-role review — Customer, Office Assistant, Broker, Founder

---

## 1. Customer

### Is it simple?

**Yes.** Seven rules map to how customers already behave: open a link, type car info, give phone, come back with same phone. No login, no app download, no case-ID memorization.

**Risk:** Until Phase 2 ships, phone return key is a promise not yet kept — customers may still lose progress on new browser/session.

### Is it useful?

**Yes.** The three questions (submitted? missing? contact?) match real WeChat anxiety after sending vehicle photos.

### What could still go wrong?

- Customer enters wrong phone digit — returns to empty or wrong case (needs validation + broker fix path).
- Customer shares spouse’s phone — two people, one key (broker must confirm identity).
- “When will someone contact me?” — constitution does not define SLA; empty promise if copy is vague.
- Customer tries second add-car while first is open — needs clear broker-mediated fork, not silent duplicate.

### What must be built next?

1. Name + phone on first screen (Phase 1).
2. Phone lookup → show active case + missing fields (Phase 2).
3. Block formal submit without phone (Phase 3).
4. Plain-language status: submitted / not submitted / waiting on office.

### What should NOT be built yet?

- SMS verification
- WeChat login
- Case picker with multiple open cases
- Customer self-close
- Full portal with history tabs

---

## 2. Office Assistant

### Is it simple?

**Yes.** Progress = missing fields aligns with how assistants already scan Chen Kui packets. Ten-second goal matches desk workflow.

### Is it useful?

**Yes.** Phone on every formal submit means the desk can call back without broker relay. One active case reduces duplicate queue entries.

### What could still go wrong?

- Cleanup backlog: old demo cases may pollute phone lookup until Phase 4.
- Formal submits without phone today still reach queue — assistant wastes time on no-contact cases.
- Missing fields on customer surface must match workbench exactly or assistant re-asks answered questions.

### What must be built next?

1. Formal submit phone gate (Phase 3).
2. Office glance unchanged but fed by cleaner phone-keyed records.
3. Postgres dedupe before pilot (Phase 4).

### What should NOT be built yet?

- OCR as primary intake
- CRM client matching automation
- Multi-case merge UI for assistants
- Payment status integration

---

## 3. Broker (Chen Kui)

### Is it simple?

**Yes.** Broker keeps control: confirms identity, closes/reopens, final action. Customer path reduces paste load but does not remove broker confirmation.

**Partial tension:** Broker paste path remains valid — constitution must not be read as “customers only, no paste.”

### Is it useful?

**Yes.** Customer self-serve for add-car fields + phone return reduces WeChat ping-pong. Broker 30-second confirm goal fits supervised pilot.

### What could still go wrong?

- Customer submits incomplete case formally if phone gate lags behind vehicle gate.
- Broker may not notice claimed vs confirmed phone — needs workbench badge, not auto-trust.
- One active case rule may block legitimate “two cars same week” — broker close/split SOP required.

### What must be built next?

1. Customer first screen + phone lookup (Phases 1–2).
2. Workbench copy: claimed contact vs broker-confirmed.
3. Explicit close/reopen before new add-car for same phone.

### What should NOT be built yet?

- WeChat bot forwarding
- Auto-quote without broker confirm
- Stripe / billing in product
- Multi-broker tenant isolation

---

## 4. Founder

### Is it simple?

**Yes.** Constitution replaces scattered Z17/Z18 customer-builder notes with seven enforceable rules. Phase order is linear: docs → screen → lookup → gate → cleanup → pilot.

### Is it useful?

**Yes.** Reverses `P16Z25_90_DAY_ROADMAP` “customer-first after retention” rejection — appropriate now that broker loop is proven. Positions P16 as product, not paste tool.

### What could still go wrong?

- **Doc/code drift:** Engineers follow master outline §3.2 many-records policy until updated — constitution must be linked from AGENTS path.
- **Scope creep:** WeChat OAuth code already in tree — temptation to “just enable” instead of phone lookup.
- **Cleanup timing:** Too early cleanup breaks demos; too late breaks phone lookup pilot.
- **Pilot re-run:** Chen Kui may expect paste-first — needs explicit “customer link” SOP.

### What must be built next?

1. Phase 1 implementation sprint (customer first screen).
2. Update ui_copy for three customer questions.
3. Phase 4 cleanup criteria doc before running DELETE-class ops.

### What should NOT be built yet?

- P17 platform
- SMS OTP
- Second office onboarding
- Score inflation without cold-URL customer walkthrough

---

## Cross-Role Verdict

| Role | Constitution approval | Blocker to trust runtime |
|------|----------------------|---------------------------|
| Customer | **Approve** (as target) | Phone lookup not built |
| Office Assistant | **Approve** | Phone gate + data cleanup |
| Broker | **Approve** | Identity confirm UX |
| Founder | **Approve** | Implementation Phases 1–3 |

**Constitution document:** Ready to serve as SSOT.  
**Product runtime:** Not yet Customer First — see gap review.

---

*End of P16 Customer First Constitution Review*
