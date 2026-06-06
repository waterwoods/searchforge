# P16-N Phase 2 — Five Second Test

**Date:** 2026-06-01  
**Method:** Cold-customer simulation — no broker knowledge, no insurance jargon, no prior SearchForge context  
**Viewport:** 1440×900 desktop; 390×844 mobile noted where different  
**Questions:** (1) What is this? (2) What should I do? (3) What happens next?  
**Pass threshold:** All three answered in 5 seconds  
**Scale:** 0–100 = average of three passes (0 / 0.5 partial / 1 full) × 100

---

## Persona

- California auto insurance customer (English or Chinese OK)
- Received a link from broker office
- Never seen Unified Intake
- Does not know what "加车" means unless explained in plain language

---

## Page 1 — Customer Landing (Empty)

**First 5 seconds visible:** Hero H2, long tagline, 3-step track, headline, ①②③ instructions, three large buttons, structured form header, textarea below fold.

| Question | Pass? | Evidence |
|----------|-------|----------|
| What is this? | ⚠️ Partial | "加车报价 · 客户统一报送" — insurance jargon; tagline is a paragraph |
| What should I do? | ❌ Fail | Three equal buttons; no single obvious path in 5s |
| What happens next? | ⚠️ Partial | Step track visible but abstract (开始报送 → 补齐 → 办公室) |

**Score: 33** (P16-M 10s test: 50 — 5s is harsher)

**Mobile (390px):** Textarea likely below fold after buttons + collapse label. **Score: 25**

---

## Page 2 — Add Car Button Clicked (First System Reply Loading)

| Question | Pass? | Evidence |
|----------|-------|----------|
| What is this? | ⚠️ Partial | Transaction banner + progress card appear |
| What should I do? | ⚠️ Partial | Input area exists but thread collapsed for add-car |
| What happens next? | ❌ Fail | Record rail sections before user reads anything |

**Score: 33**

---

## Page 3 — Add Car Mid-Collection

| Question | Pass? | Evidence |
|----------|-------|----------|
| What is this? | ✅ Full | "加车报价 · 进度" card |
| What should I do? | ✅ Full | next_best_question + submit button |
| What happens next? | ⚠️ Partial | "办公室接手" mentioned but buried in rail |

**Score: 83**

---

## Page 4 — Handoff Pending (资料已齐)

| Question | Pass? | Evidence |
|----------|-------|----------|
| What is this? | ⚠️ Partial | Alert says 最后一步 but also contact-only hint |
| What should I do? | ❌ Fail | 回手机号 OR 确认提交 — two paths in 5s |
| What happens next? | ⚠️ Partial | Button subline explains queue |

**Score: 50**

---

## Page 5 — Post-Handoff Confirmation

| Question | Pass? | Evidence |
|----------|-------|----------|
| What is this? | ✅ Full | Green card + "已提交办公室处理" |
| What should I do? | ⚠️ Partial | Wait implied; append vs 提交新问题 unclear |
| What happens next? | ✅ Full | Processing line + office timing |

**Score: 83**

---

## Page 6 — Remove Car (via Dropdown)

| Question | Pass? | Evidence |
|----------|-------|----------|
| What is this? | ⚠️ Partial | Still add-car hero unless user already selected |
| What should I do? | ⚠️ Partial | Type in textarea after menu click |
| What happens next? | ❌ Fail | No remove-car-specific expectation |

**Score: 50**

---

## Page 7 — Upload Documents (via Dropdown)

| Question | Pass? | Evidence |
|----------|-------|----------|
| What is this? | ⚠️ Partial | "上传材料" label |
| What should I do? | ❌ Fail | No upload button — only text field |
| What happens next? | ❌ Fail | Unclear how documents reach office |

**Score: 33**

---

## Page 8 — Contact Human (联系人工)

| Question | Pass? | Evidence |
|----------|-------|----------|
| What is this? | ✅ Full | Starts conversation immediately |
| What should I do? | ✅ Full | Reply in textarea |
| What happens next? | ⚠️ Partial | Generic office follow-up |

**Score: 83**

---

## Page 9 — My Requests (Empty)

| Question | Pass? | Evidence |
|----------|-------|----------|
| What is this? | ✅ Full | "我的办理进度" |
| What should I do? | ✅ Full | Empty hint → go to 客户报送 |
| What happens next? | ⚠️ Partial | Loops to problematic landing |

**Score: 83**

---

## Page 10 — My Requests (With Active Case)

| Question | Pass? | Evidence |
|----------|-------|----------|
| What is this? | ✅ Full | Case title + status tag |
| What should I do? | ✅ Full | Blue next-step panel + CTA button |
| What happens next? | ✅ Full | formal_submitted_at visible |

**Score: 100**

---

## Page 11 — Global Chrome (Tabs Visible)

| Question | Pass? | Evidence |
|----------|-------|----------|
| What is this? | ⚠️ Partial | Brand OK; tab suffixes confuse |
| What should I do? | ❌ Fail | 4 tabs — which one? |
| What happens next? | ❌ Fail | No guidance at chrome level |

**Score: 33**

---

## Scoreboard

| Page | 5s Score | P16-M 10s | Target |
|------|----------|-----------|--------|
| Landing empty | **33** | 50 | ≥75 |
| Add-car first reply | **33** | — | ≥70 |
| Add-car mid-flow | **83** | — | ≥80 |
| Handoff pending | **50** | — | ≥75 |
| Post-handoff | **83** | 83 | ≥85 |
| Remove car | **50** | — | ≥70 |
| Upload documents | **33** | — | ≥70 |
| Contact human | **83** | — | ≥80 |
| My requests empty | **83** | — | ≥75 |
| My requests active | **100** | — | ≥85 |
| Global chrome | **33** | — | N/A (hide tabs) |

**Weighted average (customer critical path):** **~50** — matches P16-M baseline

---

## Fail Clusters (5-Second Specific)

1. **Landing:** Category grid before message — Typeform would show one question  
2. **Handoff pending:** Dual path (phone in chat vs confirm button) — Stripe would be one button  
3. **Upload materials:** Label promises upload; UI is text-only — trust break  
4. **Jargon:** 加车报价, 正式提交办公室, 服务记录 — needs plain Chinese or one-line gloss  
5. **Above-fold budget:** Hero + track + buttons consume 5s before textarea visible

---

## Pass Criteria for P16-N Success

| Metric | Current | Target |
|--------|---------|--------|
| Landing 5s score | 33 | ≥75 |
| Critical path average | ~50 | ≥75 |
| Pages scoring ≥75 | 4 / 11 | ≥8 / 11 |
| Zero-score questions | 6 | 0 |

---

*End of P16-N Phase 2 — Five Second Test*
