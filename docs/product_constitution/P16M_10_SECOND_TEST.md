# P16-M Phase 4 — 10-Second Test

**Date:** 2026-06-01  
**Method:** Screenshot-level simulation — cold broker, cold assistant, cold customer  
**Questions:** (1) What is this? (2) What do I do? (3) What happens next?  
**Pass:** All three answered within 10 seconds  
**Scale:** 0–100 per page per persona

---

## Test Protocol

- No documentation, no founder, no prior SearchForge context  
- First viewport 1440×900 unless noted  
- Score = average of three question passes (0 / 0.5 partial / 1 full) × 100

---

## Page 1 — Broker Workbench Empty (`product_only`)

### Cold Broker (Chen Kui)

| Question | Pass? | Evidence |
|----------|-------|----------|
| What is this? | ✅ Full | Tagline 粘贴客户消息·整理草稿·您确认后发送 + 办公室工作台 |
| What do I do? | ✅ Full | Textarea + 开始整理 above fold |
| What happens next? | ⚠️ Partial | Trust line says manual send; no visual of draft outcome |

**Score: 83**

### Cold Office Assistant

| Question | Pass? | Evidence |
|----------|-------|----------|
| What is this? | ✅ Full | Same |
| What do I do? | ⚠️ Partial | May hesitate on 快速体验 vs paste (two paths) |
| What happens next? | ⚠️ Partial | Demo card implies "load samples first" |

**Score: 67**

### Cold Customer (wrong URL)

| Question | Pass? | Evidence |
|----------|-------|----------|
| What is this? | ❌ Fail | Broker paste tool; no customer entry in trial |
| What do I do? | ❌ Fail | N/A |
| What happens next? | ❌ Fail | N/A |

**Score: 0** (expected — trial hides customer tab)

---

## Page 2 — Broker Workbench + Case Open (`product_only`)

### Cold Broker

| Question | Pass? | Evidence |
|----------|-------|----------|
| What is this? | ✅ Full | 整理结果一眼 + urgency |
| What do I do? | ✅ Full | 复制客户草稿 prominent |
| What happens next? | ✅ Full | 主行动 line + draft preview |

**Score: 100**

### Cold Assistant

| Question | Pass? | Evidence |
|----------|-------|----------|
| What is this? | ⚠️ Partial | Glance block dense; ①②③ needs scan |
| What do I do? | ✅ Full | Copy draft |
| What happens next? | ✅ Full | Next step visible |

**Score: 83**

---

## Page 3 — Broker Workbench Full Dev (first visit)

### Cold Broker

| Question | Pass? | Evidence |
|----------|-------|----------|
| What is this? | ⚠️ Partial | Tabs + Add-Car suffix |
| What do I do? | ❌ Fail | Four tabs; may land 客户报送 |
| What happens next? | ❌ Fail | Intro alert wall |

**Score: 33**

---

## Page 4 — Customer Intake Empty

### Cold Customer

| Question | Pass? | Evidence |
|----------|-------|----------|
| What is this? | ⚠️ Partial | 加车报价 · 客户统一报送 — long tagline |
| What do I do? | ❌ Fail | 3 buttons + structured form + text — >10s |
| What happens next? | ⚠️ Partial | Step track visible but abstract |

**Score: 50**

### Cold Broker (if shown customer tab)

| Question | Pass? | Evidence |
|----------|-------|----------|
| What is this? | ⚠️ Partial | Customer portal not paste tool |
| What do I do? | ❌ Fail | Wrong surface for triage |
| What happens next? | ⚠️ Partial | 办公室接手 mentioned |

**Score: 50**

---

## Page 5 — Customer Post-Handoff Result

### Cold Customer

| Question | Pass? | Evidence |
|----------|-------|----------|
| What is this? | ✅ Full | 受理结果卡 |
| What do I do? | ⚠️ Partial | 您这边下一步 present; append vs wait unclear |
| What happens next? | ✅ Full | 办公室侧下一步 |

**Score: 83**

---

## Page 6 — Global / Chrome Only

### Cold Broker (trial)

| Question | Pass? | Evidence |
|----------|-------|----------|
| What is this? | ✅ Full | Brand + tagline |
| What do I do? | ⚠️ Partial | Must scroll past brand to paste |
| What happens next? | ⚠️ Partial | Trust only |

**Score: 67**

---

## Summary Scoreboard

| Page | Broker | Assistant | Customer |
|------|--------|-------------|----------|
| Workbench empty (trial) | **83** | 67 | 0 |
| Workbench + case (trial) | **100** | 83 | — |
| Workbench full dev | 33 | 33 | — |
| Customer empty | 50 | — | **50** |
| Customer result | — | — | **83** |
| Chrome only | 67 | 67 | — |

---

## Target vs Actual

| Metric | P16-J baseline | P16-M current | Target |
|--------|----------------|---------------|--------|
| Broker cold 10s (trial empty) | 72–74 | **83** | ≥85 |
| Broker cold 10s (with case) | — | **100** | ≥90 |
| Customer cold 10s (empty) | — | **50** | ≥70 |
| Assistant parity gap | — | **16 pts** | ≤10 |

---

## Fail Clusters (fix = UI only)

1. **Demo card vs paste** — assistant hesitation on empty workbench  
2. **Customer empty choice overload** — fails 5-second customer test  
3. **Full dev tab default** — broker wrong-tab failure (trial fixed)  
4. **Brand block height** — pushes paste below fold on 768px height  

---

*End of P16-M 10-Second Test*
