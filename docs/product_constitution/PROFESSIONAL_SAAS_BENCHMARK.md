# P16-H Phase 5 — Professional SaaS Benchmark

**Date:** 2026-05-31  
**Subject:** Unified Intake product_only UI vs Stripe, Linear, Calendly, Notion, Superhuman  
**Method:** Component audit + SaaS UX patterns (not feature parity)  
**Constraint:** Evaluation only

---

## Benchmark Summary

| Dimension | Unified Intake (trial) | Stripe | Linear | Calendly | Notion | Superhuman |
|-----------|------------------------|--------|--------|----------|--------|------------|
| **Information density** | Very high | Low | Medium | Low | Medium | Low |
| **Cognitive load** | High | Low | Low | Very low | Medium | Low |
| **Decisions before value** | 4–9 | 0–1 | 0–1 | 1 | 1–2 | 0 |
| **Clicks to first value** | 3–6 | 1–2 | 1–2 | 2–3 | 2 | 1 |
| **Trust signals** | Mixed | Strong | Strong | Strong | Neutral | Strong |
| **Clarity of purpose** | Weak | Strong | Strong | Strong | Medium | Strong |
| **Overall SaaS grade** | **D+** | A | A | A | B+ | A |

**Target for paid pilot:** B- minimum on all dimensions. Current: fails clarity and cognitive load.

---

## 1. Information Density

### Unified Intake
- **Broker workbench:** 7 focal regions on landing; case detail 10+ elements
- **Customer entry:** 9+ focal regions on empty state
- **Copy volume:** ui_copy.json entries average 2–3 sentences per label; many redundant trust lines

### Benchmarks
| Product | Pattern |
|---------|---------|
| **Stripe** | One metric, one chart, one action per dashboard cell. Whitespace is trust. |
| **Linear** | Issue list: title + status dot. Detail opens on click. |
| **Calendly** | One booking link, one calendar. Zero secondary cards on landing. |
| **Notion** | Dense when user builds; empty page is literally blank + "Type /". |
| **Superhuman** | Inbox zero aesthetic — one compose, one list. |

**Gap:** Unified Intake shows **everything at once** (queue + paste + practice + demo + detail + CRM fields). Professional SaaS **progressive disclosure**.

**Score:** Unified Intake **3/10** vs benchmark average **8/10**

---

## 2. Cognitive Load

### Unified Intake
- Dual tabs with conflicting stories (Add-Car vs paste-triage)
- English product vocabulary ("Case", "Unified Intake") mixed with Chinese broker UI
- Multiple copy buttons, status radios, collapses — each requires classification decision
- Engineer concepts leak: 服务记录编号, formal_submitted_at, lifecycle_status

### Benchmarks
| Product | Load reduction |
|---------|----------------|
| **Stripe** | Smart defaults; merchant never sees API concepts |
| **Linear** | Keyboard-first; one primary action per view |
| **Calendly** | Host vs guest — separate URLs, never mixed |
| **Notion** | Templates optional; blank page zero decisions |
| **Superhuman** | Split inbox auto-sorts; user doesn't classify |

**Gap:** Broker must classify **which tab**, **which button**, **which copy action**, **which follow-up field** before sending one WeChat reply.

**Score:** Unified Intake **4/10** vs benchmark **8/10**

---

## 3. Number of Decisions

### Path to first draft (broker, Day 0)

| Step | Decision |
|------|----------|
| 1 | Which tab? (2 options) |
| 2 | Demo queue or paste? (2 options) |
| 3 | Practice scenario or raw paste? (4 options) |
| 4 | Click 开始整理 | 
| 5 | Scroll to draft |
| 6 | 复制客户草稿 or 复制摘要? (2 options) |

**Total: 6 decisions, 4–6 clicks** (best case)

### Benchmark paths

| Product | Decisions to core value |
|---------|-------------------------|
| **Stripe** | View payment (0) or create link (2 fields) |
| **Linear** | Cmd+K → type → enter (1) |
| **Calendly** | Pick time slot (1) |
| **Notion** | Type (0) |
| **Superhuman** | Cmd+K → reply (1) |

**Target:** ≤2 decisions, ≤3 clicks for broker paste → draft.

**Score:** Unified Intake **5/10**

---

## 4. Number of Clicks

| Workflow | Unified Intake | Stripe equiv | Linear equiv |
|----------|--------------|--------------|--------------|
| First cancellation draft | 4–6 | 2 | 2 |
| Copy draft to clipboard | 2 (open case + click) | 1 | 1 |
| Append client follow-up | 4+ (find buried section) | N/A | 2 |
| Load demo | 1 (+ 30s wait) | N/A | N/A |

**Score:** Unified Intake **5/10**

---

## 5. Trust

### Unified Intake — trust positives
- 「不自动对外发送」in intro (when expanded)
- Chen Kui branding / avatar — local office feel
- Wayfinding banner explains manual paste
- No auto-send in engine (verified)

### Unified Intake — trust negatives
- Add-Car-first copy → "wrong product" signal
- English "Case" labels → unfinished
- **返回工作台** → broken wayfinding in product_only
- Too many buttons → "complex = risky" for non-technical broker
- Vercel SSO on preview → can't even reach product
- No pricing on page → commercial trust gap (Cap 6)

### Benchmarks
| Product | Trust mechanism |
|---------|-----------------|
| **Stripe** | Minimal UI + SOC badges + instant feedback |
| **Linear** | Speed + polish = competence |
| **Calendly** | Recognizable pattern (pick time) |
| **Notion** | Familiar blank page |
| **Superhuman** | Opinionated simplicity = "they thought of everything" |

**Score:** Unified Intake **6/10** (engine trust high, surface trust mixed)

---

## 6. Clarity

### The 5-second question: "What does this product do?"

| Product | Answer in 5s |
|---------|--------------|
| **Stripe** | "Payments for my business" |
| **Linear** | "Track issues" |
| **Calendly** | "Book meetings" |
| **Notion** | "Write / organize" |
| **Superhuman** | "Email fast" |
| **Unified Intake** | ❌ "加车报价？客户报送？办公室？Paste?" |

**Root cause:** Product tries to be **customer portal + broker workbench + demo lab** in one URL.

**Constitution says:** paste → case → draft → you send.  
**UI says:** 加车报价为当前旗舰流程.

**Score:** Unified Intake **3/10**

---

## Composite Benchmark Score

| Dimension | Weight | UI Score | Benchmark avg |
|-----------|--------|----------|---------------|
| Information density | 15% | 3 | 8 |
| Cognitive load | 20% | 4 | 8 |
| Decisions | 20% | 5 | 8 |
| Clicks | 15% | 5 | 8 |
| Trust | 15% | 6 | 9 |
| Clarity | 15% | 3 | 9 |
| **Weighted** | | **4.4 / 10 (44%)** | **8.2 / 10** |

---

## What Each Benchmark Would Do First

| Product | #1 change to Unified Intake |
|---------|----------------------------|
| **Stripe** | Remove every element that isn't paste → draft → copy |
| **Linear** | Single inbox list; detail on click; keyboard shortcuts |
| **Calendly** | Split customer vs broker URLs entirely |
| **Notion** | Blank paste page; structure appears after first input |
| **Superhuman** | One compose box; AI structures silently |

**Consensus:** **One door, one action, one outcome visible.**

---

## Paid Pilot Bar

To reach **B- (75/100)** on this benchmark:

1. Hide customer tab (trial)
2. Replace Add-Car copy with cancellation-first one-liner
3. Paste above fold, sole primary CTA
4. Case detail: draft + one copy button only
5. Remove English labels and CRM controls from Day 1

Estimated lift: **44% → 72%** on composite — without new features.

---

*End of P16-H Phase 5 — Professional SaaS Benchmark*
