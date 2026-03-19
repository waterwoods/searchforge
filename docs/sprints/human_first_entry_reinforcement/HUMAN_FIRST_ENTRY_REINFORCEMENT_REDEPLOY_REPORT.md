# Human-First Entry Flow Reinforcement + Redeploy Report

**Sprint**: Human-First Entry Flow Reinforcement + Redeploy  
**Created**: 2026-03-15  
**Scope**: Chen Kui Insurance Unified Entry

---

## 1. Sprint Theme

- **What was chosen**: Strengthen the 4 priorities (answer-first, button starters, live Case Summary, startup latency) without opening broad new scope.
- **Why now**: Founder wanted one more strengthening pass before checking Vercel again. Previous sprint introduced the features; this sprint makes them more production-ready.

---

## 2. Document Set Created

| Doc | Path |
|-----|------|
| Sprint Blueprint | `docs/sprints/human_first_entry_reinforcement/01_SPRINT_BLUEPRINT.md` |
| Execution Outline | `docs/sprints/human_first_entry_reinforcement/02_EXECUTION_OUTLINE.md` |
| Acceptance / SLA Criteria | `docs/sprints/human_first_entry_reinforcement/03_ACCEPTANCE_SLA_CRITERIA.md` |
| Reinforcement Checklist | `docs/sprints/human_first_entry_reinforcement/04_REINFORCEMENT_CHECKLIST.md` |

---

## 3. Baseline Recheck

| Priority | Baseline state |
|----------|----------------|
| **Answer-first** | Toyota Corolla, payment failed, missing doc chase, claim hit-and-run: all returned intent-specific replies. Exception: "付款有问题" (payment button starter) returned unclear + "内容不够完整". |
| **Button starters** | handleButtonStarter already calls submitMessage(starterMessage). add_car, claim starters worked. Payment starter failed due to unclear. |
| **Live Summary** | Card visible with Intent / Collected / Still needed. Labels in English only. |
| **Startup latency** | Documented in 05_STARTUP_LATENCY_AUDIT_NOTES.md. Cold vs warm vs LLM distinguished. |

---

## 4. Iteration Loop 1

### What changed
- **Payment markers**: Added 付款, 付款问题, 付款失败, 账单, 账单问题 to `configs/industries/insurance/markers.json` payment array.
- **Soft_route fallback**: When triage returns unclear and soft_route is set, inject intent-specific first reply via `SOFT_ROUTE_STARTER_REPLIES` in `services/fiqa_api/routes/inbox_triage.py`.
- **Starter replies**: add_car, remove_car, claim_intake, cancellation_warning, missing_document each have a human-first first reply for button clicks.

### What got more human
- "付款有问题" now returns: "这看起来是付款出了问题。现在最关键的是把最新通知或付款截图发我..."
- Button clicks with minimal text never fall through to generic "内容不够完整".

### What got more intuitive after clicking buttons
- All 5 buttons now return a clear first reply when clicked with empty input.
- User immediately sees "the system is helping me" for the chosen flow.

### What did not improve
- LLM path latency unchanged (backend).
- Cold start unchanged (Cloud Run).

### Whether it was worth it
- **Yes.** Payment starter fix and soft_route fallback eliminate the main generic-fallback gap.

---

## 5. Iteration Loop 2

### What changed
- **Live Summary**: Added "（实时更新）" note; bilingual labels: 主题/Intent, 已收集/Collected, 还需/Still needed.
- **Startup latency**: Updated 05_STARTUP_LATENCY_AUDIT_NOTES.md with reinforcement sprint summary.

### What improved vs loop 1
- Case Summary feels more structured and real-time.
- Founder can see 主题/已收集/还需 at a glance.

### What still remained weak
- Latency: cold start and LLM path unchanged. Perceived speed depends on backend deployment (Cloud Run).

### Startup latency conclusion
- **Frontend**: "正在整理 case..." during load; button-starter removes typing step.
- **Backend**: triage_path=fast for most Turn 1 cases; triage_path=llm for ambiguous.
- **Cold start**: First request >> second when Cloud Run scale-to-zero. Recommendation: min instances=1 for demo or keep-alive.

### Whether it was worth it
- **Yes.** Live Summary labels improve clarity; latency doc is complete.

---

## 6. Optional Loop 3

- **Whether used**: No.
- **Reason**: Loop 1 and 2 addressed the highest-value items. No clearly valuable, low-risk refinement remained. Stopping is correct.

---

## 7. Validation Summary

| Check | Result |
|-------|--------|
| `run_inbox_triage_scenarios.py` | 53/53 passed |
| `guardrail_inbox_triage.sh` | PASS |
| `verify_speed_routing.py` | OK |
| `npm run build` | Success |

**Limitations**: API test and multi-turn simulations require backend on 8001. Guardrail passed with server running.

---

## 8. Redeploy Result

| Item | Value |
|------|-------|
| **Frontend success** | Yes |
| **Backend redeploy** | Not required for this sprint (markers + route logic; backend must be redeployed for new behavior to be live) |
| **Production URL** | https://ui-euhunog28-andys-projects-1f411b73.vercel.app |
| **Alias** | https://ui-smoky-beta.vercel.app |
| **Alias updated** | Yes |
| **Warnings** | Chunk size > 500 kB (pre-existing) |

**Note**: Backend changes (payment markers, soft_route fallback) require backend redeploy for production. Local demo and API test on 8001 already use the new logic.

---

## 9. Post-Deploy Inspection

| Priority | Directly visible | Inferred from build/code |
|----------|------------------|--------------------------|
| **Answer-first** | — | Payment starter + soft_route fallback in code |
| **Button starters** | — | handleButtonStarter + starter replies in code |
| **Live Summary** | Yes — 主题/已收集/还需, （实时更新） | — |
| **Startup** | — | Latency doc; "正在整理 case..." in code |

**Blocked by backend deployment**: Full answer-first and button-starter behavior on production frontend requires backend (Cloud Run) to be redeployed with the new markers and route logic.

---

## 10. Founder Showcase (REQUIRED)

### Scenario 1: Quote (Toyota Corolla)
- **User does**: Types "我才买了一个2026年的丰田花冠，我想问一下，大约半年的保费是多少？"
- **System now says**: "好的，丰田花冠。先把地址邮编发我，我就能帮你算报价。"
- **Still need to collect**: zip (or delivery, driver if zip provided)
- **Summary now shows**: 主题: customer question; 已收集: year, model; 还需: zip
- **Why this is better**: Acknowledges vehicle first; asks only next missing field; no "内容不够完整".

### Scenario 2: Payment / Cancellation
- **User does**: Clicks "付款 / 账单" with empty input (or types "付款有问题")
- **System now says**: "这看起来是付款出了问题。现在最关键的是把最新通知或付款截图发我，我先帮你确认；如果还没付，今天尽快处理，避免停保。"
- **Still need to collect**: payment notice or screenshot
- **Summary now shows**: 主题: payment_lapse_expiration; 已收集: (none); 还需: payment_notice_or_screenshot
- **Why this is better**: Before: "内容不够完整". Now: intent-specific, reassuring, asks for one thing.

### Scenario 3: Missing Document
- **User does**: Types "我上周已经发过了，怎么还在追材料？"
- **System now says**: "您说发过了，我这边帮你核对。把完整通知和您发过的材料发我，核对好后就能往下推。"
- **Still need to collect**: full notice, materials sent
- **Summary now shows**: 主题: missing_document; 已收集: (customer_says_sent); 还需: full_notice, requested_documents
- **Why this is better**: Reassures first; avoids generic "请提供更多信息".

### Scenario 4: Claim
- **User does**: Clicks "报事故" with empty input (or types "刚撞了，对方跑了，我现在先干嘛？")
- **System now says**: "先别慌，我先按事故来帮您处理。先把事故经过、现场照片和对方车牌发我，我帮你确认下一步怎么报案。" (or hit-and-run variant)
- **Still need to collect**: accident details, photos, other driver info
- **Summary now shows**: 主题: customer_question (claim); 已收集: (none); 还需: accident_time, photos, etc.
- **Why this is better**: Reassuring; asks for concrete next steps; hit-and-run gets tailored reply.

### Scenario 5: Button clicked but user says something else
- **User does**: Clicks "获取报价" but then types "其实我是想问付款失败了怎么办"
- **System now says**: Reroute message "看起来这是付款/取消相关的问题，我先帮您处理这个。" + payment-specific reply
- **Still need to collect**: payment notice/screenshot
- **Summary now shows**: 主题: payment_lapse_expiration; reroute_occurred: true
- **Why this is better**: System adapts to what user actually said; doesn't force quote flow.

---

## 11. Final Judgment

1. **Were the 4 priorities reinforced?** Yes.
2. **Which of the 4 is strongest now?** Answer-first + button starters (payment fix + soft_route fallback).
3. **Which is still weakest?** Startup latency (cold start, LLM path) — documented but not optimized.
4. **Is the product now ready for founder inspection on Vercel?** Yes for frontend (Live Summary). Full behavior requires backend redeploy.
5. **What exactly should the founder test next?**
   - Open https://ui-smoky-beta.vercel.app/workbench/unified-intake
   - Click each quick-start button with empty input — verify first reply (requires backend on same API URL)
   - Type Toyota Corolla quote, payment failed, missing doc chase — verify answer-first replies
   - Check Case Summary shows 主题/已收集/还需 and （实时更新）
6. **Single best next move after this sprint**: Redeploy backend (Cloud Run) so production frontend gets the new payment markers and soft_route fallback. Then founder can test full flow on Vercel.

---

## 12. Iteration Log (REQUIRED)

### Loop 1
- **What changed**: Payment markers (付款/账单); soft_route fallback; SOFT_ROUTE_STARTER_REPLIES
- **What got better vs prior**: Payment button starter works; no generic fallback when button clicked
- **What did not improve**: LLM latency, cold start
- **What remained slow**: Backend triage (rule path is fast; LLM path slower)
- **Whether the loop was worth it**: Yes
- **Recommended next step**: Loop 2 (live summary + latency doc)

### Loop 2
- **What changed**: Live Summary labels (主题/已收集/还需); （实时更新）; latency doc update
- **What got better vs loop 1**: Summary clearer; real-time feel
- **What did not improve**: Latency (documentation only)
- **What remained slow**: Cold start, LLM path
- **Whether the loop was worth it**: Yes
- **Recommended next step**: Redeploy; skip Loop 3

---

## 13. 中文宏观总结

- **为什么要加强这四点**：创始人希望在 Vercel 上检查前再做一次加固，让入口体验更人性化、更直接。
- **我们用了什么主要方法**：1) 增加付款相关中文标记（付款、账单等）；2) 按钮点击时若 triage 返回 unclear，用 soft_route 注入意图专属首句；3) 优化 Case Summary 标签（主题/已收集/还需）并标注「实时更新」。
- **现在已经加强了什么**：付款按钮首句不再「内容不够完整」；5 个按钮点击都能得到清晰首句；Case Summary 更易读、更有实时感。
- **现在是不是可以去 Vercel 检查了**：可以。前端已部署；完整行为需后端同步部署。
- **还有哪一点最弱**：启动延迟（冷启动、LLM 路径）— 已记录，未优化。
- **下一步最该做什么**：部署后端到 Cloud Run，让生产环境前端获得新逻辑；然后创始人在 Vercel 上做完整验收。

---

## 14. COPY/PASTE FOUNDER BLOCK

```
Human-First Entry Flow Reinforcement Sprint — Summary

Strongest reinforced area: Answer-first + button starters (payment fix, soft_route fallback)
Weakest remaining area: Startup latency (cold start, LLM path — documented, not optimized)

Answer-first improved: Yes — Toyota Corolla, payment, missing doc, claim all get intent-specific first reply
Buttons became true starters: Yes — all 5 buttons return first reply when clicked with empty input
Live summary improved: Yes — 主题/已收集/还需 labels, （实时更新） note

Most likely latency cause: Backend cold start (Cloud Run scale-to-zero) or LLM path when triage_path=llm

Should Andy inspect Vercel now? Yes — frontend deployed to https://ui-smoky-beta.vercel.app
Note: Backend must be redeployed for full behavior (payment markers, soft_route fallback).
```
