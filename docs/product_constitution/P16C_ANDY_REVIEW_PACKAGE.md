# P16-C Andy Review Package

**Date:** 2026-05-31  
**For:** Andy (Founder) — 10-minute review path  
**Sprint:** A Broker Front Door (`c2e3dff`)

---

## 1. Preview URL

| URL | Use for review? |
|-----|-----------------|
| **Vercel Sprint A Preview** | ❌ **Does not exist yet** — run deploy command below first |
| Production `https://ui-smoky-beta.vercel.app/workbench/unified-intake` | ❌ **Old UI** — wrong tab, Simulation visible |
| Local (engineer only) | `http://127.0.0.1:4173/workbench/unified-intake` after product_only build |

**Create Preview now:**

```bash
cd /home/andy/searchforge/ui && source ../scripts/with_node22_path.sh
vercel deploy --yes \
  -b VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1 \
  -b VITE_API_BASE_URL=https://fiqa-api-g7zatxrycq-uw.a.run.app
```

Open the URL Vercel prints → `/workbench/unified-intake`

---

## 2. What Changed Visually

- Opens **办公室工作台** first (not 客户报送)
- Hides **我的办理** and **场景仿真**
- Hides PG tags, API URL, engineer filters
- Shows **「经纪人：请在本页粘贴客户消息」** banner
- Paste helper: **原样粘贴微信/通知文字，不用整理**
- **3 inline practice buttons** (取消/付款风险, 缺材料, 加车)
- **加载演示队列** with progress text; auto-opens cancellation case when API works
- Product intro **collapsed** by default; cancellation-first copy when expanded

---

## 3. Before / After (One Line)

**Before:** Broker lands on Add-Car customer tab, sees lab chrome, can't train without Simulation.  
**After:** Broker lands on workbench, paste-first, demo cancellation path, no engineer labels.

---

## 4. What Andy Should Click (5-Minute Path)

1. Open Preview URL (after deploy) → confirm **办公室工作台** already selected
2. Read wayfinding banner → find paste box without tab switching
3. Click **加载演示队列** → watch progress → confirm **cancellation case** opens with 下一步 + draft
4. Click **取消/付款风险** practice → **开始整理** → confirm case card appears
5. Scan queue header — confirm **no** API URL, PG tags, or 镜像异常 filters
6. Toggle filters (if queue loaded): **全部 / 需今天处理 / 24小时内** only

---

## 5. What Andy Should Ignore

- ~1,345 dirty git files (reduction/archive) — not part of Sprint A
- Production URL until redeployed with env vars
- Triage engine edge cases (address change = unclear) — post-trial fix-now
- Sprint B items: pricing, terms, invoice
- Sidebar lab routes on **non-product_only** local dev builds

---

## 6. What Still Feels Broken

| Issue | Severity |
|-------|----------|
| No Vercel Preview for `sprint-a/broker-front-door` | **P0** |
| `VITE_UNIFIED_INTAKE_PRODUCT_ONLY` not in Vercel env | **P0** |
| Production still old UI | **P0 for share** |
| Demo queue may fail if CORS missing Preview origin | **P0 on deploy** |
| Tab suffix still「加车旗舰路径」 | P1 copy |
| Payment-failure draft sometimes English | P1 engine |
| Address change triage weak | P2 engine |

---

## 7. Ready for Chen Kui Preview?

**Not yet.** Need:

1. Vercel Preview with Sprint A + product_only env  
2. Andy 5-minute dry-run PASS on that URL  
3. Demo queue E2E confirmed  
4. Optional: 30-min kickoff script still recommended Day 0  

**After Preview PASS:** OK for **supervised** Chen Kui preview (founder on screen), not unsupervised Day 1 alone until dry-run logged.

---

## 8. Ready for Production?

**NO.** Do not merge/deploy Production until:

- Preview review PASS  
- Vercel Production env includes `VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1`  
- CORS `ALLOWED_ORIGINS` includes production + preview origins  
- Cap 7 prod validation (`/readyz`, Postgres) — parallel track  

---

## 9. Recommended Next Action

**Option C from Go/No-Go:** Deploy Preview → Andy review → fix P0 if any → then merge.

```bash
# 1. Preview deploy (see §1)
# 2. Andy dry-run checklist (see §4)
# 3. If PASS → open PR sprint-a → main OR vercel deploy --prod with env
```

---

*End of P16-C Andy Review Package*
