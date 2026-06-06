# Trial Scenario Pack Spec — Founder / Broker Execution Sprint

**Sprint:** Founder / Broker Trial Execution Sprint  
**Created:** 2026-03-20

---

## 1. Purpose

Define a **realistic scenario pack** for end-to-end trial execution: customer path + workbench inspection + classification. Each scenario includes **customer input sequence**, **expected system behavior**, and **what the founder/broker must inspect**.

Execution may combine: Unified Intake UI, `scripts/run_multi_turn_simulations.py`, `scripts/run_broker_trial_stress_simulations.py`, `scripts/run_handoff_timing_simulations.py`, `scripts/run_simulation_assistant_scenarios.py`, and API checks when a server is available.

---

## 2. Core scenarios (minimum set)

### S1 — Add-car normal

| Step | Customer input (example) | What should happen | Founder inspects |
|------|----------------------------|--------------------|------------------|
| 1 | 想加一台新车，下周提车 | Asks for year/model/zip/delivery (or structured chips) | Draft is Chinese-forward; not generic “provide more” |
| 2 | 2024 Tesla Model Y | Still collecting if zip/delivery missing | `still_needed_fields` sensible |
| 3 | ZIP 90210，下周一提车 | Moves toward quote-ready / handoff when rules satisfied | `quote_ready_status`, `broker_next_step` concrete |

### S2 — Add-car + contact missing

| Step | Customer input | What should happen | Founder inspects |
|------|----------------|--------------------|------------------|
| 1–3 | Full vehicle + zip + delivery, **no** name/phone | May hand off with quote-ready but contact gaps | Workbench shows contact hint; `broker_next_step` mentions confirming name/phone |

### S3 — Add-car + materials sent

| Step | Customer input | What should happen | Founder inspects |
|------|----------------|--------------------|------------------|
| 1–2 | Vehicle details + 「材料发你微信了」 | Warmer handoff copy; materials verification | `broker_next_step` includes verify materials / office follow-up |

### S4 — Add-car + correction

| Step | Customer input | What should happen | Founder inspects |
|------|----------------|--------------------|------------------|
| 1 | 宝马X5 … | Baseline collection | Collected model |
| 2 | 不是X5是X3 | Correction absorbed | `collected_fields` / summary reflect X3 |

### S5 — Missing document + already_sent

| Step | Customer input | What should happen | Founder inspects |
|------|----------------|--------------------|------------------|
| 1 | UW要 dec page + garaging | Structured still-needed | Chips present |
| 2 | 客户说上周发过了 | Handoff; verify-with-carrier flavor | `still_needed_fields` includes verify-style items where appropriate |

### S6 — Cancellation risk

| Step | Customer input | What should happen | Founder inspects |
|------|----------------|--------------------|------------------|
| 1 | payment failed / 要取消 | `urgency` high/critical path | Same-day broker tone |
| 2 | 发了截图 | Handoff with receipt verification | `broker_next_step` actionable |

### S7 — Premium review / remove vehicle

| Step | Customer input | What should happen | Founder inspects |
|------|----------------|--------------------|------------------|
| 1 | 续保太贵，一辆车去掉会便宜吗 | Renewal + removal interest | `broker_next_step` mentions renewal/options/removal |

### S8 — Talk to agent / escalation

| Step | Customer input | What should happen | Founder inspects |
|------|----------------|--------------------|------------------|
| 1 | 联系人工 / 找陈奎 | Immediate `customer_requested_human`, handoff | Client-facing draft names office appropriately |

### S9 — Mixed-intent (side question)

| Step | Customer input | What should happen | Founder inspects |
|------|----------------|--------------------|------------------|
| 1 | 加车 + garaging proof 是什么？ | Primary intent add-car; brief doc answer + handoff | No abandonment of add-car; secondary note if present |

### S10 — Mixed-intent (premium + notice)

| Step | Customer input | What should happen | Founder inspects |
|------|----------------|--------------------|------------------|
| 1 | 保费太贵 + 英文 notice 看不懂 | Triage picks primary or structured secondary | Broker can see both threads in summary/secondary |

---

## 3. Recommended execution order

1. S1 → S2 → S3 → S4 (Add-Car backbone)  
2. S5 → S6 (operational trust)  
3. S7 → S8 (retention + human)  
4. S9 → S10 (mixed stress)  

---

## 4. Pass / concern signals

- **Pass:** Founder can state the next office action in one sentence without opening code.  
- **Concern:** Generic `broker_next_step`, wrong urgency, or customer copy that sounds like an internal ticket.  

---

*End of Trial Scenario Pack Spec*
