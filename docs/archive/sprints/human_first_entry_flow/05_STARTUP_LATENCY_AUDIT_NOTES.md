# Human-First Entry Flow — Startup Latency Audit Notes

**Sprint**: Human-First Entry Flow + Startup Latency Audit  
**Created**: 2026-03-15

---

## 1. Likely Current Causes of First-Interaction Slowness

| Layer | Likely cause | How to inspect |
|-------|--------------|----------------|
| **Frontend** | React render, API call setup, no optimistic UI | Add timestamps: click → request sent; response received → render |
| **Backend cold start** | Cloud Run scale-to-zero; first request wakes instance | Compare first request vs second request latency |
| **Embedding / RAG** | If triage uses retrieval, embedding model cold start | Check if triage path uses RAG; measure embedding call |
| **LLM** | If LLM_GENERATION_ENABLED=1, first LLM call can be slow | Compare triage_path=fast vs triage_path=llm latency |
| **Routing** | Fast path vs LLM path; rule-based is faster | Run verify_speed_routing.py; check triage_path in response |

---

## 2. What to Inspect

| Inspection | Method |
|------------|--------|
| Click to request sent | Frontend: `console.time` / `performance.now` at click and at fetch start |
| Request to response | Network tab; or backend logging |
| Response to render | Frontend: time from response to setState/display |
| Cold vs warm | First request vs second request (same session) |
| Rule vs LLM | Run with LLM_GENERATION_ENABLED=0 vs 1; compare |

---

## 3. What Data / Signals to Look At

| Signal | Where |
|--------|-------|
| `triage_path` | Triage result: "fast" | "llm" | "rule" |
| Request duration | Browser Network tab; or backend access log |
| Backend startup | Cloud Run metrics: cold start count, instance startup time |
| Button-start flow | Does it skip any step? (e.g., no typing → faster perceived) |

---

## 4. What Can Be Inferred If Hard Measurements Are Limited

- If first request >> second request: cold start likely
- If triage_path=llm and slow: LLM latency likely
- If triage_path=fast and still slow: frontend or network
- Button-start with empty input: eliminates typing time; isolates backend/LLM

---

## 5. Best Next Optimization Direction (Audit Findings)

| Finding | Likely cause | Recommendation |
|---------|--------------|----------------|
| **First click to first reply** | Backend triage (rule or LLM) + network | Button-starter eliminates typing time; perceived speed improves |
| **Cold start** | Cloud Run scale-to-zero; first request wakes instance | Consider min instances=1 for demo; or keep-alive ping |
| **LLM vs rule** | triage_path=llm slower than triage_path=fast/rule | Expand fast path for more Turn 1 cases (TURN1_LIGHTWEIGHT_COLDSTART) |
| **Frontend** | No optimistic UI before response | Already shows "正在整理 case..." during loading |

**Best next move**: Expand fast path for high-value Turn 1 intents (add-car, claim, payment) so more first interactions skip LLM. Button-starter flow already improves perceived speed by removing typing step.

---

## 6. Reinforcement Sprint (2026-03-15) — Post-Loop Summary

| Layer | Status | Notes |
|-------|--------|-------|
| **Button-starter** | Improved | Click with empty input → submitMessage(starterMessage) → first reply; no typing needed |
| **Payment starter** | Fixed | "付款有问题" now routes to payment_lapse_expiration (added 付款/账单 to markers) |
| **Soft_route fallback** | Added | When triage returns unclear + soft_route set → intent-specific first reply |
| **Live Summary** | Improved | 主题/已收集/还需 labels; "（实时更新）" note |
| **Cold vs warm** | Documented | First request >> second: cold start. triage_path=fast: rule-based. triage_path=llm: LLM latency |

---

*See also: Execution Outline, Acceptance/SLA Criteria*
