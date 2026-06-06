# Simulation Assistant Speed + Realism Audit Report

**Sprint:** Simulation Assistant Speed + Realism Audit  
**Date:** 2026-03-13  
**Mode:** Focused analysis / audit — inspect → measure → diagnose → recommend

---

## 1. Speed diagnosis

### Current request path

```
[User] Click "Run simulation" or "Next turn"
  → SimulationAssistant.runNextTurn()
  → setReplayTurns([...prev, customerTurn])  // customer turn appears immediately ✓
  → triageMessage(customerText, false, conversationTurnsForApi)
  → POST /api/inbox/triage  (axios, 30s timeout)
  → Backend: triage_conversation(text, turns) or triage_message(text)
  → _llm_triage(merged_text) OR _rule_based_triage(merged_text)
  → [If rule + notice/doc confusion] retrieve_notice_explanation() or retrieve_document_explanation()
     → get_embedder().encode() + qdrant_search()
  → Response → setReplayTurns([...prev, systemTurn])
```

### Biggest bottleneck

**LLM API call (when `LLM_GENERATION_ENABLED=1`)**  
- Each turn does one `client.chat.completions.create()` (gpt-4o-mini default)  
- Typical latency: **1.5–5 seconds** per turn  
- First turn is worst: no prior context, full prompt + 2000 chars  
- Production often uses LLM for richer drafts; rule-based is faster but less natural

### Second bottleneck

**Cloud Run cold start + embedder warmup**  
- Cold start: **5–15 seconds** (docs: `DEPLOYMENT_READINESS_SPRINT_REPORT.md`)  
- First request after idle: container spin-up + embedding model load  
- Embedder warmup: `start_embedding_warmup()` runs in background; first triage can hit `EMBED_READY=False` → retrieval skipped, but readiness check can delay  
- If `NOTICE_RETRIEVAL_ENABLED=1` and message triggers notice/document confusion: **+0.5–2s** for embedding + Qdrant search

### Third / minor

- **Network:** Vercel → Cloud Run cross-region adds ~100–300ms  
- **Rule-based path:** Fast (~50–200ms) unless retrieval is triggered  
- **Auto-play delay:** 1800ms between turns is intentional, not a bug

### Rough latency breakdown (typical first turn, LLM enabled)

| Stage                    | Time (approx) |
|--------------------------|---------------|
| Cold start (if idle)      | 5–15 s        |
| LLM API call              | 1.5–5 s       |
| Rule merge + templates    | &lt;100 ms     |
| Retrieval (if triggered)  | 0.5–2 s       |
| Network round-trip        | 0.1–0.5 s     |

**Warm path (no cold start):** ~2–6 s per turn, dominated by LLM.

### Classification

| Type              | Cause                          | Avoidable?                    |
|-------------------|--------------------------------|-------------------------------|
| Actual latency    | LLM + cold start + retrieval   | Partially (see recommendations) |
| Perceived latency | No streaming; user waits for full reply | Yes (optimistic UI)      |
| Acceptable        | 2–4 s warm is normal for LLM   | —                             |

---

## 2. Realism diagnosis

### Strongest realistic parts

- **Add-car 3-turn (SIM15):** "想加一台车，宝马X5" → "2024年的" → "90210，下周提车" — natural progression, field-by-field
- **SIM14 "发你了":** Minimal follow-up — realistic shorthand
- **SIM10 "就是上次那个材料，我又发了":** Vague "上次那个材料" — real customer ambiguity
- **SIM2 Turn 3:** "garaging proof 是什么意思？要发什么？" — real clarification ask

### Weakest / most "teaching-style" parts

- **Broker-forwarded framing:** Many turns use "客户问：...", "客户说...", "我发了截图在微信" — this is broker dictation, not raw customer voice
- **Over-orderly field reveal:** SIM3: Turn 1 quote → Turn 2 year → Turn 3 zip+delivery — too neat; real customers often mix or omit
- **Too complete:** "我买了台宝马X5，想问下保费多少钱" — real users say "宝马x5，多少钱" or "我新车，下周拿，保险大概？"
- **Explanatory tone:** Notes like "Turn 1 vague quote ask; Turn 2 year" — written for QA, not for "would a broker think this is real?"

### Biggest realism gaps

| Gap                    | Current state                                      | Real customer behavior                          |
|------------------------|----------------------------------------------------|-------------------------------------------------|
| Broker-forwarded voice | "客户问：...", "客户说..."                          | Direct: "这个 notice 什么意思？"                 |
| Too clean / complete   | Full sentences, ideal field order                   | Fragments, wrong order, mixed language          |
| Not enough messiness   | 15 scenarios mostly orderly                        | Adversarial pack (27 messy) not in Simulation Assistant |
| Mixed intent missing  | Single-intent per scenario                         | "加车，顺便 garaging proof 是什么？"            |
| Corrections / emotion  | Few "我其实已经付了" style corrections             | More "都发过了怎么还要", "还不行吗"               |

### Scenario quality snapshot

| Scenario   | Realism | Notes                                                |
|-----------|---------|------------------------------------------------------|
| SIM1      | Partial | "客户问" framing; Turn 3 good clarification          |
| SIM2      | Good    | UW follow-up, "他又发了一次", "garaging proof 是什么意思" |
| SIM3      | Weak    | Too orderly; real: "宝马x5，多少钱"                  |
| SIM14     | Strong  | "发你了" — minimal, realistic                        |
| SIM15     | Partial | Structure good; wording still tidy                   |
| Adversarial A1–A7 | N/A | Not in Simulation Assistant; used in guardrail only |

---

## 3. Startup-grade improvement options

### Speed

| Tier              | Option                                      | Cost   | Impact                         |
|-------------------|----------------------------------------------|--------|--------------------------------|
| **Low-cost**      | Show customer turn immediately (already done) | 0      | Perceived speed ✓              |
| **Low-cost**      | Skeleton / "Thinking..." for system reply    | 1–2 h  | Perceived speed ↑              |
| **Low-cost**      | Demo mode: rule-only, no retrieval for SIM   | 2 h    | Avoid retrieval latency       |
| **Medium-cost**   | Keep-alive / prewarm before demo              | 4–8 h  | Avoid cold start              |
| **Medium-cost**   | min_instances=1 (Cloud Run)                  | $/mo   | No cold start                  |
| **Not worth now** | Streaming reply tokens                      | High   | Complex; small gain for demo   |
| **Not worth now** | Lighter LLM model for SIM                    | Medium | May hurt quality               |

### Realism

| Tier              | Option                                      | Cost   | Impact                         |
|-------------------|----------------------------------------------|--------|--------------------------------|
| **Low-cost**      | "Real customer pack": 5–8 scenarios from adversarial + mixed_intent | 2–4 h | High demo value                |
| **Low-cost**      | Remove "客户问/客户说" from top trial scenarios | 1 h    | More direct customer voice     |
| **Low-cost**      | Add 2–3 messy fragments to SIM3/SIM15        | 1–2 h  | Quick realism bump            |
| **Medium-cost**   | Expand SIM with adversarial A1–A7, D1–D5    | 4–6 h  | Strong stress-test             |
| **Medium-cost**   | Mixed-intent scenarios (MI-AC1, MI-PR1)      | 4–6 h  | "Real customers ask 2 things"  |
| **Not worth now** | LLM-generated customer utterances            | High   | Unpredictable; scripted is fine for pilot |

---

## 4. Recommended priority plan

### First: Perceived speed (low-cost)

1. **Add "Thinking..." / skeleton** for system reply while waiting  
   - User sees customer turn + "Assistant is thinking..." → system reply  
   - File: `SimulationAssistant.tsx` — show placeholder in Replay when `loading && replayTurns.length > 0`  
   - Effort: ~1 hour

### Second: Realism (low-cost)

2. **Create "Real customer pack"** — 5–8 scenarios using adversarial + mixed-intent  
   - Pull from `configs/adversarial_real_user_scenarios.json` and `configs/mixed_intent_scenarios.json`  
   - Add section: "Real customer style (messy, short, mixed)"  
   - Examples: A1 "宝马x5，多少钱", D1 "都发过了怎么还要 declaration page", MI-AC1 "我想加一辆车，然后这个 garaging proof 又是什么？"  
   - Effort: 2–4 hours

### Third: Cold-start mitigation (if demo is slow)

3. **Pre-demo keep-alive** — curl `/readyz` or `/api/inbox/triage` with a tiny payload 2–3 min before demo  
   - Or: document "wait 30s after opening page" for first scenario  
   - Effort: 1 hour (script or doc)

### Postpone

- Streaming replies  
- min_instances=1 (cost)  
- Full adversarial integration into all 15 scenarios  
- LLM-generated customer utterances  

---

## 5. Biggest risks / cautions

| Risk                    | Mitigation                                           |
|-------------------------|------------------------------------------------------|
| Overengineering         | Stick to skeleton + real pack; no streaming/platform |
| Breaking guardrails     | New scenarios must pass `run_simulation_assistant_scenarios.py` |
| Cold start surprise     | Document pre-demo warmup; consider keep-alive script |
| Realism vs. robustness  | Messy scenarios may hit "unclear" — test before adding |

---

## 6. 中文总结

### 现在为什么慢

1. **LLM 调用**：每轮都要调 OpenAI，约 1.5–5 秒  
2. **Cloud Run 冷启动**：闲置后首次请求 5–15 秒  
3. **检索**：notice/document 类问题会做 embedding + Qdrant，再加 0.5–2 秒  

### 现在为什么还像教学版

1. **经纪人口吻**：很多是「客户问：…」「客户说…」，不是客户原话  
2. **太整齐**：每轮按字段顺序给，真实客户会乱序、漏信息、用碎片句  
3. **对抗/混合场景没用上**：adversarial、mixed_intent 的素材没进 Simulation Assistant  

### 小企业最值钱的修法

1. **感知速度**：加「思考中…」占位，让用户知道系统在算  
2. **真实感**：做 5–8 个「真实客户风格」场景，用 adversarial + mixed_intent 的文案  

### 第一件事最该改什么

**加「思考中…」占位** — 成本低，立刻改善等待体验  

### 第二件事最该改什么

**做 Real customer pack** — 5–8 个 messy、short、mixed 场景，让陈魁觉得「这就是我客户会说的」  

### 哪些暂时不要做

- 流式输出  
- min_instances=1（多花钱）  
- 把所有 15 个场景都改成对抗风格  
- 用 LLM 生成客户话术  

---

*See also: `docs/CHEN_KUI_TRIAL_PACK.md`, `configs/adversarial_real_user_scenarios.json`, `configs/mixed_intent_scenarios.json`*
