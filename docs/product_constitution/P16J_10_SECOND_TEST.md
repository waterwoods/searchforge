# P16-J 10-Second Test

**Date:** 2026-05-31  
**Persona:** Cold arrival — no training, no documentation, no founder  
**URL:** `/workbench/unified-intake` with `VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1`  
**Baseline comparison:** P16-H audit scored **~25/100** (1/4 questions partial pass)

---

## Questions (cold user)

| Question | P16-H (pre-I) | P16-J (post-I) | Evidence |
|----------|---------------|----------------|----------|
| **What is this?** | ⚠️ Partial — Add-Car tagline | ✅ **Yes** — 「粘贴客户消息 · 整理草稿 · 您确认后发送」 + 办公室工作台 · 客户消息整理 | `UnifiedIntakePage.tsx`, `ui_copy` trial keys |
| **Who is it for?** | ❌ Two tabs, ambiguous | ⚠️ **Partial** — Chen Kui avatar + 经纪人 wayfinding; no explicit「经纪人专用」 | Branding implies one office |
| **What should I click?** | ❌ Tabs + demo above paste | ✅ **Yes** — Paste textarea + **开始整理** in first column; optional demo below | `BrokerWorkbenchTab` Col order=1 paste |
| **Why should I care?** | ❌ No success visual | ⚠️ **Partial** — 取消/付款风险优先 + 不自动发送; no screenshot of draft outcome | Copy only, no mock |

**Pass rate: 2.5 / 4** (one partial on who + why)

---

## First viewport (1440×900, product_only)

Expected elements without scroll:

1. Dark app header (金盾·陈魁团队) — **noise**
2. White product card: avatar + trial tagline — **good story**
3. **No tab bar** — major win vs P16-H
4. Paste card title **粘贴客户消息** + textarea + **开始整理** — **primary**
5. Wayfinding alert (one line) — helpful, slight duplication
6. **快速体验（可选）** with 加载演示队列 — secondary, below paste on wide layout

**First actionable control:** Paste or **开始整理** — **not** wrong tab.

**Focal points above fold:** ~4 (header chrome, brand block, paste, wayfinding) — target ≤3; **borderline pass**.

---

## Score

| Dimension | Weight | Score |
|-----------|--------|-------|
| Product identity in 10s | 30% | 78 |
| Audience clarity | 20% | 62 |
| Primary CTA obvious | 30% | 82 |
| Value / trust in 10s | 20% | 68 |
| **Weighted total** | | **74** |

**Rounded headline score: 72 / 100** (conservative; no live eye-tracking)

| Benchmark | Score |
|-----------|-------|
| P16-H cold test | ~25 |
| P16-I target gate | ≥75 |
| **P16-J assessment** | **72–74** — **near gate**, not full 75 on cold persona |

---

## Cold persona outcomes

| Persona | 10s outcome | Likely action |
|---------|-------------|---------------|
| Chen Kui (broker) | Understands paste tool | Pastes or loads demo |
| Office assistant | Slightly slower | Finds paste with one scan |
| End customer (wrong URL) | N/A — customer tab hidden | — |
| Investor / guest on **Preview URL** | **FAIL** — Vercel login wall | Bounce |

---

## Deployment caveat (critical)

10-second test applies to **built product_only bundle only**.  
**Vercel Preview (401 SSO)** and **Production (pre-P16-I)** **fail** the test before UI renders.

---

## Fix cluster (acceptance — not building this sprint)

If pushing 72 → 80 without features:

1. Merge wayfinding + trust into one line.
2. Demote **快速体验** to link under paste empty state.
3. Add one-line hero: 「粘贴微信消息 → 整理草稿 → 您复制发出」

---

*End of P16-J 10-Second Test*
