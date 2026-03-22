# Mixed-Intent Strategy Blueprint

**Sprint:** Mixed-Intent + Secondary Case Strategy Sprint  
**Scope:** SearchForge → Chen Kui Insurance Unified Entry  
**Created:** 2026-03-19

---

## 1. Why Mixed-Intent Handling Matters Now

The product is strong in:
- Scenario package, client-aware wiring, state/workflow backbone
- Case/handoff/workbench, trial package, scenario logic center
- Broker trial simulation

But one important real-world behavior remains under-defined: **customers often switch topics, insert side questions, ask "顺便问一下", or mix multiple goals in one conversation.**

If not handled well:
- Case summaries become messy
- Broker follow-up gets harder
- Trial confidence drops
- The system feels brittle in realistic use

---

## 2. Why This Is the Right Move After Current Trial Hardening

- Trial pack and simulation hardening are in place
- Scenario Logic Center gives visibility into what exists
- The next valuable move is a **practical** mixed-intent and secondary-case strategy
- Not a perfect multi-threaded engine — a disciplined first version

---

## 3. What This Sprint Will Strengthen

| Area | Strengthen |
|------|------------|
| **Primary vs secondary intent** | Define and make visible |
| **Same-goal corrections** | Stay in current case |
| **Different-goal side questions** | Mark or split |
| **Broker handoff** | Clearer when conversation contains multiple goals |
| **Founder explainability** | How the system handles topic switching |

---

## 4. What This Sprint Intentionally Will NOT Do

| Deferred | Reason |
|----------|--------|
| Full concurrent conversation graphs | Overbuild; not V1 |
| Giant memory systems | Overbuild |
| Solve all conversational ambiguity | Unrealistic |
| Merge unrelated business goals into one case | Violates one-case-one-goal |
| Automatic split for every side question | Broker-friendly fallback: mark first, split only when justified |

---

## 5. Core Principle

**One case = one main business goal.**

- Same-goal clarification/correction → keep in current case
- Different-goal side question → mark secondary issue or split to another case
- Explicit user topic switch → allow main intent switch if justified

Do NOT allow one case to become an unstructured bag of unrelated requests.

---

## 6. V1 Behavior Targets

| Good V1 | Avoid |
|---------|-------|
| Detect side-question markers: 顺便问一下, 对了, 另外, 还有一个问题 | Full concurrent graphs |
| Detect likely second business goal | Giant memory systems |
| Preserve current main case when appropriate | Overly complex automation |
| Attach secondary issue note or recommend second case | Hidden behavior no one can explain |
| Improve broker summary / next-step clarity | |

---

*End of Blueprint*
