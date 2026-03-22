# Founder Inspection Notes

**Sprint:** Broker Trial Simulation + Handoff Timing Audit  
**Purpose:** What founder should inspect after this sprint.

---

## What to Inspect

1. **Strongest handoff-timing flows** — Add-car with driver ask; talk-to-agent; vague no-handoff
2. **Weakest flows** — Premium T2 handoff when T3 adds remove-vehicle; missing doc T2 when T3 asks "是什么意思"
3. **Best fix-now candidates** — From simulation failures
4. **Best manual test cases** — Paste in Unified Intake; observe handoff turn

---

## Manual Test Cases That Matter Most

| Test | Paste | Expect |
|------|-------|--------|
| Vague | "帮我" | No handoff; ask clarifying |
| Talk-to-agent | "联系人工" | Handoff T1 |
| Add-car full | "2024 X5 90210 下周提车" | Handoff T1 |
| Add-car partial | "加车 2024 X5" then "90210 下周提车" | Ask driver or handoff T2 |
| Premium + remove | "续保涨了" then "账单发你了" then "2021 Accord 想拿掉" | Handoff T3 with vehicle |
| Missing doc + question | "要dec page" then "发你了" then "garaging 是什么意思" | Handoff T2 or T3; answer question |

---

## What to Watch During First Real Broker-Style Usage

- Does customer feel cut off?
- Does broker receive incomplete cases?
- Does broker need to re-ask what we already "collected"?
- Are corrections visible?

---

*End of Notes*
