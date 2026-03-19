# Scenario Selection Spec — Package 2.0

**Sprint:** Standard Scenario Package 2.0  
**Purpose:** Choose the 3–5 scenarios for deepening in this sprint.

---

## 1. Chosen Scenarios (5)

| # | Scenario | Business Value | Why in Package Core | Already Strong | Needs Strengthening |
|---|----------|----------------|---------------------|----------------|----------------------|
| 1 | **Quote / Add-car** | New vehicle quote; revenue; high-frequency | Most common broker intake | Recognition, first reply, multi-turn field collection | Summary "Collected" clarity; broker_next_step when partial info; handoff phrase consistency |
| 2 | **Material collection / already sent** | Missing document; client says already sent; common pain | Reduces broker rework; high friction today | Recognition, first reply, "already sent" handoff phrase | Summary when 2+ items; "still needed" when client says sent one; broker verification guidance |
| 3 | **Renewal increase / premium review** | Premium too high; retention | High-value retention flow | Recognition, first reply | Handoff when client sends bill; summary "policy/bill sent"; broker_next_step clarity |
| 4 | **Payment / cancellation risk** | Same-day action; lapse prevention | Urgent; broker must act fast | Recognition, urgency, first reply | "Already paid" handling; broker_next_step when client says paid; summary clarity |
| 5 | **Talk to Agent / case handoff** | Customer wants human; broker takes over | Completes the package; trust signal | Free-text detection | Mid-flow detection (e.g. after add-car); handoff timing; draft mentions office |

---

## 2. Deferred Scenarios (Not in This Sprint)

| Scenario | Why Deferred |
|----------|--------------|
| Policy change (remove vehicle) | Already strong; lower priority than add-car and material collection |
| Billing clarification | Strengthens premium/payment chain indirectly; not standalone deepen |
| Claim first notice | Lower frequency; first-response guidance already good |

---

## 3. How Each Chosen Scenario Reduces Broker Effort

| Scenario | Broker Effort Reduction |
|----------|--------------------------|
| Add-car | One paste → structured case with year, model, zip, delivery; broker gets "Collected" chips; fewer "what did they say?" questions |
| Material / already sent | Summary says "dec page resent, garaging still needed" or "client says sent both—verify receipt"; broker knows exactly what to check |
| Renewal premium | Summary says "policy/bill sent"; broker_next_step: "Review renewal notice and quote options"; no re-asking for bill |
| Payment / cancellation | Summary says "client says paid—verify with carrier"; broker_next_step: "Confirm payment received; if not, process today"; urgency clear |
| Talk to Agent | Draft mentions office/陈奎; broker knows customer wants human; no confusion |

---

*End of Scenario Selection Spec*
