# Demo Audit — Founder Pitch & Demo Scripts

**Sources:** BROKER_DEMO_FLOW.md, DEMO_STORY.md, FOUNDER_ONE_PATH.md, live UI (UnifiedIntakePage, BrokerWorkbenchTab)

**Verdict:** Founder **can** explain the product at all three lengths **if** they stay on the workbench tab and use the cancellation → missing doc → add-car sequence. **Cannot** reliably deliver the documented 15-minute demo if they follow the UI default (Customer Entry / Add-Car-first) without redirecting.

---

## Can founder explain in 15 / 60 / 5 minutes?

| Length | Can explain? | Gap |
|--------|--------------|-----|
| **15 seconds** | Yes | Must memorize one sentence; UI won't teach it |
| **60 seconds** | Yes | Need to switch to 办公室工作台 + load demo queue first |
| **5 minutes** | Yes | Cancellation + add-car chips sufficient |
| **15 minutes** | Yes with rehearsal | Risk: wrong tab, slow queue load, Simulation backup unavailable in product-only |

---

## BEST_15_SECOND_PITCH

**Chinese (recommended for Chen Kui):**

> 客户微信发来乱糟糟的消息，你粘贴进来，系统帮你整理成一条服务记录：今天要不要处理、你下一步做什么、已经有什么、还缺什么、还有草稿回复。你改完复制到微信发，**不会自动发送**。

**English:**

> Paste messy customer messages — get one structured case with urgency, your next step, what's collected, what's missing, and a draft reply. You review and send. Nothing goes out automatically.

---

## BEST_60_SECOND_PITCH

**Say:**

> 这是给加州车险办公室用的。客户发通知、付款失败、补材料、加车报价——都可以原样粘贴，不用先整理。
>
> 系统会告诉你：这件什么事、紧不紧急、你办公室下一步做什么、客户已经给了什么、还缺什么，并给一条草稿让你改完复制到微信。
>
> **不连微信，不自动发送。** 你先试用一周，看能不能省下每天翻聊天记录和重复问客户的时间。

**Do (20 sec):** Open `/workbench/unified-intake` → click **办公室工作台** → **加载演示队列** → point to cancellation case → point to **下一步** and **已收集** chips.

**Ask:** "你们办公室周一早上最先要处理的是取消风险还是加车报价？"

---

## BEST_5_MINUTE_DEMO_SCRIPT

| Time | Beat | Script / action |
|------|------|-----------------|
| 0:00–0:30 | **Promise** | Use 60-second pitch opening sentence only |
| 0:30–0:45 | **Navigate** | 办公室工作台 tab → **加载演示队列** (warn: may take 20 sec) |
| 0:45–2:00 | **Urgency** | Open **取消/付款风险** case → show 当日处理 → read **下一步** aloud → show draft |
| 2:00–3:30 | **Operations** | Open **材料补交** from queue → show 在等客户 / 需核实收到 → **更新客户新消息** if time |
| 3:30–4:30 | **Revenue** | Open **加车报价** → **已收集 / 还缺** chips → "不用在脑子里记缺什么" |
| 4:30–5:00 | **Control + close** | Edit draft → "复制到微信" gesture → ask: "哪个场景最像你们办公室？还有什么不放心？" |

**Skip unless asked:** 客户报送 tab, 我的办理, 场景仿真, `/demo`, PG tags, case IDs.

**Backup if API slow:** Pre-loaded demo queue only — do not promise Simulation Assistant on production product-only UI.

---

## Demo anti-patterns (stop saying)

- "Connected to WeChat/email"
- "Reads your screenshots"
- "Automatically sends"
- "Full CRM"
- "SIM1" / "triage pipeline" / "vectors"

---

## Doc vs UI alignment gap

| Docs say | UI does |
|----------|---------|
| Open workbench, load founder demo queue | Default tab = 客户报送 |
| Cancellation first | Add-Car-first pilot intro |
| Simulation Assistant Day 1 | Tab hidden when `VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1` |
| "Broker Workbench" | 办公室工作台 |
| "Load founder demo queue" | 加载演示队列 |

**Recommendation:** Founder demo SOP adds step 0: "Click 办公室工作台 before speaking."

---

*End of demo audit*
