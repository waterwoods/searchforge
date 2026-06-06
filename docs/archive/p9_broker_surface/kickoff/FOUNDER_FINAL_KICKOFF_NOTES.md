> **HISTORICAL / ARCHIVE — P9 Broker Surface Collapse (2026-05-30)**
> **Read instead:** [`docs/TRIAL_ONE_PATH.md`](../../../TRIAL_ONE_PATH.md)

# Founder Final Kickoff Notes

**Sprint:** Broker Trial Kickoff Readiness Sprint  
**Created:** 2026-03-18  
**Purpose:** What founder should inspect after this sprint, what to say to broker, what to do after first 3–5 real conversations.

---

## 1. What to Inspect After This Sprint

| Item | Where | What to verify |
|------|-------|----------------|
| Single entry | `bash scripts/trial_launch_check.sh` | PASS; prints checklist |
| Founder launch notes | `docs/trial/FOUNDER_LAUNCH_NOTES.md` | Read before first meeting |
| Broker one-pager | `docs/trial/BROKER_TRIAL_ONE_PAGER.md` | Bring to meeting |
| Observation log template | `docs/trial/TRIAL_OBSERVATION_LOG_TEMPLATE.md` | Copy for broker |
| Fix-now queue template | `docs/trial/FIX_NOW_QUEUE_TEMPLATE.md` | Post-trial: copy, fill, save to results/trial_logs |
| Kickoff docs | `docs/trial/kickoff/` | Blueprint, Flow Spec, Evidence/Issue Spec, Demo/Checklist |

---

## 2. What to Say to Broker (First 30 Seconds)

**Chinese:**
> "这是一个加州汽车保险经纪助手。客户发来messy消息——微信、截图、通知——系统会整理成一个结构化case：有 urgency、下一步动作、收集了什么、还缺什么、草稿回复。你确认后再发，**不自动发送**。经纪保持控制。"

**English:**
> "This turns messy customer messages into structured cases: urgency, next move, what's collected, what's still needed, draft reply. You review and send. No auto-send."

**One-sentence pilot offer:**
> 试用一个月：帮你把客户发来的messy消息整理成结构化case，有下一步动作、收集了什么、还缺什么、草稿回复。你确认后再发，不自动发送。

---

## 3. What to Do After First 3–5 Real Conversations

| Collect | Format |
|---------|--------|
| Friction | `[Date] [Scenario] Friction: [one line]` |
| What worked | Brief note |
| Broker confusion | What confused, what they expected |
| Value signal | "Which scenario felt most useful?" |

**Store:** Add to observation log; post-trial fill Friction Classification table.

**Post-trial flow:**
1. Copy observation log to `results/trial_logs/{broker}_{date}.md`
2. Fill Friction Classification table
3. Use `docs/trial/FIX_NOW_QUEUE_SPEC.md` — fix now / next / defer
4. Copy `docs/trial/FIX_NOW_QUEUE_TEMPLATE.md`; fill and save to results/trial_logs
5. Add fix-now items to next sprint backlog

---

## 4. If Something Goes Wrong

| Issue | Action |
|-------|--------|
| 503 / embedding_warming | `bash scripts/restore_8001_readiness.sh` |
| Guardrail fails | Fix per script output |
| Broker stuck | Switch to founder demo queue; show SIM1–SIM3 |
| Offline mode | Use Simulation Assistant |

---

## 5. Trust-Breaking vs Acceptable Friction (Quick Reference)

| Trust-breaking (fix now) | Acceptable friction (fix next or defer) |
|-------------------------|----------------------------------------|
| Broker says "I can't use this" | Manual evidence pack; no inbox sync |
| Talk to Agent routes wrong | Copy case snapshot works; minor UI polish |
| Next move always generic | Some scenarios need refinement |
| Broker can't find next move | — |

**Rule:** If broker would not use again → fix now. If "could be better" → fix next.

---

## 6. What to Watch For During First Few Real Conversations

| Watch for | Why |
|-----------|-----|
| Broker hesitates at paste | May not know what to paste; give example |
| Broker ignores Collected chips | May not trust; point out Human confirmation |
| Broker rewrites draft completely | Draft quality; note for iteration |
| Broker can't find next move | Visibility; may need UI tweak |
| Broker confused on reopen | Resume here; waiting_on clarity |
| Talk to Agent flow | If customer says "联系人工" — does it work? |
| Correction / already_sent | Does broker see when customer said "already sent"? |

---

*End of Founder Final Kickoff Notes*
