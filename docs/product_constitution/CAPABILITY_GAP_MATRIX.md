# Capability Gap Matrix — P15

**Version:** P15  
**Date:** 2026-05-31  
**Sources:** P10 Final Audit, P11 Product Reality Audit (TOP_20_BLOCKERS, TOP_30_WORKBENCH), P14-A Founder Review / Conflict Report, P14-B Final Review  
**Rule:** Every row maps a known issue → capability → fix priority. No new product scope.

---

## Matrix

| Issue | Capability | Severity | ROI | Effort | Suggested Fix | Priority |
|-------|------------|----------|-----|--------|---------------|----------|
| Wrong default tab (客户报送 vs 办公室工作台) | 1 Front Door | Critical | Very High | Low (2h) | Default `?tab=broker`; read URL param on load | **P0** |
| Engineer UI: PG 镜像 / PG 缺失 / 镜像不一致 tags | 1 Front Door, 3 Case Record | Critical | Very High | Low (2h) | Hide in `isUnifiedIntakeProductOnlyUi()` | **P0** |
| API endpoint / 数据接口 visible in queue header | 1 Front Door | Critical | Very High | Low (2h) | Hide `API_BASE_URL` label in product_only | **P0** |
| 路由/指标 debug tag visible | 1 Front Door | Critical | Very High | Low (1h) | Conditional render off in product_only | **P0** |
| No broker wayfinding — four tabs, no start-here | 1 Front Door | Critical | Very High | Low (1h) | Banner: "经纪人：请在本页粘贴客户消息" | **P0** |
| Doc/UI split: trial assumes workbench; UI defaults Add-Car | 1 Front Door, 4 Intake | Critical | Very High | Low (2h) | Tab default + cancellation-first intro copy | **P0** |
| Day 1 unsupervised score 28/100 | 1 Front Door, 6 Trial Conversion | Critical | Very High | Medium | Sprint A bundle + optional Day 0 kickoff | **P0** |
| No proven time savings on real cases | 6 Trial Conversion | Critical | Very High | Medium (7d trial) | Observation log + ≥3 real cases + minutes field | **P0** |
| Pricing not on BROKER_ONE_PAGER | 6 Trial Conversion | Critical | Very High | Low (1h) | Publish $49 starter / $99 standard | **P0** |
| No 1-page pilot terms (Chinese) | 6 Trial Conversion | Critical | Very High | Low (4h) | Founder commercial doc in `docs/trial/` | **P0** |
| No invoice template | 6 Trial Conversion | Critical | High | Low (2h) | WeChat/PDF template for manual payment | **P0** |
| Production URL not validated | 7 Founder Control | Critical | Very High | Medium (4h) | `validate_pilot_deploy_env.py` + deploy + `/readyz` | **P0** |
| Script PASS ≠ broker-ready | 7 Founder Control | Critical | Very High | Low (3h) | Formal broker UX launch checklist (two-gate) | **P0** |
| Cases lost on refresh (non-Postgres) | 3 Case Record, 7 Founder Control | Critical | Very High | Medium (4h) | Postgres-primary prod; no JSON fallback presented as prod | **P0** |
| Simulation Assistant required in playbook but hidden | 1 Front Door, 6 Trial Conversion, 7 Founder Control | High | Very High | Medium (8h) | Inline 3 practice scenarios; update playbook | **P1** |
| Demo queue 15–30s load with no feedback | 1 Front Door | High | Very High | Low (3h) | Progress: "正在加载13条示例 (3/13…)" | **P1** |
| Cancellation not auto-opened after demo queue | 1 Front Door | High | Very High | Low (2h) | Select cancellation case on demo queue complete | **P1** |
| First-request loading missing ("broken" abandon) | 2 Triage, 4 Intake | High | Very High | Low (2h) | "首次分析约30秒" on first paste/triage | **P1** |
| Paste expectation copy missing | 4 Intake | High | High | Low (1h) | "原样粘贴微信/通知文字，不用整理" | **P1** |
| Add-Car-first banner vs cancellation-first trial | 1 Front Door, 4 Intake | High | High | Low (2h) | Collapse/replace PILOT_INTRO for trial mode | **P1** |
| Engineer queue filters (镜像异常, 旧识别, 测试, 正式) | 5 Lifecycle | High | High | Low (4h) | Simplify to 全部 / 需今天处理 / 24小时内 | **P1** |
| 更新客户新消息 not prominent | 4 Intake, 5 Lifecycle | High | High | Low (2h) | Highlight on case detail when selected | **P1** |
| Draft quality inconsistent on real messages | 3 Case Record | High | High | Medium (8h+) | Fix-now top 3 from trial log only | **P1** |
| Manual paste feels like extra work | 4 Intake, 2 Triage | High | High | Medium | Win cancellation speed; measure minutes | **P1** |
| SIM1–SIM3 in operator/broker materials | 7 Founder Control | High | High | Low (1h) | Remove from playbook + trial_launch output | **P1** |
| Observation log lacks "minutes saved" field | 6 Trial Conversion | High | High | Low (1h) | Extend `TRIAL_OBSERVATION_LOG_TEMPLATE.md` | **P1** |
| 503/warming on first paste with no message | 2 Triage, 7 Founder Control | High | High | Low (3h) | Graceful warming copy + recovery runbook | **P1** |
| Stale RAG goal docs mislead agents | 7 Founder Control | High | Medium | Low (1h) | Deprecate banner on `insurance_paid_pilot_goal.md` | **P1** |
| `.env.cloudrun` prod validation SKIP | 7 Founder Control | High | High | Medium (4h) | Complete prod probe in readiness check | **P1** |
| English "case" in broker-visible strings | 1 Front Door, 3 Case Record | Medium | Medium | Low (4h) | Replace with 服务记录 | **P2** |
| Pilot intro alert wall of text | 1 Front Door | Medium | Medium | Low (2h) | Collapse by default in production | **P2** |
| 我的办理 tab unclear in trial | 1 Front Door, 5 Lifecycle | Medium | Medium | Low (3h) | Hide in broker-only trial mode | **P2** |
| Too many queue tags on one card | 5 Lifecycle | Medium | Medium | Medium (4h) | Max 3 tags + expand | **P2** |
| chen_kui ui_copy.json not loaded | 3 Case Record | Medium | Medium | Medium (6h) | Wire client pack into UI labels | **P2** |
| Data retention post-trial unclear | 6 Trial Conversion | Medium | Medium | Low (0.5h) | State in pilot terms | **P2** |
| No testimonial captured | 6 Trial Conversion | Medium | Medium | Low (1h) | Day 7 quote field in observation log | **P2** |
| Assistant adoption playbook thin | 5 Lifecycle, 6 Trial Conversion | Medium | High | Low (2h) | 15-min assistant training script | **P2** |
| 复制案例快照 under-promoted | 3 Case Record, 7 Founder Control | Medium | Medium | Low (1h) | Support section in one-pager/playbook | **P2** |
| Mobile paste UX weak | 4 Intake | Low | Low | Medium (8h) | Desktop-only in terms OR mobile fix | **P3** |
| Monospace 服务记录编号 noise | 3 Case Record | Low | Low | Low (2h) | Short ID in list; full on detail | **P3** |
| Sticky 下一步 + draft on scroll | 3 Case Record | Low | Medium | Medium (4h) | Case detail layout | **P3** |
| Engineer sections on case detail | 3 Case Record | Low | Low | Medium (6h) | Collapse behind 高级 | **P3** |
| ChatGPT "good enough" for drafts | 2 Triage, 3 Case Record | Medium | High | Medium | Sell structure + queue in kickoff | **P2** (GTM) |
| Founder-only support bottleneck | 7 Founder Control | Medium | Medium | Low (2h) | L1 doc + 24h SLA in terms | **P2** |
| Downtime during business hours | 7 Founder Control | High | High | Medium | `/readyz` weekly + recovery script | **P1** |
| $199 tier expectations | 6 Trial Conversion | Medium | Medium | Low (0h) | Do not offer — constitution locked | **P2** (policy) |
| WeChat sync expectation | 4 Intake | High | High | Low (copy) | Explicit "manual paste v1" at every touchpoint | **P1** |
| RAG `/demo` in onboarding path | 1 Front Door, 7 Founder Control | Medium | Medium | Low (1h) | Demo URL = `/workbench/unified-intake` only | **P2** |
| Mixed 中文 + English nav ("Unified Intake") | 1 Front Door | Medium | Medium | Low (1h) | 中文-first product_only sidebar | **P2** |
| Demo vs real paste workflow unclear | 4 Intake | Medium | Medium | Low (2h) | Visual separation demo queue vs real paste | **P2** |
| Empty queue zero-state weak | 1 Front Door, 4 Intake | Medium | Medium | Medium (4h) | 3-step paste → review → copy | **P2** |
| Draft copy button label generic | 3 Case Record | Medium | Medium | Low (1h) | 复制到微信（请先修改） | **P2** |
| Rename 高风险 → 需当天处理 | 2 Triage, 5 Lifecycle | Medium | Medium | Low (1h) | CUSTOMER_LANGUAGE_GUIDE alignment | **P2** |
| Hide 管理 → 标为测试 from brokers | 5 Lifecycle | Medium | Low | Low (2h) | Founder-only build flag | **P2** |
| Local JSON demo without persistence disclaimer | 3 Case Record, 7 Founder Control | High | High | Low (2h) | Founder-only banner when not Postgres | **P1** |
| No completed Chen Kui trial | 6 Trial Conversion | Critical | Very High | High (7d) | Execute supervised trial Week 2 | **P0** (execution) |
| P13 sprint referenced but missing | 7 Founder Control | Low | N/A | N/A | Do not invent — use P10/P11 only | **—** |

---

## Severity × Capability Heat Map

| Capability | P0 | P1 | P2 | P3 |
|------------|----|----|----|-----|
| 1 Front Door | 6 | 5 | 6 | 0 |
| 2 Triage | 0 | 3 | 1 | 0 |
| 3 Case Record | 1 | 1 | 5 | 3 |
| 4 Intake | 1 | 4 | 3 | 1 |
| 5 Lifecycle | 0 | 2 | 4 | 0 |
| 6 Trial Conversion | 5 | 2 | 5 | 0 |
| 7 Founder Control | 4 | 6 | 3 | 0 |

---

## P10 Discovery Index (Cross-Reference)

| P10 # | Issue | Matrix row |
|-------|-------|------------|
| 2 | Doc/UI split | Wrong default tab |
| 3 | Simulation hidden | Inline practice scenarios |
| 4 | Engineer artifacts | PG/API/debug hide |
| 7 | Manual paste real workflow | Paste expectation copy |
| 10 | SIM1–SIM3 leak | Remove from broker materials |
| 12 | ui_copy.json not loaded | chen_kui pack |
| 13 | full_stack ≠ prod | Prod validation |
| 14 | .env.cloudrun SKIP | Prod probe |
| 15 | Postgres required | Cases persist |
| 20 | Confusion > algorithm | Front door cluster |

---

## P11 Blocker Index (Cross-Reference)

| P11 # | Blocker | Matrix row |
|-------|---------|------------|
| 1 | No time savings proof | Observation log + trial |
| 2 | Unstable prod URL | Deploy + `/readyz` |
| 3 | Cases lost | Postgres-primary |
| 4 | Draft quality | Fix-now from trial |
| 5 | Paste extra work | Cancellation win + copy |
| 6 | Wrong first screen | Default broker tab |
| 7 | Engineer UI | Chrome purge |
| 8–10 | Commercial gaps | Pricing, terms, invoice |
| 12 | No kickoff | Day 0 30-min call |
| 13 | Add-car vs cancellation | Story alignment |
| 14 | Assistant adoption | Training script |

---

*End of Capability Gap Matrix — P15*
