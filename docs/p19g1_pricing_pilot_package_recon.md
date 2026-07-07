# P19G-1 — Pricing / Pilot Package Recon for Chen Kui Insurance

**Date:** 2026-07-07  
**Type:** Pricing / packaging recon — **documentation only**  
**Audience:** Andy (founder), Chen Kui (CKS / 金盾保险), sales conversation prep  
**Prerequisite:** P19E-2 Progress Card ✅ · P19F-1 Workbench Drawer UX Polish ✅ · P19G-0 Actual Cost Gap ✅  
**Related:** `p19g0_actual_cost_gap_cost_model_recon.md` · `p19e3_channel_strategy_wecom_h5_miniprogram_recon.md` · `p18_4_cks_business_positioning_and_demo_strategy.md` · `trial/P16_TIME_SAVINGS_MODEL.md` · `BROKER_ONE_PAGER.md`

**This loop:** No code. No deploy. No config change. No payment integration. No pricing implementation.

---

## 1. Executive Summary

P19G-1 turns P19G-0 cost findings into a **sellable paid pilot package** for Chen Kui Insurance.

| Question | Answer |
|----------|--------|
| **What are we selling?** | **微信里的 Insurance Case Builder / Intake Operating System** — not a chatbot |
| **Why now?** | Add Vehicle loop is live: WeCom → H5 photos → Phase 2 text → Progress Card → Workbench broker review |
| **Core differentiator** | **WeCom + H5 + Progress Card** delivers **~82–85% Spark Driver-style guided workflow** without App or mini program |
| **Recommended pilot price** | **$699/month** (target band $599–799); minimum sustainable **$499/month** |
| **Pilot duration** | **30–60 days** |
| **Should Andy start the paid pilot conversation now?** | **Yes** — product is demo-ready for Add Vehicle; cost supports pricing; main gap is **sales materials**, not core workflow |
| **Next step after this doc** | **One-page proposal + 15-min live demo script** — not more infra polish |

**One-line pitch to Chen Kui:**

> 客户在微信里完成加车资料收集，系统把杂乱信息整理成办公室能直接处理的 case；你确认后再办事，不自动改保单。

---

## 2. Product Positioning

### 2.1 What this is NOT

| Wrong framing | Why it fails for CKS |
|---------------|-------------------|
| 普通 chatbot | 陈总已有吴小姐回微信；「能聊天」不是差异化 |
| 简单上传图片工具 | 没有状态、没有 case、没有 broker 工作流 |
| CRM | 不是 household 模型、不是 pipeline 管理、不是 carrier 集成 |
| Quote engine / rating | ADR-003 禁区；demo 与 pilot 均不承诺自动报价 |
| 自动改保单系统 | 法律与信任风险；Confirm 后仍由 broker 人工操作 |

### 2.2 What this IS

**微信里的 Insurance Case Builder / Intake Operating System**

| Layer | Role |
|-------|------|
| **WeCom chat** | 客户入口、信任锚点、文字补充、状态查询 |
| **H5 guided task page** | 结构化照片步骤（VIN → 行驶证 → 保险卡） |
| **Progress Card** | Spark-style「我在哪一步、还差什么」 |
| **Case state machine + event pipeline** | Postgres 真相源；阶段可恢复 |
| **Workbench** | Broker 审阅、已知信息、缺项、附件预览 |
| **Human confirmation** | 陈总确认后才进入办事；不自动发送、不自动改保单 |

**One sentence:**

> 客户在微信里完成资料收集，系统把杂乱信息变成 broker 可处理的 case。

### 2.3 Positioning vs competitors / alternatives

| Alternative | Our edge |
|-------------|----------|
| Raw WeChat thread | 无结构化状态、无 case 记忆、漏资料、翻历史累 |
| Generic form link | 无对话恢复、无进度卡、客户不知道找谁问 |
| Carrier portal | 客户不熟、broker 仍要整理信息 |
| Mini program (future) | 更高开发成本；pilot 不需要；WeCom+H5 已够 |

---

## 3. Why WeCom / 微信 Is Strategic

微信端体验不是临时方案，是 **paid pilot 的核心卖点**。

| # | Strategic reason |
|---|------------------|
| 1 | **华人保险客户已习惯微信沟通** — CKS ~99% 华人生意 |
| 2 | **不需要下载 App** — 零安装摩擦 |
| 3 | **不需要注册新账号** — 沿用微信身份与现有客服关系 |
| 4 | **低摩擦、低教育成本** — 「在微信里说话 + 点链接」比学新系统简单 |
| 5 | **Broker 保留人情沟通** — 陈总仍是信任中心；系统是助手不是替代 |
| 6 | **H5 task page 负责结构化步骤** — 照片顺序、确认、skip 规则 |
| 7 | **Progress Card 负责状态感** — 「你好 / 进度 / 还差什么」→ 【加车资料进度】 |
| 8 | **Workbench 负责 broker 内部处理** — 客户不见复杂度 |
| 9 | **小程序可以以后做，paid pilot 不需要** — P19E-3 已论证 defer |
| 10 | **微信丝滑体验是差异化，不是权宜之计** | Chat + Guided Task + Human Review + Case Memory |

### Spark Driver parity without native app

Per P19E-3 (post P19E-2 Progress Card):

| Layer | Spark-like score |
|-------|:----------------:|
| Photo proof discipline | ~85% |
| Binary step clarity | ~90% |
| Status / resume /「我在哪」 | ~85% |
| Trust / product feel | ~70% |
| **Overall** | **~82–85%** |

**Explicit statement:**

> **WeCom + H5 + Progress Card can deliver 80–85% of Spark Driver-style guided workflow without building a native app or mini program.**

What Spark still wins on: in-app polish, push notifications, offline. What we win on: **zero install**, **broker-in-the-loop trust**, **WeChat-native recovery** («进度」「还差什么»).

---

## 4. Current MVP Capabilities

### 4.1 Customer side (live)

| Capability | Status | Notes |
|------------|:------:|-------|
| Start Card（我要加车） | ✅ | Opens guided flow |
| H5 VIN / registration / insurance card upload | ✅ | Signed deep link; private GCS |
| Stage Complete S1（照片阶段完成） | ✅ | WeCom notification after H5 |
| Phase 2 text: delivery date / ZIP / phone | ✅ | WeCom chat merge |
| Stage Complete S2（文字阶段完成） | ✅ | Triggers broker review phase |
| Progress Card: 你好 / 进度 / 还差什么 | ✅ | 【加车资料进度】live smoke PASS |
| Restart flow: 重新加车 | ✅ | New flow when explicitly requested |
| Broker review wait state（第 3 步） | ✅ | Progress Card shows no action needed |

### 4.2 Broker side (live)

| Capability | Status | Notes |
|------------|:------:|-------|
| Workbench queue | ✅ | Document intake inbox |
| Case drawer | ✅ | Single case detail |
| Attachments preview | ✅ | Backend proxy; no public URL |
| Known facts / collected fields | ✅ | Add-car field set |
| Still needed / next step | ✅ | Rule-based merge |
| Text-first drawer UX | ✅ | P19F-1 — skeleton, lazy images |
| Preview latency logs | ✅ | PREVIEW_PERF on backend |

### 4.3 Architecture (pilot-safe)

| Component | Status |
|-----------|--------|
| Postgres source of truth | ✅ `caseiq` @ Cloud SQL |
| GCS private attachments | ✅ `caseiq-wecom-media-qa` |
| Backend preview proxy | ✅ Auth-gated |
| No public GCS URL | ✅ |
| No OCR in main WeCom/H5 flow | ✅ By design |
| No schema-heavy event table | ✅ JSONB + state machine sufficient |

---

## 5. Customer Experience Story

**场景：张先生想给家里加一辆车**

1. 张先生在微信对 CKS 客服说：**「我要加车」**
2. 收到 **开始卡片**，点链接进入 H5
3. 在 H5 按顺序上传：**VIN 照片 → 行驶证 → 保险卡**（可 skip 非必填项）
4. 回到微信，收到：**【第 1 阶段完成 ✅ · 照片资料】**
5. 在微信打字补充：**「7月10号提车，zip 92705，电话 203-123-4567」**
6. 收到：**【第 2 阶段完成 ✅ · 文字信息】** — 进入陈总确认阶段
7. 两天后张先生问：**「进度」**
8. 系统回复 **【加车资料进度】**：**第 3 步 · 陈总人工确认中 · 暂不需补资料**

**这就是微信里的 Spark-style workflow** — 客户始终知道自己在哪，不用下载 App，不用记账号，不用翻 50 条聊天记录找 VIN。

---

## 6. Broker Experience Story

**场景：陈总早上打开 Workbench**

1. 队列里出现新 case：**张先生 · Add Vehicle · WeCom 渠道**
2. 抽屉打开：**text-first** — 已知信息立刻可见（VIN、ZIP、提车日期、电话）
3. **Still needed** 列表为空或只剩 1–2 项 — 不用翻微信 thread 10 分钟
4. **Attachments** 面板：三张照片可预览，不用让客户重发
5. Progress Card 已告诉客户「第 3 步确认中」— 减少「好了吗？」追问
6. 陈总核对无误 → **Confirm** → 办公室按既有流程去 carrier 办事
7. 吴小姐若接手：打开同一 case 即知全貌 — 不用 oral transfer

**Broker 价值一句话：** 从「翻微信找信息」变成「打开 case 30 秒进入工作状态」。

---

## 7. Business Value for Chen Kui

Ranked by pilot sellability:

| Rank | Value | Evidence / framing |
|:----:|-------|-------------------|
| 1 | **节省 broker 时间** | P16 model: ~6.2 min/case saved (sim); floor 4 min; 50 cases/mo ≈ **22 hr/mo** |
| 2 | **减少漏资料** | Structured H5 slots + still_needed list; 不用靠记忆 checklist |
| 3 | **提高 intake 准确性** | 照片 + 文字分阶段；字段 merge 进 case，不散落在 bubble 里 |
| 4 | **减少来回微信沟通** | Progress Card 主动回答「进度」「还差什么」 |
| 5 | **新人/助理也能跟流程** | Case 状态 + Workbench 全貌；降低对陈总大脑的依赖 |
| 6 | **每个 case 有状态和记录** | Postgres SoT；可复盘、可交接 |
| 7 | **后续可扩展** | 理赔 Lite、停保、coverage review — 同一 case 架构 |
| 8 | **形成数据资产** | 结构化 intake 数据为未来 analytics / renewal 打基础 |

**ROI anchor (conservative):**

- 30 add-car cases/month × 5 min saved = **2.5 hr/month**
- At implicit $60/hr broker time → **$150/month value** — still justifies **$499** if only time counted
- At 50 cases × 6.2 min → **~$1,320/month value** — **$699 pilot captures ~50%** of conservative upside

---

## 8. Paid Pilot Package

### 8.1 Package name

**中文：** 微信加车资料收集试点  
**English:** WeChat Insurance Intake Pilot — Add Vehicle

### 8.2 Duration & format

| Item | Detail |
|------|--------|
| **Duration** | 30–60 days (recommend **45 days** first contract) |
| **Offices** | 1 broker office (CKS Irvine) |
| **Workflows** | **Add Vehicle only** (V1 pilot scope) |
| **Support** | WeChat/email; 1 business-day response |
| **Cadence** | Weekly 30-min improvement review (target tier) |

### 8.3 Included

| Included | Detail |
|----------|--------|
| WeCom customer entry | 企业微信客服通道 |
| H5 photo upload flow | VIN / registration / insurance card |
| Progress Card | 你好 / 进度 / 还差什么 / 继续 |
| Phase 2 text collection | 提车日期 / ZIP / 电话 |
| Workbench broker review | Queue + drawer + attachments |
| Human confirmation gate | 陈总 Confirm 后办事 |
| Hosting & ops | Cloud Run + Cloud SQL + GCS (our stack) |
| Basic support | Bug fix, smoke validation |
| Weekly feedback loop | Target tier ($699) |

### 8.4 Usage limits (contract defaults)

| Limit | Included |
|-------|----------|
| Cases/month | **100** |
| Images/month | **300** |
| Broker seats (Workbench) | **3** |
| OCR | **Not included** (V1.1 option) |
| Automated policy change | **Not included** |
| Mini program | **Not included** |
| Custom carrier integration | **Not included** |
| SLA / 24×7 | **Not included** |

**Overage:** Pause new cases or $2/case over 100 — agreed upfront.

---

## 9. Pricing Recommendation

Based on P19G-0: COGS ~$50–80/month; fixed infra ~$25–45; value anchor ~$1,000+/month at volume.

### Tier 1 — Minimum ($499/month)

| | |
|---|---|
| **For** | Friendly pilot; proof of value; tight scope |
| **Includes** | Full Add Vehicle workflow; 100 cases; 300 images; 3 seats |
| **Excludes** | Weekly calls (biweekly only); OCR; custom work |
| **Verdict** | **Floor price** — viable if CKS commits to ≥20 cases/month and honest feedback |

**$199/month is too low for long-term** — even at $25–50 cloud cost, it cannot cover development, maintenance, support, and the **$500–1,300/month broker value** delivered. OK only as **one-time 30-day intro** with hard caps, not recurring pricing.

### Tier 2 — Target ($699/month) ⭐ Recommended

| | |
|---|---|
| **For** | Serious paid pilot; weekly improvement; 100 cases/month |
| **Includes** | Everything in Minimum + weekly 30-min review + priority bug fix |
| **Why $699** | Middle of $599–799 band; easy to say; leaves room for intro discount to $599 |

### Tier 3 — Mature ($999+/month)

| | |
|---|---|
| **For** | Real office intake system after pilot success |
| **Adds** | Multi-workflow (claim lite, premium review); 5+ seats; async OCR pilot; analytics; retention policy |
| **When** | After 60-day pilot proves ≥4 min/case saved + broker satisfaction |

### Pricing summary table

| Tier | Price | Best for |
|------|-------|----------|
| Intro (one-time) | $499 first month → $699 | Close the deal |
| **Target** | **$699/month** | **Standard paid pilot** |
| Minimum recurring | $499/month | Cap usage; biweekly check-in |
| Mature | $999+/month | Post-pilot expansion |

---

## 10. Usage Limits / Scope

### In scope (pilot)

- Add Vehicle intake end-to-end
- WeCom + H5 + Progress Card + Workbench
- Up to 100 cases / 300 images per month
- 3 Workbench users
- English + Chinese customer copy
- Bug fixes during pilot period

### Out of scope (do not promise)

| Item | Defer to |
|------|----------|
| OCR / auto VIN read | V1.1 add-on |
| Auto quote / rating | Never in pilot |
| Auto policy change / bind | Never |
| Mini program | V2 if metrics justify |
| Claim / premium / renewal lanes | Phase 2 pilot extension |
| CRM / household model | V2+ |
| Multi-office / white-label | Post-CKS success |
| Payment portal / Stripe | Out of product scope |
| 24×7 SLA | Enterprise tier only |

---

## 11. What Is Included

**Customer experience:**
- Guided add-car flow in WeChat
- Photo upload via H5
- Text field collection in chat
- Progress/status replies without human chase
- Clear broker-review-wait state

**Broker experience:**
- Structured case in Workbench
- Known / missing fields
- Attachment preview
- Confirm gate before office action
- Case memory for staff handoff

**Operations (our side):**
- Cloud hosting on GCP + Vercel
- WeCom channel maintenance
- Deploy & smoke validation
- Pilot-period bug fixes

---

## 12. What Is Not Included Yet

| Gap | Customer impact | Pilot honest answer |
|-----|-----------------|---------------------|
| OCR | Broker still reads photos | 「照片已收好，文字字段系统整理；OCR 下一阶段」 |
| Premium / Claim lanes | Only add-car live | 「试点先做加车，理赔/续保可第二期」 |
| Auto WeChat reply send | Broker copies/confirms | 「草稿给你，你发 — 不自动替您说话」 |
| VIP tags / segment | Manual for now | 「可以加标签，试点后完善」 |
| H5 read-only progress page | Progress Card covers 85% | 「微信里问进度即可；H5 进度页可后加」 |
| Thumbnails / faster preview | P19F-1 improved UX; not instant | 「能看，大图加载需几秒」 |
| Analytics dashboard | Manual weekly review | 「试点用周报，不是 BI 大屏」 |

---

## 13. Pilot Success Metrics

### Customer side

| Metric | Target | How to measure |
|--------|--------|----------------|
| Cases completed without manual chase | ≥70% | Broker log: «did you WeChat chase for missing info?» |
| Avg time to collect required info | <48 hr from Start Card | Case timestamps |
| H5 drop-off rate | <30% | Started H5 vs completed S1 |
| «进度» queries answered by Progress Card | ≥90% correct | Spot-check 10 cases |
| End-to-end completion rate | ≥60% of started flows | Cases reaching Phase 3 |

### Broker side

| Metric | Target | How to measure |
|--------|--------|----------------|
| Time saved per case | ≥4 min (floor) / 6 min (goal) | Broker weekly log (P16 tracker) |
| Missing info rate at Confirm | ↓ vs baseline | Compare first 10 manual vs 10 pilot cases |
| WeChat back-and-forth rounds | ↓ ≥30% | Count bubbles per case (sample) |
| Broker satisfaction | ≥4/5 | End-of-pilot survey |
| Cases processed in pilot | ≥20 (min) / 50 (good) | Postgres count |

### System

| Metric | Target |
|--------|--------|
| H5 upload success rate | ≥95% |
| Progress Card correctness | ≥95% on spot-check |
| Workbench drawer text render | <2s warm |
| Preview load success | ≥90% |
| API error rate | <2% |

### Business (go/no-go for $999 tier)

| Criterion | Pass |
|-----------|------|
| Saves ≥5–10 min/case (broker-reported) | Required |
| Reduces missed info (broker-reported) | Required |
| Chen Kui willing to continue paid | Required |
| Supports $499+ without discount pressure | Desired |

---

## 14. Sales Narrative / Talking Points

### Opening (30 seconds)

> 陈总，我们不是做一个聊天机器人。我们做的是：**客户在微信里把加车资料交齐，你打开工作台 30 秒就知道缺什么、有什么照片、下一步干什么。** 你确认后再去办事，系统不会自动改保单。

### Three proof points (live demo)

1. **Customer:** 发「我要加车」→ H5 传照片 → 回微信补文字 → 问「进度」→ 收到【加车资料进度】
2. **Broker:** Workbench 打开 case → 已知信息 + 照片预览 + 缺项列表
3. **Trust:** 第 3 步明确写「陈总人工确认中」— AI 整理，人决策

### Value framing (not tech framing)

| Say | Don't say |
|-----|-----------|
| 「省你翻微信的时间」 | 「我们用 Cloud Run」 |
| 「客户不会迷路」 | 「Progress Card 算法」 |
| 「吴小姐也能接手」 | 「Postgres JSONB」 |
| 「试点一个月看省多少时间」 | 「以后上 OCR」 |

### Close

> 建议先做 **45 天试点，$699/月**，只做加车。一个月下来你告诉我省了多少时间、少漏了多少资料。值就继续；不值就停 — 没有长期绑定。

---

## 15. Risks and Objections

| # | Objection | Honest answer |
|---|-----------|---------------|
| 1 | **为什么不用小程序？** | 小程序要审核、开发慢、客户还是要学新入口。我们现在 WeCom+H5+进度卡已经做到 Spark 八成体验，试点够用了。量大了再加小程序。 |
| 2 | **客户会不会不会点 H5？** | 华人客户天天点链接（支付、表单、银行）。我们用的是微信里一键打开的 H5，不是陌生网站。试点会看 drop-off 数据；如果高再优化文案。 |
| 3 | **会不会自动改保单？** | **不会。** 系统只整理资料；你 Confirm 后办公室按老流程去 carrier 操作。 |
| 4 | **图片安全吗？** | 照片存私有云存储，不公开链接；只有你和授权同事能在工作台看。比微信聊天里散落照片更可控。 |
| 5 | **不做 OCR 有什么价值？** | 价值在 **流程和状态**，不是识字。客户按步骤交照片+文字，你打开 case 就知道有什么、缺什么 — 不用翻 50 条微信。OCR 是加速器，不是试点前提。 |
| 6 | **为什么要每月收费？** | 这是持续运行的办公室系统：微信通道、服务器、案例存储、每周改进。不是卖一次软件。云成本虽不高，但维护、支持和迭代需要持续投入。 |
| 7 | **一个月 case 不多怎么办？** | 试点包含 100 case 额度；用多少算多少。即使 20 个 case，每个省 5 分钟也是 100 分钟 — $699 买的是 **流程标准化**，不只是按件计费。 |
| 8 | **和普通微信聊天有什么区别？** | 普通聊天：信息散落、无状态、靠人记。这个：**有步骤、有进度卡、有 case、有工作台** — 客户问「进度」系统答，不用你总是重复。 |
| 9 | **客户发错图怎么办？** | 可以重新上传或开新流程（重新加车）。Broker 在工作台看到附件，不对就微信让客户重发 — 和今天一样，但 case 里有记录。 |
| 10 | **以后能做理赔/停保/coverage review 吗？** | **能。** 同一套 case 架构。试点先把加车跑通；证明了再扩展第二条 lane。 |

---

## 16. Final Recommendation

### 16.1 Should Andy start the paid pilot conversation now?

**Yes.**

| Ready | Not ready |
|-------|-----------|
| Add Vehicle E2E live | OCR |
| Progress Card PASS | Mini program |
| Workbench drawer polished | Multi-lane (claim/premium) |
| Cost model supports $499+ | Payment automation |
| Spark-like UX ~82–85% | Perfect preview speed |

The bottleneck is **sales conversation**, not core product for Add Vehicle.

### 16.2 Recommended price & package

| Item | Recommendation |
|------|----------------|
| **Price** | **$699/month** (offer $599 first month if needed to close) |
| **Duration** | 45 days, roll to month-to-month |
| **Scope** | Add Vehicle only; 100 cases; 300 images; 3 seats |
| **Cadence** | Weekly 30-min review |

### 16.3 Why WeChat experience is the core sell

- CKS 客户已在微信 — **meet them where they are**
- Progress Card 证明 **不会迷路** — Spark 最难复制的状态感
- Broker 仍在 loop — **信任不破坏**
- No App / no mini program = **faster pilot, lower risk**

### 16.4 Next step: sales deck vs more polish

| Priority | Action |
|:--------:|--------|
| **1** | **One-page proposal (中英文)** — price, scope, limits, success metrics |
| **2** | **15-min live demo script** — customer path + broker path + objection prep |
| **3** | Broker weekly time-savings log template (reuse P16 tracker) |
| **4** | Optional polish: H5 progress read-only page (V1.1, not blocking close) |

**Do not delay pilot close for:** thumbnails, mini program, OCR, claim lane.

### 16.5 Do not promise in sales conversation

- Auto quote / bind / policy change
- OCR accuracy or «自动识别 VIN»
- Mini program timeline
- Claim / premium lanes in pilot SOW
- 24×7 support or SLA
- «AI 代替陈总回复客户»

---

## STOP Report

| # | Item | Result |
|---|------|--------|
| 1 | **Document path** | `docs/p19g1_pricing_pilot_package_recon.md` |
| 2 | **Recommended positioning** | **微信里的 Insurance Case Builder / Intake OS** — not chatbot |
| 3 | **Why WeCom/微信 strategic** | Zero install, habit fit, Progress Card = Spark-like state; **82–85% guided workflow** |
| 4 | **Current MVP value** | Add Vehicle E2E: WeCom → H5 → Phase 2 → Progress Card → Workbench |
| 5 | **Recommended pilot package** | **WeChat Insurance Intake Pilot — Add Vehicle**, 45 days, 1 office |
| 6 | **Recommended price** | **$699/month** target ($599 intro ok); floor **$499**; mature **$999+** |
| 7 | **Included usage limits** | 100 cases/mo · 300 images/mo · 3 seats · no OCR |
| 8 | **Not included** | OCR, auto bind, mini program, claim/premium lanes, carrier integration, SLA |
| 9 | **Success metrics** | ≥4 min/case saved · ↓ missing info · ≥20 cases · broker ≥4/5 satisfaction |
| 10 | **Main objections** | 小程序/OCR/安全/月费 — see §15 (10 Q&A) |
| 11 | **Code changed?** | **No** |
| 12 | **Deploy happened?** | **No** |
| 13 | **STOP** | **✅ P19G-1 CLOSED** |

**Next:** One-page proposal for Chen Kui + live demo booking — or P19G-2 Sales Deck if Andy wants a separate artifact.

---

*P19G-1 CLOSED 2026-07-07. No code. No deploy. No config change. Recon only.*
