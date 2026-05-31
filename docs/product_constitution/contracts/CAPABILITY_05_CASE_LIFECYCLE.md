# Capability Contract 05 — Case Lifecycle Management

**Capability:** Case Lifecycle Management  
**Version:** V1 Ratified  
**Date:** 2026-05-31  
**Maps to:** Capability Map V1 §5

---

## SECTION 1 — Purpose

Why this capability exists.

Queue, prioritize, reopen, and continue cases across the broker office workday. Ensures **nothing urgent is buried** and follow-up messages update the same record without starting over.

Includes **light customer identity v1**: session/case continuity only — **no CRM**. Reopen + paste follow-up is the identity model.

---

## SECTION 2 — Primary User

Who uses it.

| User | Usage |
|------|-------|
| **Broker owner** | Manages Work now / Waiting queue; reopens cases Monday morning |
| **Office assistant** | Daily queue scan; follow-up paste on existing cases |
| **Founder** | Reviews queue state via case snapshot for support |

---

## SECTION 3 — Inputs

What enters the capability.

| Input | Source |
|-------|--------|
| Structured cases | From Structured Case Record |
| Broker status updates | Work now / Waiting; notes |
| Follow-up pastes | 更新客户新消息 on existing case |
| Session/case ID | Light continuity — not full CRM profile |
| Time fields | waiting_on / next_contact_by (where present) |

---

## SECTION 4 — Outputs

What must come out.

| Output | Requirement |
|--------|-------------|
| Prioritized queue | Same-day action cases surface first |
| Work now / Waiting split | Broker-facing queue lanes |
| Queue card preview | 下一步 visible without opening case |
| Reopen context | Prior Collected / Still needed retained |
| Follow-up merge | New paste updates same 服务记录 |
| Notes / activity | Broker notes persist on case |
| Readiness labels | 当日处理 / 需核实收到 on queue cards |

---

## SECTION 5 — Success Metrics

How success is measured.

| Metric | Target | Source |
|--------|--------|--------|
| Same-day cases first | Cancellation visible at top of Work now | Demo queue + real paste |
| Monday-morning scenario | Broker names queue workflow by Day 7 | TRIAL_ONE_PATH |
| Follow-up continuity | ≥1 reopen + paste during trial | Trial success criteria |
| Queue scan time | Broker finds urgent case in &lt;30s | Observation log |
| Assistant adoption | Assistant uses queue independently by Day 5 | P11 hidden multiplier |

---

## SECTION 6 — Acceptance Criteria

How we know it works.

- [ ] Work now queue shows same-day / cancellation cases first  
- [ ] Queue cards show 下一步 preview without opening detail  
- [ ] 已收集 / 还缺 chips visible on queue or detail  
- [ ] Reopen case + paste follow-up updates same record in Postgres  
- [ ] Broker can move case between Work now and Waiting  
- [ ] Queue filters simplified: 全部 / 需今天处理 / 24小时内 (product_only)  
- [ ] No engineer filters (镜像异常, 旧识别, 测试, 正式) in broker trial mode  

---

## SECTION 7 — Current State

Score **0–100** today.

### Score: **55 / 100**

| Dimension | Score | Notes |
|-----------|-------|-------|
| Queue existence | 75 | Work now / Waiting works |
| Prioritization | 70 | Same-day logic present |
| Queue UX | 45 | Too many tags; engineer filters |
| Follow-up workflow | 55 | Reopen works; 更新客户新消息 buried |
| Session continuity | 60 | Case IDs exist; no CRM profile (by design) |
| Assistant playbook | 40 | Thin adoption script |
| Mobile queue | 40 | Desktop-first |

**P11 reference:** Office workflow Partial; trial UX and wayfinding weak.

---

## SECTION 8 — Gap Analysis

What's missing.

| Gap | Severity |
|-----|----------|
| Too many queue tags on one card | **P2** |
| Engineer queue filters meaningless to broker | **P1** |
| 更新客户新消息 not prominent | **P1** |
| Assistant adoption playbook thin | **P1** |
| 我的办理 tab purpose unclear | **P2** |
| No self-serve friction log in UI | **P2** |
| Mobile UX weak | **P3** |
| waiting_on / next_contact_by under-promoted | **P2** |

---

## SECTION 9 — Top 10 Improvements

Ranked.

| # | Improvement | ROI |
|---|-------------|-----|
| 1 | Simplify queue filters → 全部 / 需今天处理 / 24小时内 | Remove engineer noise |
| 2 | Highlight 更新客户新消息 when case selected | Follow-up discoverability |
| 3 | Reduce queue card tags (max 3 + expand) | Scanability |
| 4 | 15-min assistant training script in trial pack | Doubles office ROI |
| 5 | 下一步 preview on queue cards (verify prominence) | Monday-morning speed |
| 6 | Rename queue urgency labels per CUSTOMER_LANGUAGE_GUIDE | Clarity |
| 7 | Hide 管理 → 标为测试 from non-founder builds | Less misuse |
| 8 | Empty Work now state: "paste urgent message here" CTA | Habit formation |
| 9 | Log reopen events in observation template | Trial measurement |
| 10 | Sticky queue summary: "X 需今天处理" | At-a-glance urgency |

---

## SECTION 10 — Must Not Build

Prevent scope creep.

- Full CRM customer profiles  
- Customer linking across offices  
- Multi-user assignment / routing engine  
- SLA timers / escalation automation  
- Calendar integration  
- Task management / project boards  
- Carrier workflow sync  
- Automated follow-up reminders (SMS/email)  
- Per-broker custom queue taxonomy  
- Enterprise audit log / compliance export  

---

*End of Capability Contract 05*
