# Capability Contract 03 — Structured Case Record

**Capability:** Structured Case Record  
**Version:** V1 Ratified  
**Date:** 2026-05-31  
**Maps to:** Capability Map V1 §3

---

## SECTION 1 — Purpose

Why this capability exists.

Persist and present **one office-ready service record** the broker can act on immediately: Case focus, Your next move, Collected, Still needed, urgency, and an **editable client reply draft**.

P11 competitive audit: the moat is **insurance-specific case structure**, not generic AI drafts alone. This capability answers "What is this about?" in one view.

---

## SECTION 2 — Primary User

Who uses it.

| User | Usage |
|------|-------|
| **Broker owner** | Reads case card; edits draft; copies to WeChat |
| **Office assistant** | Same workflow for daily paste/triage |
| **Founder** | Reviews case snapshot for L2 support |

---

## SECTION 3 — Inputs

What enters the capability.

| Input | Source |
|-------|--------|
| Triage output | Urgent Message Triage (6-field) |
| Broker notes | Manual entry on case |
| Follow-up messages | Reopen + paste updates same record |
| Persistence layer | Postgres (prod) or local JSON (demo only) |

---

## SECTION 4 — Outputs

What must come out.

| Output | Broker-facing label |
|--------|---------------------|
| Case focus | 本案焦点 |
| Your next move | 下一步 |
| Collected | 已收集 |
| Still needed | 还缺 |
| Urgency badge | 需当天处理 / 24小时内 / 常规 |
| `client_reply_draft` | Editable draft — broker copies to WeChat |
| Human confirmation badge | When AI collected data needs verify |
| Case ID | 服务记录编号 (short in list, full on detail) |

**Draft rules:** Professional tone; bilingual acceptable; broker always edits before send; never auto-send.

---

## SECTION 5 — Success Metrics

How success is measured.

| Metric | Target | Source |
|--------|--------|--------|
| Case card completeness | All 4 broker fields populated on scenario pack | UNIFIED_INTAKE_MVP_STANDARD |
| Draft copied with edits | ≥2 times during 7-day trial | TRIAL_ONE_PATH |
| Broker trust | Day 7: draft "good starting point" not "rewrite from scratch" | Observation log |
| Persistence | Cases survive refresh on prod Postgres | CURRENT_PRODUCT_SHAPE |
| Competitive differentiation | Broker names insurance structure vs ChatGPT | P11 competitive audit |

---

## SECTION 6 — Acceptance Criteria

How we know it works.

- [ ] Case card shows Case focus, Your next move, Collected, Still needed per MVP standard  
- [ ] Editable draft present on every triaged case  
- [ ] Draft copy button: 复制到微信（请先修改）  
- [ ] Prod cases persist in Postgres across sessions  
- [ ] Reopen retains prior Collected / Still needed context  
- [ ] Human confirmation badge when manual_followup_needed  
- [ ] No engineer internal labels (workbench_lane_kind, quote_ready_status) visible in product_only  

---

## SECTION 7 — Current State

Score **0–100** today.

### Score: **72 / 100**

| Dimension | Score | Notes |
|-----------|-------|-------|
| Case structure | 85 | Insurance-specific fields strong |
| Draft generation | 70 | Quality varies on real messages |
| Persistence (prod) | 75 | Postgres path exists; validation incomplete |
| Persistence (local) | 50 | JSON demo loses trust if presented as prod |
| Label consistency | 65 | Mixed EN/ZH ("case") |
| Draft UX | 78 | Editable + copy works |
| Client pack tuning | 55 | chen_kui pack exists; ui_copy not loaded |

**P11 reference:** Product core (engine) 85; case structure is competitive moat.

---

## SECTION 8 — Gap Analysis

What's missing.

| Gap | Severity |
|-----|----------|
| Draft quality inconsistent on real messages | **P1** |
| Local JSON demo presented without persistence disclaimer | **P1** |
| PG 镜像 engineer labels on case cards | **P0** (Front Door overlap) |
| English "case" in broker-visible strings | **P1** |
| chen_kui ui_copy.json not loaded | **P2** |
| Sticky 下一步 + draft on scroll | **P2** |
| Monospace 服务记录编号 noise in list | **P2** |
| Engineer sections on case detail | **P3** |

---

## SECTION 9 — Top 10 Improvements

Ranked.

| # | Improvement | ROI |
|---|-------------|-----|
| 1 | Fix-now: top 3 draft failures from trial log (cancellation, missing doc priority) | Payment blocker #4 |
| 2 | Load chen_kui ui_copy.json into draft/case labels | Client pack exists unused |
| 3 | Replace "case" with 服务记录 in broker-visible strings | Language consistency |
| 4 | Draft copy button: 复制到微信（请先修改） | Reinforces control |
| 5 | Sticky 下一步 + draft on case detail scroll | Action always visible |
| 6 | Short 服务记录编号 in list; full on detail | Less monospace noise |
| 7 | Human confirmation badge prominence | Trust on AI-collected data |
| 8 | Collapse engineer sections behind "高级" on case detail | Power users only |
| 9 | Prominent 复制案例快照 for support escalation | L2 speed |
| 10 | Prod-only banner when not on Postgres (founder builds only) | Prevent trust kill |

---

## SECTION 10 — Must Not Build

Prevent scope creep.

- Full CRM customer profile on case record  
- Auto-send draft to WeChat  
- In-product OCR to populate case fields  
- Carrier policy PDF parsing  
- Multi-page case wizard redesign  
- Version history / audit trail for enterprise  
- Custom fields per broker (v1)  
- Rich text / HTML draft editor  
- AI "confidence score" exposed to broker (engineer metric)  
- Separate draft-only SKU without case structure  

---

*End of Capability Contract 03*
