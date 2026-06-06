# P16-E Phase 5 — AI Simulation Against Preview

**Date:** 2026-05-31  
**Input:** Deployed Preview bundle evidence + P16-C local simulation + guardrail PASS  
**Preview:** https://ui-fvxlrxp4u-andys-projects-1f411b73.vercel.app/workbench/unified-intake  
**Constraint:** Simulation assumes product_only UI as baked in Preview; API/CORS on live Preview not fully exercised

---

## Persona A — Chen Kui (Broker Owner)

**Profile:** Busy owner; only cares if this saves time; payment decision Day 7.

| Horizon | Journey | Scores (clarity / trust / speed / confusion⁻ / trial / payment) |
|---------|---------|------------------------------------------------------------------|
| **First 30s** | Opens Preview (after Vercel login). Lands on workbench tab, sees wayfinding + paste. No Simulation tab. | 4 / 3.5 / 3.5 / 3 / 3.5 / 3 |
| **First 5 min** | Clicks「加载演示队列」or pastes cancellation text. If API works: sees 下一步 + draft → value moment. Tab suffix still Add-Car flavored. | 4 / 3.5 / 4 / 3.5 / 4 / 3.5 |
| **Day 1** | Uses paste for 2–3 real messages. Empty queue on first visit may hide filters. | 4 / 3 / 3.5 / 3 / 4 / 3 |
| **Day 7** | Would pay if daily time saved ≥15 min and no API surprises. Needs proof on real messages. | 4 / 3.5 / 4 / 3.5 / 4 / 3.5 |

**Chen Kui composite: 72 / 100** (weight 50%)

---

## Persona B — Office Assistant

**Profile:** 50+ messages/day; needs queue scan + clear next action.

| Horizon | Journey | Scores (avg /5 → ×20) |
|---------|---------|------------------------|
| **First 30s** | Same entry as broker — good for shared office. | 4 / 3.5 / 3 / 3.5 / 3.5 |
| **First 5 min** | Filters (全部/需今天处理/24小时内) help when queue populated. `broker_next_step` on cards helps scan. | 4 / 3.5 / 3.5 / 3.5 / 3.5 |
| **Day 1** | Paste + 开始整理 works; loading copy reduces anxiety.「更新客户新消息」still buried. | 4 / 3.5 / 3.5 / 3 / 3.5 |
| **Day 7** | Adopts if broker mandates; otherwise parallel WeChat habit persists. | 3.5 / 3.5 / 3.5 / 3.5 / 3.5 |

**Assistant composite: 70 / 100** (weight 30%)

---

## Persona C — End Customer (Indirect)

**Profile:** Messy WeChat; no insurance terms; experiences broker replies only.

| Horizon | Journey | Scores |
|---------|---------|--------|
| **First 30s** | N/A (no UI) | — |
| **First 5 min** | Broker finds paste box quickly on Preview → faster structured reply. | 4 / 4 / 4 / 4 / 4 |
| **Day 1** | Better cancellation/doc-chase drafts (guardrail-backed). | 4 / 4 / 4 / 4 / 4 |
| **Day 7** | Notices broker responds faster with fewer repeat questions. | 4 / 4 / 4 / 4 / 4 |

**Customer indirect composite: 80 / 100** (weight 20%)

---

## Aggregate AI Simulation Score

| Persona | Weight | Score |
|---------|--------|-------|
| Chen Kui | 50% | 72 |
| Assistant | 30% | 70 |
| Customer | 20% | 80 |
| **Weighted average** | | **73 / 100** |

Threshold ≥70 for simulated GO: **met**, contingent on Andy live Preview + API from browser.

---

## TOP_10_REMAINING_CONFUSIONS

1. Vercel SSO/login before seeing product — friction for non-technical broker
2. Tab suffix still「加车旗舰路径」— cancellation wedge copy lag
3. Header tagline Add-Car-first
4. 客户报送 tab still visible — wrong-tab risk
5. Empty queue hides urgency filters on first load
6. Demo queue may fail if Preview origin CORS not allowlisted on Cloud Run
7.「我的办理」/「场景仿真」strings exist in bundle — support confusion if env regresses
8. Uncommitted `ui/` files in deploy — unknown delta vs `c92cabf` for Andy
9. Production still pre-Sprint A — comparison trips if Andy opens wrong URL
10. Payment value prop not explicit in UI (Day 7 conversion)

---

## TOP_10_THINGS_IMPROVED

1. Real Preview URL exists for Sprint A (first time)
2. `VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1` baked into Preview bundle
3. Correct Cloud Run API URL in bundle
4. Default workbench tab (product_only) vs Production 客户报送
5. Simulation / 我的办理 tabs hidden at runtime
6. Wayfinding banner for paste-first workflow
7. Improved paste placeholder (原样粘贴微信)
8. Inline 3 practice scenarios (取消/付款风险, 缺材料, 加车)
9. First-triage loading copy (首次分析约30秒)
10. Demo queue button + progress strings present

---

## TOP_10_BLOCKERS_BEFORE_CHEN_KUI

1. Andy has not completed authenticated 5-min Preview walkthrough
2. Deployment Protection — broker trial URL must be public or bypass configured
3. Preview env vars not saved in Vercel dashboard (repeat-deploy risk)
4. Demo queue E2E not verified from Preview origin → Day 1 empty/broken feel
5. CORS allowlist for new Preview hostname on API (if blocked)
6. Uncommitted `ui/` deploy artifact — should clean before merge
7. Production still wrong surface — must not send Chen Kui to `ui-smoky-beta` yet
8. Add-Car copy wedge — trust gap for cancellation-first trial
9. No completed real-broker trial record (Cap 6)
10. Merge + Production deploy explicitly out of scope until Andy approves

---

*End of P16-E Phase 5*
