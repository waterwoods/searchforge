# Insurance Paid Pilot — Strict Execution Plan

**Created**: 2026-03-06  
**Phase**: Commercialization Sprint

---

## 1. Current Repo Status

| Component | Status | Path / Script |
|-----------|--------|---------------|
| Demo launcher | ✅ | `scripts/run_demo_local.sh` |
| Quick validate | ✅ | `scripts/demo_quick_validate.sh`, `scripts/demo_quick_validate.py` |
| One-click ingest | ✅ | `scripts/run_demo_ingest_oneclick.sh` |
| Demo prepare | ✅ | `scripts/demo_prepare_tomorrow.sh` |
| Deploy backend | ✅ | `scripts/deploy_rag_demo.sh` |
| Snapshot offline | ✅ | `scripts/snapshot_demo_answers.py` |
| Demo UI | ✅ | `ui/src/pages/DemoPage.tsx` |
| Query route | ✅ | `services/fiqa_api/routes/query.py` (mode=demo) |
| Search core | ✅ | `services/fiqa_api/services/search_core.py` (gov+insurer diversity) |
| Offline fallback | ✅ | `ui/src/assets/demo_fallback.json` + DEFAULT_FALLBACK_ITEMS |
| Frontend deploy | ❌ | Not automated |

---

## 2. Exact Docs Created/Updated

| Doc | Path | Purpose |
|-----|------|---------|
| Goal | `docs/goals/insurance_paid_pilot_goal.md` | Mission, scope, acceptance criteria |
| Business rules | `docs/business_rules/insurance_broker_pilot_rules.md` | Product rules, useful answer, must-nots |
| Release gate | `docs/release/insurance_demo_gate_v1.md` | Pre-demo checklist |
| Status report | `reports/openclaw/insurance_paid_pilot_report_v1.md` | Blockers, fixes, next actions |
| Execution plan | `docs/INSURANCE_PAID_PILOT_EXECUTION_PLAN.md` | This document |

---

## 3. Exact Blockers

1. **demo_quick_validate may FAIL** — Collection empty or stale. Fix: `run_demo_ingest_oneclick.sh`
2. **Frontend not deployed** — No public URL. Fix: Vercel or ngrok
3. **Cloud Run missing TRANSLATION_* env** — deploy_rag_demo.sh does not pass them. Fix: Add to ENV_VARS in deploy script

---

## 4. Minimum Patch List

| Patch | File(s) | Change |
|-------|---------|--------|
| P1 | `scripts/deploy_rag_demo.sh` | Add `TRANSLATION_ENABLED=1`, `TRANSLATION_PROVIDER=argos` to ENV_VARS |
| P2 | `ui/src/pages/DemoPage.tsx` | Change header to "陈奎专属 · 加州汽车保险智能助手" (or broker name) |
| P3 | `scripts/demo_quick_validate.py`, `demo_quick_validate.sh`, `snapshot_demo_answers.py` | Add 4th question (SR-22) and 5th (续保) — optional, 3 is minimum |

---

## 5. Live-Demo Gate Checklist

Before showing to broker, run:

```bash
cd /home/andy/searchforge

# 1. Demo runnable
bash scripts/run_demo_local.sh
# → Must print "Demo ready" and http://localhost:5173/demo

# 2. Validation pass
bash scripts/demo_quick_validate.sh
# → Exit 0; REPORT.md says "Overall: PASS"

# 3. Collection readiness (if validate fails)
bash scripts/run_demo_ingest_oneclick.sh

# 4. Fallback readiness
# → demo_fallback.json has 3+ items, or DEFAULT_FALLBACK_ITEMS used

# 5. Night before
bash scripts/demo_prepare_tomorrow.sh
```

---

## 6. 15-Minute Broker Demo Script

| Minute | Action |
|--------|--------|
| 0–2 | Open demo URL. Show title: "保险经纪人智能助手 — 陈奎版". Point out data sources (DMV, CDI, insurers). |
| 2–5 | Click Q1 (新车最低保险). Show bullets, steps, citations. Click "复制给客户（可直接发微信）". Paste into WeChat mock. |
| 5–8 | Click Q2 (注册暂停恢复). Show dmv.ca.gov citation. Emphasize "官方来源". |
| 8–11 | Click Q3 (合规查询). Show insurance.ca.gov. "客户问合规，直接查这里." |
| 11–13 | Type a custom question (e.g., SR-22 or 续保). Show results. |
| 13–15 | "您平时客户最常问哪几个问题？我们可以加进去。" Collect feedback. |

**Feedback questions to ask:**
1. 您客户最常问的 3 个问题是什么？
2. 您觉得哪些来源（DMV、保险公司）最有用？
3. 复制给客户的格式够用吗？需要改吗？
4. 您愿意付多少钱/月用这个？（如 $29、$49）
5. 您能给我们一句推荐语吗？

---

## 7. Division of Labor

| Task | Owner | Notes |
|------|-------|-------|
| Business direction, pricing, final approval | **Andy** | Non-delegable |
| Broker meeting, demo delivery | **Andy** | 15–30 min; use script |
| Strategy, copywriting, demo script wording | **ChatGPT** | Meeting notes, one-pagers, outreach copy |
| Code edits, scripts, setup, fixes, docs | **Cursor** | All repo changes |
| Validation, replay, repetitive checks, report generation | **OpenClaw** | demo_quick_validate, demo_prepare_tomorrow, ingest |

---

## 8. Next 10 Actions (In Order)

| # | Action | Owner |
|---|--------|-------|
| 1 | Run `bash scripts/demo_quick_validate.sh` — confirm PASS | Cursor / Andy |
| 2 | If FAIL: run `bash scripts/run_demo_ingest_oneclick.sh` | Cursor |
| 3 | Add TRANSLATION_* to `deploy_rag_demo.sh` ENV_VARS | Cursor |
| 4 | Rename DemoPage header for broker (e.g., 陈奎专属) | Cursor |
| 5 | (Optional) Add 5th question; update quick_validate + snapshot | Cursor |
| 6 | Run `bash scripts/demo_prepare_tomorrow.sh` night before demo | Andy |
| 7 | Deploy backend: `bash scripts/deploy_rag_demo.sh` | Andy |
| 8 | Deploy frontend (Vercel) or start ngrok; get shareable URL | Andy |
| 9 | Rehearse 15-min demo script | Andy |
| 10 | Schedule and run demo with broker; capture feedback | Andy |

---

*End of execution plan*
