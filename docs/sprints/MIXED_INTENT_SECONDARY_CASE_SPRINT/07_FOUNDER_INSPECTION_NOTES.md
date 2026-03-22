# Founder Inspection Notes

**Sprint:** Mixed-Intent + Secondary Case Strategy  
**Purpose:** What founder should inspect after this sprint; test cases; success looks like.

---

## 1. What to Inspect

| Area | What to check |
|------|---------------|
| **Same-goal corrections** | "不是 payment，是续保" → stays in one case; summary reflects correction |
| **Side questions** | "加车，顺便 garaging 是什么" → primary add-car; secondary noted |
| **Broker handoff** | conversation_summary has "Also asked" when mixed; broker_next_step clear |
| **Case focus** | One case = one main goal; no messy multi-goal dump |

---

## 2. Test Cases to Use

| ID | Message | Expected |
|----|---------|----------|
| MI-AC1 | 我想加一辆车，然后这个 garaging proof 又是什么？ | Add-car primary; document confusion in draft or note |
| MI-N2 | payment failed 怎么办，另外 dec page 我上周发过了 | Payment primary; document "already sent" in draft |
| MI-CL2 | 出事了要拍什么，还有这个 payment failed 通知什么意思 | Claim primary; notice confusion secondary |
| RC-S7 | 加车顺便 notice 什么意思 | Add-car primary; notice secondary noted |

---

## 3. Success Looks Like

- Primary intent is clear in every case
- When customer mixes goals, "Also asked" appears in summary
- Broker can tell what to do first
- Same-goal corrections do not cause split or confusion
- Founder can explain: "We handle mixed intent by keeping one main goal per case and noting the rest"

---

## 4. How to Run

```bash
# Guardrail
bash scripts/guardrail_inbox_triage.sh

# Mixed-intent simulation
PYTHONPATH=. python3 scripts/run_complex_adversarial_simulation.py --pack mixed_intent

# Demo
bash scripts/run_demo_local.sh
# Open /workbench/unified-intake; paste mixed-intent message
```

---

*End of Founder Notes*
