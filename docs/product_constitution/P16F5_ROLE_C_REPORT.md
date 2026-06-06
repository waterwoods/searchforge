# P16-F.5 Phase 4 — Role C Simulation

**Date:** 2026-05-31  
**Persona:** Role C — confused real user; no founder guidance  
**Preview:** https://ui-fvxlrxp4u-andys-projects-1f411b73.vercel.app/workbench/unified-intake  
**Constraint:** Automation blocked at Vercel SSO; scores combine P16-F inference + P16-F.5 revalidation (CORS still unfixed)

---

## Role C definition

Per sprint brief: a user who must **discover value without founder translation** — not the hidden Simulation-tab LLM customer bot (`role_c_simulation_service.py`), but the **unsupervised broker/client experience** of opening the trial URL cold.

---

## First 30 seconds

**Journey:** Open link → Vercel login (if unauthenticated) → land on workbench.

| Observation | Impact |
|-------------|--------|
| SSO wall before product | Immediate friction; "is this a dev site?" |
| After login: 办公室工作台 selected | Good — no tab hunt |
| Wayfinding + paste visible | Good — finds entry in &lt;10s |
| Header/tagline still Add-Car flavored | Mild confusion vs cancellation wedge |
| 客户报送 tab still visible | Wrong-path risk |
| Queue area empty or loading | Neutral until error |

| Dimension | Score /5 |
|-----------|----------|
| Clarity | 3.5 |
| Trust | 3.0 |
| Speed to orient | 3.5 |
| Would continue | 3.0 |

**First 30 seconds composite: 65 / 100**

---

## First 5 minutes

**Journey:** Wait for queue → try paste → 开始整理 → expect draft.

| Observation | Impact |
|-------------|--------|
| **Network Error** on queue load | Instant "broken" signal |
| CORS hint mentions production alias | May open **wrong** (pre-Sprint A) URL |
| Paste works but triage fails same CORS path | Cannot prove value |
| Practice scenario buttons don't bypass API | Same failure |
| 加载演示队列 fails | No cancellation value moment |
| No pricing / trial terms on screen | Payment path invisible |

| Dimension | Score /5 |
|-----------|----------|
| Clarity | 2.0 |
| Trust | 1.5 |
| Speed | 1.0 |
| Would continue | 1.5 |
| Would pay | 1.0 |

**First 5 minutes composite: 28 / 100**

---

## First 15 minutes

**Journey:** Retry refresh, explore tabs, attempt demo queue, consider leaving.

| Observation | Impact |
|-------------|--------|
| Repeated Network Error | Abandon likely |
| 客户报送 tab → Add-Car portal | Reinforces wrong product mental model |
| No founder to explain CORS | User blames product quality |
| Cannot copy draft to WeChat | Core loop broken |
| Would tell colleague "don't bother" | Negative word-of-mouth |

| Dimension | Score /5 |
|-----------|----------|
| Clarity | 2.5 |
| Trust | 2.0 |
| Would continue | 2.0 |
| Would pay | 1.5 |

**First 15 minutes composite: 38 / 100**

---

## Qualitative answers

| Question | Answer |
|----------|--------|
| **What confuses me?** | Login wall; Network Error; Add-Car labels on a cancellation product; two tabs when I was told "paste here" |
| **What delights me?** | Clean paste box copy; broker tab already selected; practice scenario labels (if API worked) |
| **Would I continue?** | **No** — cannot complete one successful triage |
| **Would I quit?** | **Yes** — within 5 minutes |
| **Would I pay?** | **No** — no demonstrated time savings |

---

## Score summary

| Horizon | Score /100 | vs P16-F | vs P16-E (CORS-fixed assumption) |
|---------|------------|----------|----------------------------------|
| First 30 seconds | **65** | +30 (UI shell better characterized) | −8 |
| First 5 minutes | **28** | −7 | −45 |
| First 15 minutes | **38** | +10 | −35 |
| **Overall Role C** | **40 / 100** | +5 | −33 |

Threshold for unsupervised trial readiness: **≥70** — **NOT MET**.

---

## If CORS were fixed (reference only — not measured live)

P16-E estimated Role-C-weighted simulation **73/100** when API works. Current **40/100** implies ~**33 points** lost primarily to Preview CORS + access friction, not Sprint A UI regressions.

---

*End of P16-F.5 Phase 4*
