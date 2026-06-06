# P16-J Founder Walkthrough

**Date:** 2026-05-31  
**Persona:** Andy (founder) — first-time approval lens  
**Method:** Code-path verification + local stack (`run_demo_local.sh`, product_only) + API scenarios + synthesis with P16-I shipped UI; live browser blocked (Cursor browser cannot reach `127.0.0.1`; Vercel Preview returns 401 SSO)  
**Build:** `901b0df` on `sprint-a/broker-front-door`

---

## Walkthrough script (10 steps)

| Step | Action | Result | Notes |
|------|--------|--------|-------|
| 1 | Open `/workbench/unified-intake` | ✅ Pass (local) | Single workbench surface; no 客户报送 / 场景仿真 tabs in product_only |
| 2 | Understand product | ✅ Pass | Tagline: 「粘贴客户消息 · 整理草稿 · 您确认后发送」; subtitle mentions 取消/付款风险 |
| 3 | Paste cancellation message | ✅ Pass | Rules/LLM triage → `cancellation_warning`, critical, draft |
| 4 | Paste missing document message | ✅ Pass | `missing_document`, medium, actionable draft |
| 5 | Paste add-car request | ✅ Pass | Chinese draft with 待补充 fields |
| 6 | Load demo queue | ✅ Pass | 加载演示队列 + progress; 13 seeds; guardrail-backed |
| 7 | Open cancellation case | ✅ Pass | Auto-open cancellation case after queue load (founder demo path) |
| 8 | Copy draft | ✅ Pass | Single primary **复制客户草稿**; 复制摘要 hidden in product_only |
| 9 | Append customer follow-up | ✅ Pass | **追加客户补充** promoted near glance (P16-I) |
| 10 | Reopen later | ⚠️ Partial | Case persists locally; prod persistence + stable URL not validated this sprint |

---

## Step-by-step — confusions, delights, questions

### 1–2. Open page / Understand product

**Delights**

- No tab bar paralysis — one door.
- Cancellation wedge in header copy, not Add-Car flagship.
- Trust line visible: 不自动对外发送.

**Confusions**

- Dark **金盾·陈魁团队** app header still feels like a dev shell around a white product card.
- Avatar + team name — implies account/login; there is none.
- Wayfinding Alert + trust line slightly duplicate the same message.

**Questions**

- Is this for Chen Kui or for any broker office? (Branding says Chen Kui — OK for pilot, odd for second broker.)

### 3–5. Paste three message types

**Delights**

- Paste card is **first column** (order=1 on xl); no scroll to find textarea on desktop.
- Inline practice buttons (取消/付款风险, 缺材料, 加车报价) pre-fill paste — fast demo.
- Loading copy「首次分析约30秒」sets expectation.
- Engine quality unchanged — drafts are copy-ready.

**Confusions**

- **快速体验（可选）** card sits above paste in DOM order for product_only layout — paste is right column first on wide screens, but on mobile queue/demo may still compete (order 2 vs 1).
- English notice → English draft; Andy must mentally translate for WeChat — acceptable for demo, risky on real Chinese threads without edit habit.
- **开始整理** disabled when case already open — label shift to「已打开」needs one failed click to learn.

**Questions**

- Will Cloud Run stay warm enough that 30s is rare? (Local cold start OK with message.)

### 6–7. Demo queue + cancellation case

**Delights**

- One card merges demo + practice scenarios (P16-I).
- Progress N/13 during load — professional patience signal.
- Cancellation case surfaces same-day urgency + next move — North Star value moment in &lt;5 min.

**Confusions**

- Still two paths on Day 0: **加载演示队列** vs paste — Andy knows to paste; Chen Kui might only click demo.
- Queue title **待处理** — good; empty left column until load can feel broken before first action.

**Questions**

- Does Preview deploy auto-open the same case? (Code yes; needs Andy confirm on Vercel after login.)

### 8. Copy draft

**Delights**

- One primary copy button — decision paralysis removed.
- Draft expanded by default; 整理明细 collapsed — payoff visible.

**Confusions**

- Long case detail still requires scroll on laptop to reach draft on very long cases.
- Monospace case ID visible — engineer signal (low).

### 9. Append follow-up

**Delights**

- **追加客户补充** near glance — P16-H P0 addressed.
- Append API path guardrail-tested.

**Confusions**

- Multiple activity labels (续接此处, 最近更新) if lab strings leak in edge cases — mostly hidden in product_only.
- Re-open from queue vs new paste — two mental models remain.

### 10. Reopen later

**Delights**

- Local Postgres/SQLite persistence works in demo mode.

**Confusions**

- Sending **Preview URL** to Chen Kui hits Vercel SSO — product never loads (P16-G known).
- **Production URL** shows wrong UI entirely.

**Questions**

- When do we promote `901b0df` + env flags to a broker-stable URL without SSO?

---

## Summary table

| Category | Count | Top items |
|----------|-------|-----------|
| **Confusions** | 8 | Dark shell; demo vs paste; English draft; SSO on Preview URL |
| **Delights** | 10 | Single surface; paste-first copy; one copy CTA; demo progress; triage quality |
| **Questions** | 5 | Preview deploy parity; prod promote; warm API; second-broker branding |

---

## Andy walkthrough verdict (this sprint)

**Local product_only:** Andy can complete the full loop without founder translation — **pass**.  
**Vercel Preview URL:** **not validated** — requires Andy hard-refresh after SSO + confirm P16-I bundle deployed.

---

*End of P16-J Founder Walkthrough*
