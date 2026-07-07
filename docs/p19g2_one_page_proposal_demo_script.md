# P19G-2 — One-page Proposal + 15-Minute Demo Script for Chen Kui Insurance

**Date:** 2026-07-07  
**Type:** Sales materials — **documentation only**  
**Audience:** Andy (founder) → Chen Kui (CKS / 金盾保险)  
**Prerequisite:** P19E-2 Progress Card ✅ · P19F-1 Workbench Drawer UX Polish ✅ · P19G-0 Actual Cost Gap ✅ · P19G-1 Pricing / Pilot Package Recon ✅  
**Related:** `p19g1_pricing_pilot_package_recon.md` · `p19g0_actual_cost_gap_cost_model_recon.md` · `p19e3_channel_strategy_wecom_h5_miniprogram_recon.md`

**This loop:** No code. No deploy. No config change. No OCR. No mini program. No payment integration.

---

## 1. Executive Summary

P19G-2 把 P19G-1 的定价与包装结论，落成**可直接给陈总看的中文 one-page proposal** 和 **15 分钟 live demo 脚本**。

| Question | Answer |
|----------|--------|
| **我们在卖什么？** | **微信里的 Insurance Case Builder / Intake OS** — 不是 chatbot |
| **核心卖点？** | 客户不用下载 App、不用小程序，在微信里完成 guided workflow；系统像 Spark Driver 一样一步一步引导，最后把杂乱信息整理成陈总可处理的 case |
| **推荐试点价格？** | **$699/month**（首月可用 $599 friendly start） |
| **试点周期？** | **45 天**，1 个办公室，只做 Add Vehicle |
| **Demo 时长？** | **15 分钟** — 问题 framing → 客户端 → 文字收集 → 经纪人端 → 商务收尾 |
| **本轮代码变更？** | **无** |

**给陈总的一句话：**

> 客户在微信里把加车资料交齐，系统帮你整理好；你确认后再办事，不会自动改保单。

---

## 2. One-page Proposal for Chen Kui

> 以下可直接打印或微信转发给陈总。业务语言，非技术文档。

---

# 微信加车资料收集试点

**把客户微信里的零散资料，自动整理成经纪人可处理的保险 case。**

**致：陈总 · 金盾保险（CKS）**  
**试点周期：45 天 · 推荐价格：$699/月（首月 $599）**

---

### A. 当前痛点

| 痛点 | 日常表现 |
|------|----------|
| 资料分散在微信聊天里 | VIN、行驶证、保险卡、提车日期、ZIP、电话散落在不同气泡里 |
| 经常漏资料 | 客户忘了发 ZIP，或照片发了文字没发，陈总要反复追问 |
| 翻聊天记录浪费时间 | 一个 case 可能要往上翻几十条消息才能找齐信息 |
| 助理 / 新人不容易接手 | 信息在陈总脑子里或微信 thread 里，没有统一 case 视图 |
| 进度不清楚 | 客户问「好了吗？」「还差什么？」— 每次都要人工回复 |

---

### B. 我们的解决方案

```
客户在微信说「我要加车」
        ↓
系统发【开始卡片】→ 客户点 H5 上传 VIN / 行驶证 / 保险卡
        ↓
回到微信补充：提车日期 · 停放 ZIP · 联系电话
        ↓
客户随时问「进度 / 还差什么」→ 系统回复【加车资料进度】
        ↓
陈总在 Workbench 看到整理好的 case → 人工确认 → 办公室按既有流程办事
```

**这不是聊天机器人，而是微信里的 guided workflow。**

---

### C. 为什么有价值

| 价值 | 说明 |
|------|------|
| 减少反复微信追问 | Progress Card 主动回答「进度」「还差什么」 |
| 减少漏资料 | H5 按步骤收照片 + 文字字段 checklist |
| 提高 intake 准确性 | 信息进 case，不散落在 bubble 里 |
| 加快每个 case 处理速度 | 打开 Workbench 30 秒进入工作状态，不用翻微信 |
| 客户体验更清楚 | 客户始终知道自己在第几步 |
| 每个 case 有状态、有记录、可追踪 | 吴小姐接手也能看全貌 |
| 后续可扩展 | 理赔、停保、coverage review — 同一套 case 架构 |

---

### D. 试点范围

| 项目 | 内容 |
|------|------|
| **周期** | 45 天 |
| **办公室** | 1 个（CKS Irvine） |
| **工作流** | Add Vehicle（加车）only |
| **客户入口** | WeCom / 微信 |
| **照片上传** | H5 guided task page |
| **状态查询** | Progress Card（你好 / 进度 / 还差什么） |
| **经纪人审阅** | Workbench queue + case drawer |
| **用量上限** | 100 cases/月 · 300 images/月 · 3 staff seats |

---

### E. 不包含

- 自动改保单
- 自动报价
- Carrier integration
- OCR 自动识别
- 小程序
- 理赔 / 停保 / coverage review
- 24/7 SLA

---

### F. 价格建议

| 档位 | 价格 | 适合场景 |
|------|------|----------|
| Friendly pilot | **$499/月** | 试水、用量较少、双周回顾 |
| **Recommended pilot** ⭐ | **$699/月** | 标准试点：每周 30 分钟改进回顾 + 优先 bug 修复 |
| Mature office system | **$999+/月** | 试点成功后扩展多工作流、更多席位 |

**建议陈总先用：**

> **45 天试点，$699/月，首月可用 $599 作为 friendly start。**

值就继续；不值就停 — 无长期绑定。

---

## 3. Product Positioning

### 我们是什么

**微信里的 Insurance Case Builder / Intake Operating System**

| 层次 | 角色 |
|------|------|
| WeCom 聊天 | 客户入口、信任锚点、文字补充、状态查询 |
| H5 guided task | 结构化照片步骤（VIN → 行驶证 → 保险卡） |
| Progress Card | Spark-style「我在哪一步、还差什么」 |
| Case + event pipeline | 每个 case 有状态、有记录、可恢复 |
| Workbench | 陈总审阅、已知信息、缺项、附件预览 |
| Human confirmation | 陈总确认后才办事；不自动发送、不自动改保单 |

### 我们不是什么

| 错误定位 | 为什么不对 |
|----------|------------|
| 普通 chatbot | 陈总已有吴小姐回微信；「能聊天」不是差异化 |
| 简单上传工具 | 没有状态、没有 case、没有 broker 工作流 |
| CRM | 不是 household 模型、不是 pipeline 管理 |
| 自动报价 / 改保单 | 法律与信任风险；试点明确不做 |

### 一句话定位

> 客户在微信里完成资料收集，系统把杂乱信息变成 broker 可处理的 case。

---

## 4. Customer Workflow

**场景：张先生想给家里加一辆车**

这不是 chatbot 闲聊，而是**微信里的 guided workflow** — 有步骤、有状态、有完成感。

| 步骤 | 客户做什么 | 系统做什么 |
|:----:|------------|------------|
| 1 | 微信说：**「我要加车」** | 发送【开始卡片】，带 H5 上传链接 |
| 2 | 点卡片按钮 | 打开 H5 guided task page |
| 3 | 上传 **VIN 照片** | H5 确认收到，进入下一步 |
| 4 | 上传 **行驶证照片** | H5 确认收到，进入下一步 |
| 5 | 上传 **保险卡照片**，或点跳过 | H5 完成照片阶段 |
| 6 | — | 微信收到：**【第 1 阶段完成 ✅ · 照片资料】** |
| 7 | 在微信打字补充：<br>「7月10号提车，zip 92705，电话 2031234567」 | 系统提取字段，写入 case |
| 8 | — | 微信收到：**【第 2 阶段完成 ✅ · 文字信息】** |
| 9 | 两天后问：**「进度」** | 回复 **【加车资料进度】**：<br>**第 3 步 · 陈总人工确认中 · 暂不需补资料** |
| 10 | — | 客户安心等待，不用反复追问 |

**关键体验点：**

- 客户不用下载 App，不用注册新账号
- 照片在 H5 里结构化上传，文字在微信里自然补充
- 任何时候问「进度 / 还差什么」，系统有明确回答
- 第 3 步明确写「陈总人工确认中」— 信任不破坏

---

## 5. Broker Workflow

**场景：陈总早上打开 Workbench**

| 步骤 | 陈总看到什么 | 价值 |
|:----:|--------------|------|
| 1 | Workbench 队列出现新 case：**张先生 · Add Vehicle · WeCom** | 不用在微信里「感觉」有没有新单 |
| 2 | 打开 case drawer — **text-first 渲染** | 客户名、状态、next step 立刻可见 |
| 3 | **Attachments** 面板：VIN / 行驶证 / 保险卡 | 三张照片可预览，不用让客户重发 |
| 4 | **Known facts**：VIN、提车日期、ZIP、电话 | 已知字段一目了然 |
| 5 | **Still needed** 列表 | 还缺什么清楚列出（通常为空或 1–2 项） |
| 6 | 核对无误 → **Confirm** → 办公室按既有流程去 carrier 办事 | 系统不自动改保单；陈总仍是决策中心 |
| 7 | — | **不用在微信聊天里反复翻历史记录** |

**Broker 价值一句话：**

> 从「翻微信找信息 10 分钟」变成「打开 case 30 秒进入工作状态」。

**P19F-1 已改善的体感：**

- Drawer 打开时 text-first render — 文字信息先出来
- Attachments lazy load + skeleton — 照片后台加载，不挡操作
- Preview latency logs — 我们持续监控加载速度

---

## 6. Why WeChat / WeCom Matters

微信端体验不是临时方案，是 **paid pilot 的核心卖点**。

| # | 战略原因 |
|---|----------|
| 1 | CKS ~99% 华人生意 — 客户已习惯微信沟通 |
| 2 | **不需要下载 App** — 零安装摩擦 |
| 3 | **不需要小程序** — 试点够用；量大了再加 |
| 4 | 沿用微信身份与现有客服关系 — 不破坏信任 |
| 5 | 「在微信里说话 + 点链接」比学新系统简单 |
| 6 | H5 负责结构化照片步骤 — 顺序、确认、skip 规则 |
| 7 | Progress Card 负责状态感 — 「进度」「还差什么」有明确回答 |
| 8 | Workbench 负责 broker 内部处理 — 客户不见复杂度 |
| 9 | Broker 保留人情沟通 — 陈总仍是信任中心 |
| 10 | WeCom + H5 + Progress Card 已做到 **Spark Driver ~82–85% 的 guided workflow 体验** |

**Spark Driver 对比（诚实版）：**

| Spark 仍更强 | 我们更强 |
|--------------|----------|
| App 内 polish、push 通知 | 零安装、微信原生入口 |
| 离线能力 | Broker-in-the-loop 信任 |
| — | 客户问「进度」系统答，不用陈总重复 |

---

## 7. What The Pilot Includes

### 客户侧

- WeCom 客服通道入口
- 「我要加车」→ 开始卡片
- H5 照片上传（VIN / 行驶证 / 保险卡）
- 阶段完成通知（S1 照片 · S2 文字）
- Progress Card（你好 / 进度 / 还差什么 / 继续）
- Phase 2 文字收集（提车日期 / ZIP / 电话）
- Broker review 等待状态（第 3 步）

### 经纪人侧

- Workbench 队列 + case drawer
- Known facts / still needed / next step
- Attachments 预览（私有存储，不公开链接）
- Human confirmation gate
- Text-first drawer UX（P19F-1）

### 运营侧（我方）

- Cloud 托管（GCP + Vercel）
- WeCom 通道维护
- 试点期 bug 修复 + smoke 验证
- 每周 30 分钟改进回顾（$699 档）

### 用量上限

| 项目 | 上限 |
|------|------|
| Cases / 月 | 100 |
| Images / 月 | 300 |
| Workbench seats | 3 |
| OCR | 不含 |
| 自动改保单 | 不含 |
| 小程序 | 不含 |

---

## 8. What The Pilot Does Not Include

| 项目 | 试点说明 | 后续 |
|------|----------|------|
| 自动改保单 / bind | **不做** — 陈总 Confirm 后人工操作 | — |
| 自动报价 / rating | **不做** | — |
| Carrier integration | **不做** | 视试点结果 |
| OCR 自动识别 VIN | **不做** — 照片已收好，broker 看图 | V1.1 可选 add-on |
| 小程序 | **不做** — WeCom+H5 已够 | 量大了再评估 |
| 理赔 / 停保 / coverage review | **不做** — 试点只做加车 | 第二期扩展 |
| 24/7 SLA | **不做** | Enterprise 档 |
| 自动替陈总发微信 | **不做** — 草稿给你，你发 | — |
| Analytics dashboard | **不做** — 试点用周报 | 成熟档 |

---

## 9. Pricing / Terms

### 三档定价

| 档位 | 月费 | 包含 | 不含 |
|------|------|------|------|
| **Friendly pilot** | $499 | 完整 Add Vehicle 流程；100 cases；300 images；3 seats | 双周回顾（非每周）；OCR |
| **Recommended pilot** ⭐ | **$699** | 上述全部 + **每周 30 分钟回顾** + 优先 bug 修复 | OCR；多工作流 |
| **Mature office** | $999+ | 多工作流；5+ seats；OCR pilot；analytics | 需试点成功后升级 |

### 建议成交条款

| 条款 | 建议 |
|------|------|
| 首月 | $599 friendly start（如需促成） |
| 正式月费 | $699/月 |
| 周期 | 45 天试点 → 月付续签 |
| 绑定 | 无长期合约；不满意可停 |
| 超额 | 超过 100 cases 暂停新单或 $2/case — 事先约定 |
| 支持 | 微信 / email；1 个工作日响应 |

### 价值锚点（给陈总算账）

- 30 个加车 case/月 × 5 分钟节省 = **2.5 小时/月**
- 50 个 case × 6 分钟 = **~5 小时/月**
- $699 买的是 **流程标准化 + 少漏资料 + 客户体验**，不只是按件计费

---

## 10. Success Metrics

### 客户侧

| 指标 | 目标 | 怎么量 |
|------|------|--------|
| 无需人工追问即可完成 | ≥70% | 经纪人记录：「有没有追微信要资料？」 |
| 收齐资料平均时间 | <48 小时（从开始卡片） | Case 时间戳 |
| H5 中途放弃率 | <30% | 开始 H5 vs 完成 S1 |
| 「进度」查询由 Progress Card 正确回答 | ≥90% | 抽查 10 个 case |
| 端到端完成率 | ≥60%（从开始到第 3 步） | Postgres 计数 |

### 经纪人侧

| 指标 | 目标 | 怎么量 |
|------|------|--------|
| 每个 case 节省时间 | ≥4 分钟（底线）/ 6 分钟（目标） | 经纪人周记（P16 tracker） |
| Confirm 时缺资料率 | 比 baseline 下降 | 前 10 个手动 vs 后 10 个试点 case 对比 |
| 微信来回轮数 | ↓ ≥30% | 抽查每个 case 气泡数 |
| 经纪人满意度 | ≥4/5 | 试点结束问卷 |
| 试点处理 case 数 | ≥20（最低）/ 50（良好） | 系统计数 |

### 系统侧

| 指标 | 目标 |
|------|------|
| H5 上传成功率 | ≥95% |
| Progress Card 正确率 | ≥95%（抽查） |
| Workbench drawer 文字渲染 | <2s（warm） |
| 图片预览成功率 | ≥90% |

### Go / No-go（是否升级到 $999 档）

| 条件 | 要求 |
|------|------|
| 经纪人报告节省 ≥5 分钟/case | 必须 |
| 少漏资料（经纪人确认） | 必须 |
| 陈总愿意继续付费 | 必须 |

---

## 11. 15-Minute Demo Script

**场合：** 陈总办公室 / 微信视频 / 面对面  
**设备：** Andy 手机（微信客户端）+ 笔记本（Workbench）  
**前提：** Demo 环境已 smoke PASS（`check_chen_kui_demo_environment.sh`）

---

### 0–2 min · Problem Framing

**Andy 说：**

> 陈总，今天给你看一个东西。我们先说问题。
>
> 现在加车资料都在微信聊天里散着 — VIN 在一条消息，行驶证在另一条，ZIP 客户忘了发，你或吴小姐要反复问。
>
> 一个 case 可能要翻几十条聊天记录，助理接手也要问你「这个客户 VIN 在哪」。
>
> 客户也不知道自己交齐了没有，老问「好了吗」「还差什么」。
>
> 我们要解决的不是「能不能聊天」，而是：**怎么把微信里的杂乱信息，整理成你办公室能直接处理的 case。**

**动作：** 不需要操作屏幕。眼神交流，确认陈总点头。

---

### 2–6 min · Customer Side Demo

**Andy 说：**

> 你看客户这边。客户在微信里说四个字：

**动作：** Andy 手机 → 微信对 CKS 客服号发送：**「我要加车」**

**Andy 说：**

> 系统马上回一张【开始卡片】— 不是一堆菜单让你选，是直接进加车流程。
>
> 客户点按钮，打开 H5 页面。

**动作：** 点开始卡片 → H5 打开

**Andy 说：**

> H5 里按顺序来：先 VIN，再行驶证，再保险卡 — 可以跳过。
>
> 这不是让客户随便发图，是**一步一步引导**，像 Spark Driver 接单那样。

**动作：**

1. 展示 VIN 上传步骤（可用 demo 照片或已上传 case）
2. 展示行驶证步骤
3. 展示保险卡或 skip
4. 完成 H5 → 回到微信

**Andy 说：**

> 照片阶段完成，客户回到微信会收到这张卡 — **【第 1 阶段完成 ✅ · 照片资料】**。
>
> 客户很清楚：照片交完了，下一步要补文字。

**动作：** 展示 Stage Complete S1 卡片

---

### 6–9 min · Text Collection Demo

**Andy 说：**

> 接下来客户不用再去 H5，直接在微信里打字就行。

**动作：** 发送：**「7月10号提车，zip 92705，电话2031234567」**

**Andy 说：**

> 系统识别提车日期、ZIP、电话，写进 case。
>
> 三个字段齐了，客户收到第二张完成卡。

**动作：** 展示 Stage Complete S2 卡片

**Andy 说：**

> 现在客户资料都交齐了，进入你这边的确认阶段。
>
> 假设两天后客户问进度 — 很常见对吧？

**动作：** 发送：**「进度」**

**Andy 说：**

> 系统回复【加车资料进度】— **第 3 步 · 陈总人工确认中 · 暂不需补资料**。
>
> 客户不用再来烦你「还要发什么」。你也少回一句是一句。

**动作：** 展示 Progress Card

---

### 9–13 min · Broker Side Demo

**Andy 说：**

> 现在看你的这边。你早上打开 Workbench。

**动作：** 笔记本打开 `https://ui-smoky-beta.vercel.app/workbench/document-intake`（或当前 stable alias）

**Andy 说：**

> 队列里已经有这个 case 了 — 张先生，Add Vehicle，WeCom 渠道。

**动作：** 展示 case queue，点开刚才的 case

**Andy 说：**

> 打开 drawer — 注意文字信息先出来，不用等照片加载。
>
> 这边是已知字段：提车日期、ZIP、电话。
>
> 这边是还缺什么 — 这个 case 已经齐了。
>
> 照片在这 — 点一下能预览，不用让客户重发。

**动作：**

1. 展示 known facts / still needed / next step
2. 滚动到 attachments，点开一张预览
3. 强调 text-first：「文字先出来，照片后台加载」

**Andy 说：**

> 你核对没问题，Confirm，办公室按你们老流程去 carrier 办事。
>
> **系统不会自动改保单。** 最后是你在做决定。
>
> 吴小姐要是接手这个客户，打开同一个 case 就知道全貌 — 不用你 orally transfer。

---

### 13–15 min · Business Close

**Andy 说：**

> 陈总，这就是完整的闭环。
>
> 建议咱们先做 **45 天试点**：
>
> - 只做 **加车** — 最清楚、最容易量效果
> - **$699 一个月**，首月可以 **$599** 试试
> - 包含 100 个 case、300 张图、3 个同事账号
> - **每周咱们花 30 分钟**看数据：省了多少时间、少漏了多少资料
>
> 不包含：自动改保单、OCR、小程序、理赔 — 那些是以后的事。
>
> 一个月下来你告诉我值不值。值就继续；不值就停。没有长期绑定。
>
> 你觉得怎么样？

**动作：** 停顿，等陈总反应。准备进 Objection Handling。

---

## 12. Demo Talking Points

**陈总能听懂的要点 — 按优先级排列：**

| # | Talking Point | 为什么这么说 |
|---|---------------|--------------|
| 1 | **这个不是替代陈总，而是帮陈总把资料收齐、整理好** | 消除「AI 抢生意」顾虑 |
| 2 | **系统不会自动改保单** | 法律与信任底线 |
| 3 | **最后仍然是陈总人工确认** | Human-in-the-loop |
| 4 | **客户不用下载 App** | 零摩擦；华人客户已在微信 |
| 5 | **微信入口最符合华人保险客户习惯** | CKS 99% 华人生意 |
| 6 | **H5 负责结构化上传** | 不是随便发图；有顺序、有确认 |
| 7 | **Progress Card 解决「客户不知道到哪一步」** | Spark-style 状态感；P19E-2 已验证 |
| 8 | **Workbench 解决「陈总不用翻聊天记录」** | 核心 broker 价值 |
| 9 | **现在先做加车，因为这是最清楚、最容易试点的流程** | 范围克制 = 容易成功 |
| 10 | **每个 case 有状态、有记录，吴小姐也能接手** | 团队扩展性 |
| 11 | **试点 45 天，每周看效果，不满意可停** | 降低决策风险 |
| 12 | **不做 OCR 也有价值 — 价值在流程和状态，不是识字** | 诚实设预期 |

### 说什么 vs 不说什么

| ✅ 说 | ❌ 不说 |
|-------|--------|
| 「省你翻微信的时间」 | 「我们用 Cloud Run」 |
| 「客户不会迷路」 | 「Progress Card 算法」 |
| 「吴小姐也能接手」 | 「Postgres JSONB」 |
| 「试点一个月看省多少时间」 | 「以后上 OCR」 |

---

## 13. Objection Handling

**10 个务实 Q&A — 不夸大：**

---

**Q1：为什么不用小程序？**

> 小程序要微信审核、开发周期长、客户还是要学新入口。我们现在企业微信 + H5 + 进度卡，已经能做到类似 Spark Driver 八成以上的引导体验，试点完全够用。等量大了、数据证明值得，再加小程序也不迟。

---

**Q2：客户会不会不敢点 H5？**

> 华人客户天天在微信里点链接 — 支付、银行、表单。我们的 H5 是从微信卡片一键打开，不是陌生网站。试点我们会看数据：多少人点了、多少人完成。如果放弃率高，我们优化文案和按钮，不是推翻方案。

---

**Q3：这个会不会自动修改保单？**

> **不会。** 系统只做资料收集和整理。你在 Workbench 确认后，办公室还是按你们现在的流程去 carrier 操作。我们不会自动发送、不会自动改保单、不会自动绑定。

---

**Q4：图片安全吗？**

> 照片存在私有云存储，没有公开链接。只有你和授权的同事能在 Workbench 里看。比照片散落在微信聊天记录里更可控 — 至少我们知道哪些 case 有哪些附件，离职交接也有记录。

---

**Q5：没有 OCR 还有价值吗？**

> 有。价值在**流程和状态**，不在自动识字。客户按步骤交照片和文字，你打开 case 就知道有什么、缺什么 — 不用翻 50 条微信。OCR 是加速器，以后可以加，但不是试点的前提。

---

**Q6：如果客户乱发图片怎么办？**

> 和现在一样 — 你或吴小姐微信让客户重发对的图。区别在于：case 里有记录，你知道他发过什么、什么时候发的。也可以让客户重新走一遍流程（「重新加车」）。试点期间我们会看这类 case 的比例，再决定要不要加「重传」按钮优化。

---

**Q7：如果客户不会用怎么办？**

> 目标客户是会用微信的中青年客户 — 说话、点链接、发图。如果客户实在搞不定，吴小姐可以代发「我要加车」、帮客户点 H5。系统减少的是**重复追问**，不是消灭人工服务。年纪大的客户你们本来就会多照顾，这个不变。

---

**Q8：为什么要月费？**

> 这是持续运行的办公室系统：微信通道、服务器、案例存储、每周改进。不是卖一次软件装完就结束。云成本本身不高，但维护、支持、根据你们反馈迭代，需要持续投入。月费也是让我们有动力把系统做好，而不是卖完就跑。

---

**Q9：如果一个月 case 少怎么办？**

> 试点包含 100 个 case 额度，用多少算多少。即使一个月只有 20 个加车 case，每个省 5 分钟也是 100 分钟 — 差不多两个小时的经纪人时间。$699 买的是**流程标准化和客户体验**，不只是按件计费。case 少的时候，我们重点看「每个 case 省多少、少漏多少」。

---

**Q10：后面能不能做理赔 / 停保 / coverage review？**

> **能。** 同一套 case 架构 — 不同的工作流模板。试点先把加车跑通，因为这是最频繁、字段最清楚的流程。证明了省时间、少漏资料，第二期加理赔或停保是自然延伸。但现在不承诺、不收费、不开发 — 避免分散精力。

---

## 14. Follow-up Plan

### Demo 当天

| 动作 | 负责人 | 时间 |
|------|--------|------|
| 发送 one-page proposal（§2 中文版） | Andy | Demo 结束前或当天 |
| 确认陈总是否有疑问 | Andy | Demo 中 §13 已覆盖大部分 |
| 约定下周跟进电话 / 微信 | Andy | Demo 结束前 |

### Demo 后 48 小时内

| 动作 | 详情 |
|------|------|
| 发送试点合同草案 | 45 天、$699/月、scope 见 §7–8 |
| 确认试点启动日 | 建议选月初，方便按月计费 |
| 确认 3 个 Workbench 账号 | 陈总 + 吴小姐 + 1 位同事 |
| 确认 WeCom 客服号已连通 | `check_chen_kui_demo_environment.sh` |

### 试点第 1 周

| 动作 | 详情 |
|------|------|
| 第一次 weekly review（30 min） | 过至少 3 个真实 case |
| 启动经纪人时间节省周记 | 复用 P16 tracker 模板 |
| 记录客户 drop-off 点 | H5 哪一步放弃最多 |

### 试点第 4–6 周

| 动作 | 详情 |
|------|------|
| 中期回顾 | 对照 §10 success metrics |
| Go / No-go 讨论 | 继续 $699、升 $999、或停 |
| 若继续：讨论第二期 lane（理赔 / 停保） | 不在试点 SOW 内 |

### 如果陈总说「再想想」

| 回应 | 内容 |
|------|------|
| 不强推 | 「没问题，proposal 你留着。想试的时候告诉我，环境随时 ready。」 |
| 提供低门槛选项 | 「要不先 $599 一个月，只做 20 个 case 试试？」 |
| 不降价到 $199 | 不可持续；P19G-0 成本模型已论证 |

---

## 15. Final Recommendation

### 15.1 现在应该做什么

| 优先级 | 动作 |
|:------:|------|
| **1** | 用本文 §2 one-page proposal 约陈总 demo |
| **2** | 按 §11 脚本做 15 分钟 live demo |
| **3** | Demo 后 48h 内发合同草案 |
| **4** | 试点启动后每周 review + P16 时间节省 tracker |

### 15.2 现在不应该做什么

- 不做 OCR
- 不做小程序
- 不做理赔 / 停保 lane
- 不为了「更完美」延迟 pilot conversation
- 不承诺自动改保单、自动报价、24/7 SLA

### 15.3 核心判断

| 判断 | 理由 |
|------|------|
| **产品已 ready for Add Vehicle demo** | P19E-2 Progress Card ✅ · P19F-1 Workbench ✅ |
| **成本支持 $499+ 定价** | P19G-0：月成本 ~$25–50；100 cases ~$35–80 |
| **瓶颈是 sales conversation，不是产品** | P19G-1 结论 |
| **微信体验是核心卖点** | 零安装 + guided workflow + Progress Card = 差异化 |
| **45 天 / $699 / 首月 $599 是最佳成交组合** | 范围清晰、价格好说、无长期绑定 |

### 15.4 成交话术（最后一句）

> 陈总，客户已经在微信里了。我们让他们在微信里把资料交齐，你打开工作台 30 秒就知道有什么、缺什么。你确认后再办事。先试 45 天，一个月你告诉我值不值。

---

## Next UX Polish After Proposal

> **以下为未来微信体验优化 backlog。不影响现在开始 pilot conversation。不在本轮实现。**

| # | 优化项 | 目的 |
|---|--------|------|
| 1 | 更短的微信文案 | 减少客户阅读负担 |
| 2 | 更像人工经纪人的语气 | 信任感；不像机器人 |
| 3 | 更清楚的按钮 label | 降低 H5 drop-off |
| 4 | 更好的 Progress Card copy | 「第 X 步」更口语化 |
| 5 | 更自然的错误恢复 | 格式不对时给示例，不「骂」客户 |
| 6 | 「继续上传」体验优化 | 中断后回来一键续传 |
| 7 | Broker asks more info loop | 陈总缺资料时，系统帮发追问卡 |
| 8 | Async OCR later | VIN 自动读码；broker 加速器 |

**原则：** 微信体验继续打磨是核心路线，但**不阻塞 pilot close**。先成交、再迭代。

---

## STOP Report

| # | Item | Result |
|---|------|--------|
| 1 | **Document path** | `docs/p19g2_one_page_proposal_demo_script.md` |
| 2 | **One-page proposal created?** | **Yes** — §2 中文版，可直接给陈总 |
| 3 | **Demo script created?** | **Yes** — §11 完整 15 分钟脚本 |
| 4 | **Recommended positioning** | **微信里的 Insurance Case Builder / Intake OS** — not chatbot |
| 5 | **Recommended pilot price** | **$699/month**（首月 $599 friendly start）；floor $499；mature $999+ |
| 6 | **Pilot scope** | 45 天 · 1 office · Add Vehicle · 100 cases/mo · 300 images/mo · 3 seats |
| 7 | **Not included** | 自动改保单 · 自动报价 · carrier integration · OCR · 小程序 · 理赔/停保/coverage review · 24/7 SLA |
| 8 | **Demo duration / structure** | **15 min** — 0–2 problem · 2–6 customer · 6–9 text+progress · 9–13 broker · 13–15 close |
| 9 | **Key talking points** | 不替代陈总 · 不自动改保单 · 微信入口 · H5 结构化 · Progress Card 状态感 · Workbench 省翻微信 · 先加车 |
| 10 | **Main objections covered** | **10 Q&A** — §13（小程序/H5安全/OCR/月费/扩展等） |
| 11 | **Code changed?** | **No** |
| 12 | **Deploy happened?** | **No** |
| 13 | **STOP** | **✅ P19G-2 CLOSED** |

**Next:** 约陈总 demo → 发合同 → 启动试点 weekly review

---

*P19G-2 CLOSED 2026-07-07. Document only. No code. No deploy. No config change.*
