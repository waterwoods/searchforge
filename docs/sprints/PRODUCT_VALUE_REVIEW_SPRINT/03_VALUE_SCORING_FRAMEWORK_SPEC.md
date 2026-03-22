# Value Scoring Framework Spec

**Sprint:** Product Value Review Sprint  
**Created:** 2026-03-19

---

## 1. Scoring Dimensions (1–10 each)

| Dimension | Definition | 1 = | 10 = |
|-----------|------------|-----|------|
| **Commercial value** | Helps trial adoption, paid pilot, revenue | No impact | Direct path to paid adoption |
| **Broker value** | Reduces rework, improves handoff, daily usefulness | No impact | Major daily time-saver |
| **Customer value** | Improves speed, clarity, trust for end customer | No impact | Clear customer benefit |
| **Reuse value** | Helps future client B/C without rework | None | Enables scaling |
| **Implementation cost** | Effort to do now (inverse: lower cost = higher score) | Very expensive | Trivial |
| **Risk / disruption** | Likelihood of breaking stable flows (inverse) | High risk | No risk |
| **Urgency / timing fit** | Right time to do it for trial | Wrong time | Perfect timing |

---

## 2. Scoring Conventions

- **Commercial value:** Trial adoption = 7–9; post-trial monetization = 5–7; no direct path = 1–4.
- **Broker value:** Reduces rework in handoff = 7–9; nice-to-have = 4–6; no impact = 1–3.
- **Customer value:** For broker-assistant, "customer" often = broker's client; indirect.
- **Reuse value:** Config extraction, client pack = 6–8; single-broker only = 1–3.
- **Cost:** 1–3 = high effort; 4–6 = medium; 7–10 = low.
- **Risk:** 1–3 = high disruption; 4–6 = medium; 7–10 = low/none.
- **Urgency:** Trial-ready now = 8–10; post-trial = 4–6; wrong time = 1–3.

---

## 3. Combined Priority Score

**Formula (simple):**

```
Priority = (Commercial × 2 + Broker + Customer + Reuse) / 5  —  (Cost_inv + Risk_inv) / 2  +  Urgency / 5
```

Where `Cost_inv = 11 - Cost` and `Risk_inv = 11 - Risk` (invert so lower cost/risk = higher contribution).

**Simpler alternative for ranking:**
- **Value score** = (Commercial + Broker + Customer + Reuse) / 4
- **Friction score** = (Cost + Risk) / 2  (higher = more friction)
- **Timing bonus** = Urgency / 10
- **Net** = Value − 0.3×Friction + 0.2×Timing

For founder readability, we use **explicit 1–10 scores** and **qualitative ranking** (top / mid / defer) rather than a single numeric formula. The formula is a sanity check, not the sole decider.

---

## 4. Bucket Definitions

| Bucket | Criteria |
|--------|----------|
| **Do now** | High commercial + broker value; low cost; low risk; right timing for trial |
| **Do next** | Important but not blocking; can follow trial or first sprint |
| **Defer** | Low ROI now; or high cost/risk; or wrong timing |

---

## 5. Trap Features (Explicitly Call Out)

A **trap feature** is attractive but low ROI for current stage:
- High technical interest, low commercial value
- Helps future scaling but not first paid pilot
- Expensive to do well; half-done = trust-breaking

---

## 6. High-Leverage Features (Explicitly Call Out)

A **high-leverage feature** is:
- Direct path to trial adoption or broker daily use
- Low cost, low risk
- Right timing (before or immediately after first trial)

---

*End of Scoring Framework Spec*
