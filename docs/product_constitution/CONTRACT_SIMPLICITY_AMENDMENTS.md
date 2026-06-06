# P16-H Phase 7 — Contract Simplicity Amendments

**Date:** 2026-05-31  
**Scope:** Capability 1 (Broker Front Door) + Capability 4 (Customer Intake Collection)  
**Rule:** Do NOT create Capability 8. Propose **additional acceptance criteria** only.  
**Authority:** Constitution V1 locked — amendments are contract §6 additions for future sprint closure

---

## Executive Summary

Current contracts specify **functional** acceptance (correct tab, paste works, loading copy). They do **not** specify **simplicity** acceptance — which is why Sprint A can pass checklist items while still scoring **58/100** on simplicity and failing the 10-second cold-user test.

**Recommendation:** Add §6 simplicity criteria to Cap 1 and Cap 4. No new capability required — simplicity is part of "broker reaches value without founder translation."

---

## Capability 1 — Broker Front Door

### Existing §6 (summary)
- Broker tab default ✅ (shipped)
- Engineer chrome hidden ✅ (shipped)
- Demo queue progress ✅ (shipped)
- Cancellation auto-open ✅ (shipped)
- Wayfinding banner ✅ (shipped)

### Gap
Contract validates **mechanism** not **comprehension**. Chen Kui can land on correct tab and still not know what to do in 10 seconds.

### Proposed Additional Acceptance Criteria

#### Simplicity — First viewport (product_only)

- [ ] **S1.** Primary action (paste textarea OR explicit「粘贴客户消息」CTA) visible **without scroll** on 1440×900 and 390×844 viewports  
- [ ] **S2.** ≤ **3** distinct visual focal points above fold on broker workbench empty state (excluding global header)  
- [ ] **S3.** Zero English product vocabulary visible in broker walkthrough screenshot (`Case`, `Unified Intake` as user-facing labels)  
- [ ] **S4.** Tab labels ≤ **4 Chinese characters** each OR single-word labels; **no suffix subtitles** in product_only  
- [ ] **S5.** Header/tagline copy aligns with cancellation-first wedge (constitution §7) — zero「加车旗舰/主路径」in broker-first viewport  

#### Simplicity — Decision budget

- [ ] **S6.** Cold user reaches paste textarea in ≤ **1 click** from broker tab landing (0 clicks preferred)  
- [ ] **S7.** Decisions before first「开始整理」≤ **2** (paste text + click analyze) on Day 0 path  
- [ ] **S8.** **返回工作台** and other lab escape links hidden in product_only  

#### Simplicity — Trial mode surface

- [ ] **S9.** ≤ **2 tabs** visible in product_only trial configuration (recommend 1: workbench only)  
- [ ] **S10.** Onboarding cards above paste (demo, practice, intro) ≤ **1** combined card OR paste appears **above** onboarding  

#### Simplicity — Case detail (broker)

- [ ] **S11.** **复制客户草稿** is the single primary CTA on opened case; secondary actions in overflow menu  
- [ ] **S12.** Case detail default view shows **glance summary + draft** without expanding collapses  
- [ ] **S13.** Status radio / CRM fields not visible in product_only default case view  

### Proposed §5 Metric Additions

| Metric | Target |
|--------|--------|
| 10-second cold-user comprehension | ≥3/4 questions (product, user, button, success) |
| Simplicity score (P16-H rubric) | ≥75/100 on deployed preview |
| Focal points above fold | ≤3 |

### Must Not Build (unchanged + clarify)

- No Capability 8 "UI Simplicity" — criteria live here in Cap 1  
- No redesign sprint that adds tabs/features — deletions only  

---

## Capability 4 — Customer Intake Collection

### Existing §6 (summary)
- Broker paste raw text ✅
- Paste expectation copy ✅
- Case in queue after triage ✅
- Add-Car portal works but not default path ⚠️ (UI still promotes Add-Car)

### Gap
Contract says Add-Car is secondary GTM but **ui_copy.json** still makes it primary on customer surface. No acceptance test for **message-first** or **decision budget** on customer portal.

### Proposed Additional Acceptance Criteria

#### Simplicity — Customer portal (when tab visible)

- [ ] **S1.** Empty state: message textarea is **first interactive control** above fold  
- [ ] **S2.** Category buttons / workflow track **not visible** until after first message OR behind「更多办理类型」  
- [ ] **S3.** ≤ **2** focal points on customer empty state (headline + textarea)  
- [ ] **S4.** Headline describes **problem domain** (取消/缺材料/加车/账单) not **workflow maturity** ("最成熟路径")  

#### Simplicity — Trial configuration

- [ ] **S5.** product_only trial: customer portal either **hidden** OR shows banner「经纪人请用办公室工作台」  
- [ ] **S6.** Zero numbered multi-step instructions (①②③) on empty state  

#### Simplicity — Broker paste path (Cap 4 § primary)

- [ ] **S7.** Paste-to-case: **one** loading message visible; no silent spinner >5s  
- [ ] **S8.** Follow-up paste (**追加客户补充**) discoverable in ≤ **2 clicks** from opened case (target: 1 click, same viewport as draft)  

#### Simplicity — Copy alignment

- [ ] **S9.** All Cap 4 touchpoints use「原样粘贴微信/通知文字，不用整理」or equivalent — no conflicting Add-Car-first strings in same viewport as broker paste  

### Proposed §5 Metric Additions

| Metric | Target |
|--------|--------|
| Wrong-surface paste (broker pastes on customer tab) | 0 in observation log |
| Customer empty-state decision count | ≤1 before first keystroke |
| Message-first compliance (hybrid or hidden tab) | Founder sign-off |

### Must Not Build (unchanged + clarify)

- WeChat sync, OCR, etc. unchanged  
- **Do not** expand customer portal feature set to fix simplicity — **hide/reorder/delete** only  

---

## Cross-Capability Simplicity Gate (Founder UX Checklist)

Add to **Capability 7** reference (not new cap) — broker UX gate before Day 0:

| Gate | Source caps | Pass |
|------|-------------|------|
| 10-second audit | Cap 1 | ≥3/4 |
| Simplicity score | Cap 1 + 4 | ≥75 |
| TOP 20 deletions shipped | Cap 1 + 4 | ≥15/20 |
| ui_copy cancellation alignment | Cap 1 + 4 | Founder screenshot sign-off |

---

## Why Not Capability 8?

| Argument | Response |
|----------|----------|
| Simplicity is cross-cutting | So is "trust" — already in Cap 1 §4 outputs |
| Engineering might ignore | Acceptance criteria in existing contracts are enforceable at sprint close |
| New cap = scope creep | Constitution §90-day rule: no new capabilities |

Simplicity is **part of front door** (can broker enter?) and **part of intake** (can user submit without confusion?).

---

## Implementation Notes (Future Sprint)

| Amendment pack | Files | Effort |
|----------------|-------|--------|
| Cap 1 §6 additions | `CAPABILITY_01_BROKER_FRONT_DOOR.md` | Doc only — P16-H proposes, founder ratifies |
| Cap 4 §6 additions | `CAPABILITY_04_INTAKE_COLLECTION.md` | Doc only |
| ui_copy alignment | `configs/clients/chen_kui/ui_copy.json` | 2h |
| Conditional hides | `UnifiedIntakePage.tsx`, `BrokerWorkbenchTab.tsx`, `CustomerEntryTab.tsx` | 8–12h |

**P16-H does not modify contracts** — this document is the ratification proposal.

---

*End of P16-H Phase 7 — Contract Simplicity Amendments*
