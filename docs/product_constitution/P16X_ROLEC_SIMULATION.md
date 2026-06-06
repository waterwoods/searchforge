# P16-X Phase 1 — Role C Simulation

**Date:** 2026-06-01  
**Persona:** Role C — cold user, no product knowledge, no founder explanation  
**Method:** Live browser on deployed Preview only (no localhost, no code assumptions)  
**URL:** https://ui-waterwoods-andys-projects-1f411b73.vercel.app/workbench/unified-intake

---

## Setup

| Fact | Observed |
|------|----------|
| Cold HTTP | 200 — no Vercel SSO (fixed since P16-V/W) |
| Default surface | **Broker workbench** (`product_only`; customer tab absent) |
| First paint | Brand card「金盾·陈魁团队 · 客户统一受理」+ paste textarea +「开始整理」 |
| Test message | DMV cancellation / SR-22 scenario (Chinese) |

---

## 1. What does the user think the product does?

**Honest read:** A **back-office message organizer** for「陈魁团队」— paste WeChat or notice text, get a structured summary and a draft reply.

**Not obvious:**
- Whether the user is supposed to be the **broker** or the **customer** (title says「客户统一受理」but instructions say「粘贴客户消息」).
- Whether anything is sent automatically (footer clarifies「不自动对外发送」— but only if user scrolls past brand card).
- What happens to the message after submit (no timeline, no「办公室会联系您」for a customer-shaped visitor).

**Score — 10-second comprehension:** **48 / 100**  
Better than Production customer portal (P16-Q: 35), worse than a dedicated landing page. User guesses「insurance office internal tool」not「consumer app.」

---

## 2. What happens after first submit?

| Step | Experience |
|------|------------|
| Click「开始整理」| Textarea locks ~30s; loading copy not always visible without scroll |
| Result appears | Below fold:「整理结果（办公室一眼）」three-step glance, Chinese draft, orange/green urgency border |
| Primary actions | **复制客户草稿** (prominent); 整理明细 / 客户草稿 collapses |
| Paste area | Still visible above result; hint text switches to「本条已整理…可继续粘贴下一条」 |
| Queue | Unchanged unless user scrolled to「待处理」and clicked a row |
| Persist | Case ID shown (short monospace); no celebration, no「done」state |

**Critical gap:** After first submit the product **stops talking**. No single line says: copy draft → send in WeChat → when customer replies, do X.

**Score — post-submit clarity:** **42 / 100**

---

## 3. What is unclear?

| # | Confusion | Severity |
|---|-----------|----------|
| 1 | Am I the broker or the customer? | **Critical** |
| 2 | Is my job finished after copy, or do I wait inside this page? | **Critical** |
| 3 | How do I add a follow-up when the customer answers? (Append UI not visible on fresh triage) | **Critical** |
| 4 | Why is「办公室主行动」sometimes English while UI is Chinese? | High |
| 5 | What is「快速体验（可选）」vs just pasting? | High |
| 6 | Demo queue loads 12 cases in 15–30s — looks like the product is broken or duplicating rows | High |
| 7 | Queue previews in English for demo cases | Medium |
| 8 |「状态」hidden in kebab — lifecycle invisible | Medium |
| 9 | Multiple collapses (整理明细 / 更多状态标签 / 结构化字段) — which to open? | Medium |
| 10 |「清空」vs paste next message — conflicting mental models | Medium |

---

## 4. What causes abandonment?

| Abandon trigger | When | Probability |
|-----------------|------|-------------|
| **Value without continuation** | User copies draft, switches to WeChat — never returns | **High** |
| **30s first wait** | Cold user with no patience context | High |
| **Wrong persona** | Customer opens broker URL, cannot「报送」 | High (if link mis-shared) |
| **Scroll fatigue** | Result below paste + demo + queue; never sees draft | Medium |
| **English in glance** | Trust drop for Chinese-only user | Medium |
| **No empty-state story** | Blank paste box — no「paste one cancellation notice to try」 | Medium |
| **Demo queue noise** | 12 duplicate-looking rows after load | Medium |

**Abandonment verdict:** Most users **complete one turn** (paste → copy) then **leave the product permanently** for WeChat. The UI does not pull them back.

---

## Role C composite (deployed Preview)

| Dimension | Score |
|-----------|-------|
| First impression | 48 |
| Post-submit clarity | 42 |
| Trust | 55 |
| Would return unprompted | 28 |
| **Overall Role C** | **43 / 100** |

**Threshold for unsupervised readiness (≥70): NOT MET**

---

## Delta vs prior sprints

| Claim | P16-X reality |
|-------|---------------|
| P16-I Role C ~58 (authenticated broker) | Confirmed for **supervised** broker path |
| P16-Q Role C 42 (trial reality) | **43** — Preview SSO fixed; single-turn gap dominates |
| P16-O customer 92 (local only) | **Zero weight** — customer tab not on Preview |

---

*End of P16-X Phase 1 — Role C Simulation*
