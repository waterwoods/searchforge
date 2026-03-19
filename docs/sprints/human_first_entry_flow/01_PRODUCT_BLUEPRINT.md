# Human-First Entry Flow + Startup Latency Audit — Product Blueprint

**Sprint**: Human-First Entry Flow + Startup Latency Audit  
**Created**: 2026-03-15  
**Scope**: Chen Kui Insurance Unified Entry — Customer Entry + Broker Workbench

---

## 1. Why This Sprint Matters Now

The founder reports that the Unified Entry still feels:
- **Too mechanical** — generic "内容不够完整" when the user clearly asked for a quote
- **Buttons are passive** — clicking does not start a flow; user must still type
- **No visible structure** — customer and office don't see a live case summary forming
- **First interaction feels slow** — cold start / first click latency unclear

This sprint upgrades the entry experience so it feels like a **human helper**, not a rigid form.

---

## 2. Why "Answer First, Then Ask One Missing Thing" Is Right

| Current problem | Desired behavior |
|-----------------|------------------|
| User: "我才买了一个2026年的丰田花冠，我想问一下，大约半年的保费是多少？" | System should say: "好的，2026年丰田花冠，我来帮您看报价。先把地址邮编发我，我就能帮你算。" |
| System says: "内容不够完整" | System acknowledges intent, then asks only the next missing field (zip) |
| Asks 5 fields at once | Asks 1–2 next things max |
| Sounds like a form | Sounds like an office assistant |

**Principle**: The system must first show "I understood what you are asking" before asking for more. Never lead with generic "information incomplete" when intent is clear.

---

## 3. Why Buttons Must Become True Starters

| Current | Target |
|---------|--------|
| Click "获取报价" → only sets a tag | Click "获取报价" → system immediately begins quote flow |
| User must type after clicking | System proactively returns first reply: "好的，我来帮您看新车报价。先把年份和车型发我，我就能帮你算。" |
| Button is passive context | Button triggers real first step |

**Implementation**: On button click with empty input, auto-submit a minimal starter message that triggers the right flow. The backend returns the natural first reply for that intent.

---

## 4. Why Live Case Summary Helps

| Who | Benefit |
|-----|---------|
| **Customer** | Sees the system is organizing their request in real time; feels structured, not chaotic |
| **Office** | Gets a draft summary that updates as intake progresses; less manual reading |
| **Trust** | Both sides see intent + collected + still needed; reduces "did it understand me?" anxiety |

The summary does not need to be perfect. It needs to be **useful** and **visible**.

---

## 5. Why Startup Latency Still Matters

First impression is critical. If the first interaction feels slow:
- User may assume the system is broken
- Founder demo feels sluggish
- Cold start (backend, embedding, LLM) vs frontend vs routing must be clearly identified

**Audit goal**: Document what is likely frontend delay, backend/cold-start delay, routing/LLM delay, and the best next optimization direction.

---

## 6. Design Principle (Non-Negotiable)

**Do NOT open broad new scope. Do NOT redesign the whole system.**

This sprint is about making the entry flow feel human, direct, and useful — within the existing architecture.

---

*See also: UX/Interaction Design Spec, Execution Outline, Acceptance/SLA Criteria, Startup Latency Audit Notes*
