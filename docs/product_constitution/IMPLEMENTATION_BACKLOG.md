# Implementation Backlog — P15

**Version:** P15  
**Date:** 2026-05-31  
**Rule:** Every task maps to ratified capability contracts. Grouped into four implementation sprints aligned with `ROADMAP_FROM_CONSTITUTION.md`.

---

## Sprint A — Broker Front Door

**Goal:** Cap 1 score 35 → 75; unsupervised Day 1 ≥ 70.

| Task | Why | Acceptance Criteria | Risk | Est. Hours |
|------|-----|---------------------|------|------------|
| A1. Default `?tab=broker` on trial URL | P10 #2, P11 #6 — wrong tab kills Day 1 | URL opens 办公室工作台 without click; `?tab=broker` in share link | Low | 2 |
| A2. Read `tab` query param on page load | Deep links and founder share URL | `UnifiedIntakePage` respects `?tab=broker\|customer` | Low | 1 |
| A3. Hide PG mirror tags in product_only | P10 #4 — "beta / not for me" | Zero PG 镜像/缺失/不一致 visible when `VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1` | Low | 2 |
| A4. Hide API endpoint / 数据接口 in product_only | P11 workbench #2 | No localhost/API URL in broker queue header | Low | 2 |
| A5. Hide 路由/指标 debug tag | P11 workbench #4 | Tag absent in product_only | Low | 1 |
| A6. Broker wayfinding banner | P11 #5 — replaces tab confusion | One-line 中文 banner above paste area | Low | 1 |
| A7. Auto-open cancellation after demo queue | P10 top action #6 — first value | After 加载演示队列, cancellation case selected | Medium — case ID drift | 2 |
| A8. Demo queue progress indicator | P10 risk #9 — 30s "broken" | Progress text during seed load (e.g. 3/13) | Low | 3 |
| A9. First-request loading copy on paste/triage | P11 #10 — abandon prevention | "首次分析约30秒" shown on first analyze | Low | 2 |
| A10. Paste expectation copy | P10 #7 — manual paste is v1 | Placeholder/helper: 原样粘贴微信/通知文字 | Low | 1 |
| A11. Collapse pilot intro / cancellation-first copy | P14-B residual Add-Car ambiguity | Intro collapsed default; trial copy mentions cancellation wedge | Medium — copy review | 2 |
| A12. Inline 3 practice scenarios panel | P10 #3 — Simulation hidden | Broker can run 3 scenarios without Simulation tab | Medium — UI scope | 8 |
| A13. Hide 我的办理 tab in broker trial mode | P11 #26 — single front door | Tab hidden when product_only + trial flag | Low | 3 |
| A14. Simplify queue filters in product_only | P11 #14 — engineer filters | 全部 / 需今天处理 / 24小时内 only | Low | 4 |
| A15. Hide engineer filter legend / PG glossary | P11 engineer leftovers | Broker-visible legend cleaned | Low | 2 |

**Sprint A total:** ~34 hours (~5 dev days)

---

## Sprint B — Trial Conversion

**Goal:** Cap 6 score 45 → 65 pre-trial; 80 post-trial evidence.

| Task | Why | Acceptance Criteria | Risk | Est. Hours |
|------|-----|---------------------|------|------------|
| B1. Add $49/$99 to BROKER_ONE_PAGER | P11 blocker #10 | Pricing visible on customer-facing one-pager | Low | 1 |
| B2. 1-page pilot terms (Chinese) | P11 blocker #9 | PDF/md in broker's hands before Day 0 | Medium — legal review | 4 |
| B3. Invoice template (WeChat/PDF) | P11 blocker #8 | Founder can send $49 or $99 invoice in &lt;5 min | Low | 2 |
| B4. Observation log "minutes saved" field | P11 proof layer #1 | Template updated; example row filled in dry-run | Low | 1 |
| B5. Update TRIAL_ONE_PATH + playbook — no Simulation | P10 #3, #10 | Playbook steps match prod UI; no SIM1–SIM3 | Low | 2 |
| B6. 15-min assistant training script | P11 blocker #14 — $99 tier | Doc in `docs/trial/`; kickoff checklist item | Low | 2 |
| B7. Day 7 value questions + payment script | TRIAL_ONE_PATH | Founder script for invoice vs ranked blockers | Low | 1 |
| B8. Data retention clause in terms | P11 blocker #16 | Explicit post-trial case handling | Low | 0.5 |
| B9. L1 support + 24h SLA in terms | P11 blocker #19 | WeChat + response commitment documented | Low | 2 |
| B10. Draft copy button label | P11 #15 — trust | 复制到微信（请先修改） on case detail | Low | 1 |
| B11. Promote 复制案例快照 in one-pager | P10 #17 | Support escalation path documented | Low | 1 |

**Sprint B total:** ~17.5 hours (~2 founder days + 2 eng hours)

---

## Sprint C — Lifecycle

**Goal:** Cap 5 score 55 → 70; Monday-morning queue usable by Day 7.

| Task | Why | Acceptance Criteria | Risk | Est. Hours |
|------|-----|---------------------|------|------------|
| C1. Highlight 更新客户新消息 on case detail | P11 #16 — follow-up buried | CTA visible when case selected | Low | 2 |
| C2. Verify 下一步 preview on queue cards | P11 valuable list | Preview readable without opening case | Low | 1 |
| C3. Reduce queue card tags (max 3 + expand) | P11 #18 — scanability | Cards scannable in &lt;3s | Medium | 4 |
| C4. Rename urgency labels per language guide | P11 #19 | 需当天处理 replaces 高风险 where shown | Low | 1 |
| C5. Empty Work now CTA | Habit formation | Zero-state prompts real paste | Low | 2 |
| C6. Sticky 下一步 + draft on scroll | P11 #21 | Action visible on long case detail | Medium | 4 |
| C7. Log reopen events in observation template | Trial measurement | Field for follow-up paste count | Low | 0.5 |
| C8. Hide 管理 → 标为测试 from brokers | P11 #25 | Founder-only actions | Low | 2 |

**Sprint C total:** ~16.5 hours (Week 2–3; partial overlap Sprint A filters)

---

## Sprint D — Intake Collection

**Goal:** Cap 4 score 62 → 80; paste path trusted and measured.

| Task | Why | Acceptance Criteria | Risk | Est. Hours |
|------|-----|---------------------|------|------------|
| D1. Graceful 503/warming message | P14-B risk #16 | User sees retry guidance, not blank error | Medium | 3 |
| D2. Separate demo vs real paste visually | P11 confusing list | Demo queue distinct from real paste area | Low | 2 |
| D3. Empty queue 3-step onboarding | P11 #23 | paste → review → copy visible at zero state | Medium | 4 |
| D4. Apply CUSTOMER_LANGUAGE_GUIDE in triage→UI | Cap 2 gap | Category labels match broker Case focus | Medium | 4 |
| D5. Load chen_kui ui_copy.json | P10 #12 | Client pack labels in UI | Medium | 6 |
| D6. Replace "case" with 服务记录 | P11 #8 | No English "case" in product_only strings | Low | 4 |
| D7. Mobile paste area (optional) | P11 #29 — P3 | Only if phone-first office confirmed | High scope | 8 |
| D8. Log paste source in observation template | Trial analytics | real vs demo tagged | Low | 0.5 |

**Sprint D total:** ~31.5 hours (D7 optional/deferred)

---

## Sprint 7 Overlap — Founder / Operator (Cross-Cutting)

Not a separate product sprint — gates Sprint A–B.

| Task | Why | Acceptance Criteria | Risk | Est. Hours |
|------|-----|---------------------|------|------------|
| O1. Formal broker UX launch checklist | P10 #13 two-gate | Checklist doc + PASS/FAIL before URL sent | Low | 3 |
| O2. `validate_pilot_deploy_env.py` PASS | P11 blocker #2 | Validator green | Medium — env | 2 |
| O3. Deploy paid pilot + `/readyz` | P11 blocker #2–3 | `intake_path_ready`; cases persist | High — outage | 4 |
| O4. Founder dry-run with observation log | P10 action #10 | Playbook Day 0 without founder translation | Low | 2 |
| O5. Remove SIM1–SIM3 from broker materials | P10 #10 | No SIM refs in broker-facing output | Low | 1 |
| O6. Deprecate banner on stale RAG goal doc | P14-A surprise #5 | Agent anti-drift | Low | 1 |
| O7. Weekly `/readyz` during trial | Uptime confidence | Logged probe results | Low | 1 |

**Operator total:** ~14 hours

---

## Backlog Summary

| Sprint | Focus | Capability | Hours | Week |
|--------|-------|------------|-------|------|
| **A** | Broker Front Door | 1, 4 (partial), 5 (filters) | ~34 | 1 |
| **B** | Trial Conversion | 6, 7 (docs) | ~17.5 | 1 end |
| **C** | Lifecycle | 5, 3 (partial) | ~16.5 | 2–3 |
| **D** | Intake Collection | 4, 2 (labels), 3 (copy pack) | ~31.5 | 2–3 |
| **O** | Founder Control gates | 7 | ~14 | 1 parallel |

**14-day minimum path:** Sprint A + O + Sprint B commercial (B1–B5) + supervised trial — defer most of C/D unless trial log demands fix-now.

---

*End of Implementation Backlog — P15*
