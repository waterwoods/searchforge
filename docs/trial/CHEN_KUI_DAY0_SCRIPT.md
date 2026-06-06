# Chen Kui Day 0 Script — 30-Minute Founder Session

**Purpose:** Supervised kickoff. Goal = **first successful paste → draft copied to WeChat**.  
**Audience:** Chen Kui (陈魁) + Andy (founder)  
**Materials sent before call:** [`BROKER_ONE_PAGER_V2.md`](../product_constitution/BROKER_ONE_PAGER_V2.md), [`PILOT_TERMS_V1.md`](./PILOT_TERMS_V1.md), workbench URL, blank [`TRIAL_OBSERVATION_LOG_V2.md`](./TRIAL_OBSERVATION_LOG_V2.md)

**Pre-flight (Andy, before call):**
```bash
bash scripts/trial_launch_check.sh    # must PASS
bash scripts/guardrail_inbox_triage.sh
```
Confirm broker can open URL (no SSO surprise — use local or broker-stable Preview).

---

## Minute-by-minute

### 0:00–2:00 — Open + frame

**Say (Chinese):**
> 陈哥，今天 30 分钟。目标很简单：你粘贴一条真实客户消息，看到整理好的 case 和草稿，复制到微信。  
> 7 天免费试用，不自动发送，你始终自己发。今天做完第一次，后面你自己用。

**Do:**
- Confirm he opened the URL and sees **办公室工作台**
- Point out: **不自动对外发送**

---

### 2:00–5:00 — What this is (not)

**Say:**
> 这不是 CRM，不连你的微信。你把客户原文粘贴进来，系统帮你整理：今天要不要处理、下一步、已经有什么、还缺什么、草稿。  
> 微信还是你发消息的地方。这个工具帮你省「读消息 + 从头写回复」的时间。

**Do:**
- Scroll briefly: paste box, queue, case detail
- **Do not** tour every button

---

### 5:00–8:00 — Demo queue (trust build)

**Say:**
> 我先加载演示队列，你看三条最常见的：取消、缺文件、加车。

**Do:**
1. Click **加载演示队列**
2. Open **cancellation** case first — point to:
   - Urgency / 今天要处理
   - Your next move / 下一步
   - Collected / Still needed
   - Draft reply
3. **30 seconds each** on missing-doc and add-car — same four points

**Say after cancellation:**
> 取消通知这种，Same-day 的排前面。你不用重新读整段微信。

---

### 8:00–18:00 — Scenario 1: Cancellation (real paste)

**Say:**
> 现在用你手机上一段真实的。最好是取消通知或付款失败。原样粘贴，不用整理。

**Do:**
1. Chen Kui copies a real WeChat message → paste
2. Wait for case output (~30–60 sec)
3. Walk through output together:
   - 「这个 focus 对不对？」
   - 「下一步合理吗？」
   - 「草稿能不能用？」
4. He edits draft if needed
5. **Copy draft → paste into WeChat (don't send yet, or send if he's comfortable)**

**Log in observation log:**
- Scenario: Cancellation
- Minutes saved: estimate together
- Draft copied?: Y/N
- Confidence before/after: 1–5

**If output wrong:** Don't defend. Say: 「这条我记下来，试用期间我改。你看其他字段有没有用。」

---

### 18:00–23:00 — Scenario 2: Missing document

**Say:**
> 第二条：缺文件。客户说「我发过了」或者 DMV 缺材料那种。

**Do:**
1. Demo queue → missing-doc case **OR** real paste if he has one
2. Highlight **Collected vs Still needed**
3. Copy draft with small edit

**Say:**
> 这种消息最怕重复问客户。这里一眼看到还缺什么。

**Log:** same fields as above.

---

### 23:00–27:00 — Scenario 3: Add-car quote

**Say:**
> 第三条：加车报价。客户零散发年份、车型、邮编。粘贴进来，看系统怎么收。

**Do:**
1. Demo queue add-car **OR** real multi-line WeChat paste
2. Show collected fields building up
3. Draft may need more edits — that's OK

**Say:**
> 加车通常要多轮。第一粘贴不一定完整，你可以追加新消息到同一个 case。

**Log:** same fields.

---

### 27:00–29:00 — Week plan + cancellation example (how to stop)

**Say:**
> 接下来 7 天：
> - 每天粘贴 1–3 条真实消息
> - 用这个表记录（发你了）— 特别是「省了多少分钟、草稿有没有复制」
> - 第 7 天我们聊 15 分钟，决定 $49 还是 $99，或者先不付费
>
> **怎么停止：** 试用期间随时停，不收费。付费后提前 7 天微信我说一声就行。你的 case 数据是你的，不付费保留 30 天可以导出。

**Do:**
- Send link to PILOT_TERMS_V1
- Confirm WeChat support: 24h 工作日回复

---

### 29:00–30:00 — Close

**Say:**
> 今天目标达到了吗？你复制过草稿了吗？  
> 明天再粘贴一条真实的，微信有问题随时发截图。

**Success = he copied at least one draft (demo or real) and understands paste → case → copy flow.**

---

## If things go wrong

| Problem | Response |
|---------|----------|
| URL won't load / SSO | Switch to Andy's screen share or local URL; fix deploy before Day 1 alone |
| Paste fails / slow | Use demo queue; log friction; promise fix within 24h |
| Draft unusable | Edit together; log as friction; still count partial value from structure |
| He expected WeChat sync | Reset with one-pager §4; if hard no → note fit risk |
| No real messages handy | Demo queue all three; schedule Day 1 for first real paste |

---

## Andy checklist (end of call)

- [ ] Chen Kui copied ≥1 draft
- [ ] Observation log v2 started (Day 0 row filled)
- [ ] PILOT_TERMS_V1 sent
- [ ] BROKER_ONE_PAGER_V2 sent
- [ ] Day 7 call time booked
- [ ] Friction logged if any

---

*End of Chen Kui Day 0 Script*
