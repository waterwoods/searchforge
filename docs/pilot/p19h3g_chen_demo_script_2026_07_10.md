# P19H-3g — 陈总演示脚本（WeCom Broker Intake Copilot）

**Date:** 2026-07-10  
**Audience:** 陈总（经纪人）+ 办公室协助演示  
**Duration:** ~15–20 分钟  
**Workbench:** https://ui-smoky-beta.vercel.app/workbench/unified-intake  
**定位:** 微信原生事故资料收集助手 — **不是** 保险公司报案系统、不是 CRM、不是定责系统

---

## 演示前准备（2 分钟）

| 项 | 说明 |
|----|------|
| 演示微信 | 用**干净测试客户**或同事微信号（避免旧 case 干扰） |
| 陈总浏览器 | 打开 Workbench，登录办公室账号 |
| 话术准备 | 强调：「这只是帮陈总整理资料，不代表已向保险公司报案」 |
| 已知限制 | Cloud Run 若未开 `WECOM_SLICE_SEND_REPLY`，End Card 可能仅 preview；可口头说明「客户会收到这条确认」 |

---

## Scene 1 — 客户正式开始事故记录

### 客户操作（企业微信）

发送：

```text
我要理赔
```

### 预期系统反应

- 收到 **Start Card**（带 `━━━━━━━━━━━━` 边框）
- 标题：`【事故记录已开始 ✅】`
- 内容包含：
  - 陈总办公室值班助手
  - **有没有受伤？**（快捷按钮：没有受伤 / 有人受伤 / 不确定）
  - 提醒：**这不代表已经向保险公司正式报案**

### 跟陈总解释

> 「客户必须明确说『我要理赔』，系统才正式开始一份事故记录。随便发照片不会进您的工作台，避免混乱 case。」

### 可选：点「没有受伤」

客户点击 **没有受伤** → 受伤情况记入 timeline。

---

## Scene 2 — 客户补充事故经过 + 查进度

### 客户操作

发送：

```text
没有人受伤。昨天7月8号晚上，在 Santa Ana 红绿灯，我们停着，后车没停撞上来。我的车是 Honda。
```

### 预期系统反应

- 事故时间、地点、经过写入 case timeline
- 基本信息齐全后可能出现 framed **【事故信息已记录 ✅】**（C1 阶段完成卡）
- Workbench 出现 **Claim · 记录中** 行

### 客户再问进度

发送以下任一：

```text
进度
```

或 `状态` / `理赔进度`

### 预期系统反应

- **Status Card** — `【当前状态】`
- 显示：状态 / 客户 / 事故时间·地点 / **已收到** / **还缺** / **下一步**
- **不会**新建第二份 Claim
- **不会**再发 Start Card

### 跟陈总解释

> 「客户不用反复问『还要什么』。回复『进度』，系统自动告诉他已收到什么、还缺什么、下一步做什么。您不用每条微信都回同样的话。」

---

## Scene 3 — 客户发照片

### 客户操作

发送 **一张车损或现场照片**（任意测试图即可）。

### 预期系统反应

- 短确认（不是完整 Status Card）
- 照片绑定到**当前 active Claim** 的 timeline（`customer_photo`）
- **不会**进入 Raw Inbound 默认队列

### 跟陈总解释

> 「照片自动归到这份事故记录里，不会丢在微信聊天记录里。您打开 Workbench 就能看到有几张照片、还缺什么。」

### 可选验证

客户再发 `进度` → Status Card 的「已收到」应显示照片数量。

---

## Scene 4 — 已有 Claim 时提到新事故（Collision Resolver）

### 前置

Scene 1–3 的 Claim 仍在收集中（未 broker_done）。

### 客户操作

发送：

```text
今天又有一个新的事故，我在 Costco 停车场被刮了。
```

### 预期系统反应

- **Collision Resolver Card** — `【请选择事故记录】`
- 三个选项：
  1. 继续上一个事故，补充资料
  2. **开始新的事故记录**
  3. 联系陈总
- 系统**不会**静默把两次事故混在一起

### 演示选择

点击或回复：**开始新的事故记录**（或回复 `2`）

### 预期结果

- 新建第二份 Claim
- 再次收到 framed **Start Card**
- 第一份 Claim 仍独立存在

### 跟陈总解释

> 「系统不会猜。客户提到新事故，必须选是继续旧的，还是开新记录。这样 Costco 和 Santa Ana 不会混成一份。」

---

## Scene 5 — 陈总打开 Workbench 并结束收集

### 陈总操作

1. 打开 https://ui-smoky-beta.vercel.app/workbench/unified-intake
2. 在 **Office Review Queue** 找到 Claim 行（如 `Claim · 记录中 · Broker Review pending`）
3. 点击打开 **Drawer**
4. 阅读：
   - **Claim Case Brief**（摘要）
   - **Highlights**（重点：受伤、缺失项、照片等）
   - **Missing info**（还缺什么）
   - **Next step / next_best_question**
5. 确认资料足够后，点击 **Broker Done**（陈总已确认 / 结束收集）

### 预期系统反应

- API `POST .../broker-done` → 200
- 客户侧（若 WeCom send 已配置）：**End Card**
  - `【陈总已确认 ✅】`
  - 收集阶段已结束
  - 提醒：不代表保险公司结案或赔付
- Workbench：case 从**活跃队列移除**，状态变为 `Claim · 已确认 / 已交接`
- 再次点击 broker_done → idempotent，不重复 timeline

### 跟陈总解释

> 「您不用从几十条微信里翻。打开一行，10 秒内能看到：什么时候、哪里、怎么回事、有什么照片、还缺什么。点『确认完成』，客户收到正式结束通知，收集阶段结束 — 但这不是向保险公司报案，也不是赔付结果。」

---

## 演示收尾话术（给陈总）

1. **产品是什么：** 微信里的资料收集 Copilot，帮办公室整理事故记录。
2. **产品不是什么：** 不替客户报案、不定责、不判断 coverage、不自动联系保险公司。
3. **客户怎么开始：** 必须说「我要理赔」— 不是发照片就自动开始。
4. **客户怎么查进度：** 回复「进度」— 不用等您逐条回复。
5. **两次事故怎么办：** 系统让客户选，不会混案。
6. **您怎么收尾：** Workbench 看 Brief → Broker Done → 客户 End Card。

---

## 常见问题（演示 Q&A）

| 问题 | 回答 |
|------|------|
| 客户只发照片没说理赔？ | 只收技术记录，不进您默认队列；引导客户说「我要理赔」 |
| 客户以为已经报给保险公司了？ | 每张卡都有 disclaimer；可再口头强调 |
| End Card 客户没收到？ | 检查 Cloud Run `WECOM_SLICE_SEND_REPLY`；preview 在 API 已验证 |
| Workbench 看不到 case？ | 确认客户是否完成 Start Ceremony；刷新队列 |
| 名字显示「微信客户」？ | 当前版本未自动提取微信昵称；不影响 Brief 内容 |

---

## 相关

- 审计报告：`docs/pilot/p19h3g_pilot_readiness_audit_chen_2026_07_10.md`
- 上线清单：`docs/pilot/p19h3g_pilot_launch_checklist_2026_07_10.md`
