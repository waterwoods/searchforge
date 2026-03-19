# Insurance Broker Pilot — Business Rules

**Created**: 2026-03-06  
**Scope**: California Auto Insurance Broker Assistant — paid pilot v1

---

## 1. What This Product Must Do for the Broker

| Rule | Description |
|------|-------------|
| **R1** | Answer client-like questions in Chinese (e.g., 新车最低保险, 注册暂停恢复, 合规查询) |
| **R2** | Return authoritative sources: ≥1 gov domain (dmv.ca.gov, insurance.ca.gov) and ≥1 insurer domain when possible |
| **R3** | Provide copy-to-client-ready format: bullets, steps, citations — suitable for pasting into WeChat |
| **R4** | Support offline fallback: 5 sample questions load pre-saved answers when backend is down |
| **R5** | Translate Chinese queries to English for search; translate results back to Chinese for display |

---

## 2. What Counts as a Useful Answer

| Criterion | Threshold |
|-----------|-----------|
| **Sources** | ≥3 results; ≥2 with non-empty snippet |
| **Diversity** | ≥1 gov domain; ≥1 insurer domain (when collection has both) |
| **Citations** | Each source has `url` and `domain` for client-facing copy |
| **Format** | Bullets (3) + steps (≤5) extractable for "复制给客户" |

---

## 3. What Must NOT Happen in a Live Demo

| Rule | Description |
|------|-------------|
| **N1** | No blank screen or uncaught error — use Offline fallback if backend down |
| **N2** | No "Collection not found" — ensure `auto_insurance_demo_core` exists and has data |
| **N3** | No raw English-only results when broker asked in Chinese — translation must be on |
| **N4** | No all-gov or all-insurer results for mixed queries — diversity fallback must apply |
| **N5** | No 500/504 without graceful degradation — Offline mode must work |

---

## 4. What Can Be Manual in the First Paid Pilot

| Area | Manual Approach |
|------|-----------------|
| **Payment** | Zelle / Venmo / WeChat; send invoice PDF |
| **Onboarding** | Email with URL + 3 steps + 5 questions |
| **Support** | WeChat / email; no ticketing |
| **Terms** | One-pager; paste in email |
| **Deploy** | Manual `deploy_rag_demo.sh`; manual frontend deploy or ngrok |

---

## 5. What Should Be Deferred

| Area | Reason |
|------|--------|
| **Stripe / Paddle** | Manual payment sufficient for v1 |
| **Multi-tenant auth** | Single broker pilot |
| **LLM answer generation** | Retrieval + snippets enough |
| **Usage limits / rate limiting** | Not needed for 1 broker |
| **Billing dashboard** | Manual tracking |
| **China / Europe regions** | California only for now |
| **Agent workflows** | Retrieval-only is sufficient |

---

## 6. Validation Rules (Enforced by demo_quick_validate.py)

| Rule | Check |
|------|-------|
| **ok** | API returns `ok: true` |
| **results>=3** | `sources.length >= 3` |
| **sources>=2** | `sources.length >= 2` |
| **snippets>=2** | ≥2 sources have non-empty snippet/text |
| **gov_domain** | ≥1 domain is dmv.ca.gov, insurance.ca.gov, or *.ca.gov |
| **insurer_domain** | ≥1 domain is geico.com, progressive.com, usaa.com, etc. |

---

*End of business rules*
