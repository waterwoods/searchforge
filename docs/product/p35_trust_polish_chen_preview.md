# P3.5 Trust Polish — Chen Preview

**Date:** 2026-07-25  
**Mode:** Founder / UX Writer / Office Receptionist — not Engineering sprint  
**Scope:** Customer-facing copy, hierarchy, micro-interactions only  
**Frozen:** C01 / C02 / C03 architecture, Workflow, AMS, Timeline, Notification, backend logic, AI  

**One objective:** Every customer finishes thinking — *They already know me. They listened. I know what happens next. I trust Chen’s office.*

**Out of scope:** New capability, new pages, workflow redesign, AMS, notifications, architecture.

---

## 1. Every copy change

### Opening / Home

| Before | After |
|--------|-------|
| 今天需要办理什么？ | 今天怎么了？我们在。 |
| 告诉陈总发生了什么，我们帮您整理资料 | 告诉陈总发生了什么，我们帮您记下 |
| 正在确认您的案件状态… | 正在为您准备… |
| 请稍候，我们不会在确认前开始新的报案。 | 请稍候。 |
| 暂时无法确认案件状态 | 暂时连不上办公室 |
| 暂时无法确认您的案件状态，请重试或联系陈总。 | 请重试，或直接联系陈总。 |

### Start Claim

| Before | After |
|--------|-------|
| 正在确认… / 请稍候，确认后才能开始新的报案。 | 正在为您准备… / 请稍候。 |
| 今天发生了什么？（panel + form, twice） | Panel owns the question; form title removed on matched/blank |
| 办公室已了解您（subtitle + signal + chips） | Once — chips label only |
| …VIN、保险卡等证件资料，如需再补充会通知您。 | 可录音转文字，也可直接打字。先说清楚事故情况即可。 |
| 例如：今天上午 9 点 或 Today 9 am | 例如：今天上午 9 点 |
| 用于帮助确认事故顺序。 | *(deleted)* |
| 现在可以跳过，之后也可以补交。 | 照片现在可以跳过。 |
| 可能对应到多位客户。… | 我们想先跟您确认一下。… |
| 办公室已了解您。只需告诉我们今天的事故。 | 只需告诉我们今天的事故。 |
| Visible「xx 字」counter | *(deleted from Start Claim)* |
| Soft notice button「知道了，继续报案」 | Banner text only — no fake gate button |

### Review

| Before | After |
|--------|-------|
| 请确认资料 | 交给陈总前看一眼 |
| 请确认内容是否正确 | 看一眼再交给陈总 |
| 内容正确即可提交 | 没问题就可以交给陈总 |
| 主要资料已齐全，可以确认并交给陈总。 | 这些内容会交给陈总。 |
| 资料概要 | 您刚才说的 |
| 正在加载提交前检查… | 正在准备… |
| 确认并交给陈总 | 交给陈总 |
| …这不是向保险公司正式报案。 | …这不等于向保险公司正式报案。 |

### Receipt / Waiting / Case Status

| Before | After |
|--------|-------|
| 资料已提交 + status pill + 提交时间 + 下一步 + 陈总会联系您 + 可能还需补充 + disclaimer | **已收到** · **陈总会尽快联系您** · **先不用操作** |
| 资料已提交，等待陈总审核 | 已提交，陈总正在看 / 先不用操作 |
| 资料已收到，等待陈总审核 | 已收到，陈总正在看 |
| 审核中 | 陈总正在看 |
| 补充资料已收到，陈总会继续审核。 | 补充已收到，陈总会继续看。 |
| 下一步由陈总审核 | 下一步由陈总联系您 |
| 陈总开始审核。 | 陈总会尽快联系您。 |
| 资料已齐，陈总正在审核。 | 资料已齐，陈总正在看。 |
| 陈总正在审核中。 | 陈总正在看。 |
| 请等待确认。 | 如需补充，陈总会再联系您。 |
| 加载失败，请重试 | 一会儿再试，或联系陈总 |

### Success / Safety

| Before | After |
|--------|-------|
| 已收到您的事故说明 + VIN/保险卡 lines | 已收到 · 陈总会先了解事故情况 · 如需补充，我们会再通知您 · 先不用操作 |
| 此记录用于办公室整理事故信息，不代表已向保险公司正式报案。 | 这是给办公室整理用的记录，不等于向保险公司正式报案。 |

---

## 2. Every button change

| Before | After | Why |
|--------|-------|-----|
| 确认并交给陈总 | 交给陈总 | Shorter, office voice |
| Soft notice「知道了，继续报案」 | *(removed as button)* | Was a fake gate |
| Receipt primary「资料已提交，等待陈总审核」(disabled) | No primary when waiting; secondary only | Parents need permission to stop |
| Receipt sections implied many next actions | One calm next line + optional「查看已提交内容」/「返回首页」 | Less paralysis |

Unchanged (correct): 提交给陈总 · 联系陈总 · 继续 · 开始 · 返回首页

---

## 3. Every headline change

| Screen | Before | After |
|--------|--------|-------|
| Service Home | 今天需要办理什么？ | 今天怎么了？我们在。 |
| Opening gate | 正在确认您的案件状态… | 正在为您准备… |
| Start gate | 正在确认… | 正在为您准备… |
| Review | 请确认资料 | 交给陈总前看一眼 |
| Receipt | 资料已提交 | 已收到 |
| Case Status | 资料已收到，等待陈总审核 | 已收到，陈总正在看 |
| Success | 已收到您的事故说明 | 已收到 |

---

## 4. Anything to delete

- Double「今天发生了什么？」on matched/blank path  
- Repeated「办公室已了解您」in subtitle + confidence signal  
- Character counter on Start Claim story  
- 「用于帮助确认事故顺序」helper  
- VIN from Start Claim default subtitle and Success body  
- 「Today 9 am」from customer-facing placeholder / validation hint  
- Soft-notice option button  
- Receipt: status pill, 提交时间, separate「下一步 / 陈总会联系您 / 可能还需补充」blocks when waiting  

---

## 5. Anything to simplify

- Receipt → three-line calm landing when nothing is owed  
- Trust phrase said once (chips)  
- Waiting vocabulary unified: 陈总正在看 / 会联系您 / 先不用操作  
- Safety line kept true, quieter, after reassurance  
- Soft policy notice → one sentence banner  

---

## 6. Anything that still sounds like software

| Residual | Severity | Notes |
|----------|----------|-------|
| Chip grid layout | Low | Acceptable; copy now office-warm |
| Status pill on Case Status | Low | Now says 陈总正在看 |
| Progress `1/3` on Request More | Low | Only when customer owes work |
| 「重试」on error | Low | Needed; paired with 联系陈总 |
| VIN label on Request More item | Acceptable | Only when Chen asked for it |

---

## 7. Anything Chen would never say

**Removed / rewritten (was never Chen):**  
审核 · 案件状态 · 请确认资料 · 资料概要 · 多位客户 · VIN-first · 确认后才能开始 · 正式报案 as peer of Next Step

**Chen would say (now closer):**  
> 我知道你是谁。今天怎么了？说完就行。我看了找你。先不用操作。

---

## 8. Final Trust Score

| | Before | After |
|--|-------:|------:|
| **Overall** | **6.8 / 10** | **8.2 / 10** |
| Customer Trust (matched) | 7.5 | 8.5 |
| Calmness under stress | 6.0 | 8.0 |
| Continuity (am I done?) | 5.5 | 8.5 |
| Human office feel | 6.5 | 8.0 |
| Demo readiness for Chen | 7.0 | 8.5 |

Biggest lift: **Submit → Receipt / Waiting** no longer returns the customer to administration anxiety.

---

## 9. Ready for Chen Preview?

# **YES**

**Why:**  
Opening no longer sounds like a system gate. Matched path asks the story once and says “we know you” once. Waiting voice is office language (陈总正在看), not underwriting (审核). Receipt gives permission to put the phone down. Safety truth remains, quieter. No architecture or capability drift. Build Gate PASS. Focused customer-surface tests PASS.

**Still ask Chen in the room (not blockers):**  
1. Flag ON for S2 / S3 / S5 walk so “they know me” is visible.  
2. One physical Preview: Home → matched story → submit → calm receipt.  
3. Voice quality for 58-year-olds (product truth, not this polish).

---

## Parents test

> If my own parents had a small accident today, would I confidently hand them this Mini Program, without explaining anything?

**YES — for the matched / blank / waiting path after this polish.**

Stop. Do not invent more work. The goal is trust, not perfection.
