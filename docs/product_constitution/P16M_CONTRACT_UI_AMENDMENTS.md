# P16-M Phase 7 — Capability Contract UI Amendments

**Date:** 2026-06-01  
**Scope:** Capability 01 (Broker Front Door) · Capability 04 (Intake Collection) — **UI clauses only**  
**Constraint:** Amendments propose UI simplicity; **do not change capability scope or Constitution**

---

## Capability 01 — Broker Front Door

### Existing UI-Related Clauses (summary)

| Section | Current requirement |
|---------|---------------------|
| §4 Outputs | Clean broker surface; no PG/API/debug; wayfinding one-line; demo progress; trust footer |
| §6 Acceptance | Default 办公室工作台; hide engineer chrome; inline 3 scenarios; collapse intro |
| §9 Improvements | Default tab, hide labels, wayfinding, demo progress, collapse intro |

### Proposed UI Simplicity Amendments

**Amendment 01-A — Single Primary Action**  
Add to §4 Outputs:

> The broker empty state shall expose **exactly one** primary button above the fold: paste submission (开始整理). Demo queue and practice scenarios shall be **secondary** (link or collapsed panel), never equal visual weight to paste.

*Scope unchanged:* Demo queue remains available; only presentation tightens.

---

**Amendment 01-B — Chrome Consolidation**  
Add to §4 Outputs:

> Product-only mode shall use **one product header** (white card). The dark application header title shall not duplicate brand copy when redundant.

*Scope unchanged:* Branding remains; layer count reduced.

---

**Amendment 01-C — Queue Row Density Cap**  
Add to §6 Acceptance:

> In product-only mode, each queue list row shall display **at most two** metadata tags (urgency + optional due). Full tag sets remain accessible in case detail collapse.

*Scope unchanged:* All metadata still reachable; list scan simplified.

---

**Amendment 01-D — Success State Definition**  
Add to §4 Outputs:

> After triage, the **primary focal action** shall be 复制客户草稿 (or equivalent copy-out action). No other button shall use primary styling at the same viewport level.

*Scope unchanged:* Draft copy already required; visual hierarchy codified.

---

**Amendment 01-E — Paste Card When Case Open**  
Add to §6 Acceptance:

> When a case is open, the paste-new-message area shall **collapse** to a secondary link until the user explicitly starts a new intake.

*Scope unchanged:* New paste still available; de-emphasized during review.

---

## Capability 04 — Customer Intake Collection

### Existing UI-Related Clauses (summary)

| Section | Current requirement |
|---------|---------------------|
| §2 Primary User | Broker paste primary; customer portal secondary |
| §4 Outputs | Paste confirmation; workflow expectation "原样粘贴…" |
| §6 Acceptance | Broker paste; loading message; Add-Car not default trial path |
| §9 Improvements | Broker default, paste copy, loading, wayfinding |

### Proposed UI Simplicity Amendments

**Amendment 04-A — Customer Portal Not Trial Front Door**  
Add to §10 Must Not Build (UI presentation):

> Customer portal (客户报送) shall not appear as a **peer tab** on the broker trial URL. It may exist at a separate route for secondary Add-Car collection.

*Scope unchanged:* Customer intake capability remains; GTM presentation clarified.

---

**Amendment 04-B — Customer Empty State One CTA**  
Add to §4 Outputs (customer portal when shown):

> Customer empty state shall present **one recommended primary action** (办理加车报价). Secondary paths (联系人工, 其他事项, structured form) shall not use equal primary button styling simultaneously.

*Scope unchanged:* All intake paths remain; visual hierarchy fixed.

---

**Amendment 04-C — Loading as Trust**  
Strengthen §4 Outputs:

> First triage request shall show **persistent inline loading copy** (≥30s expectation) occupying the result area — not only a spinner.

*Scope unchanged:* Loading already implied; acceptance sharpened.

---

**Amendment 04-D — Post-Handoff Customer CTA**  
Add to §4 Outputs (customer portal):

> After formal handoff, the UI shall display **one explicit next-step sentence** for the customer (wait / append / new issue) — not rely on implicit read-only cards alone.

*Scope unchanged:* No new workflow; clarity requirement only.

---

**Amendment 04-E — Engineer Timing Copy**  
Add to §10 Must Not Build:

> Customer-facing result cards shall not show **UTC/timestamp implementation footnotes** in default view. Timing may appear in broker detail collapse only.

*Scope unchanged:* Timestamps remain in data; customer UI simplified.

---

## Cross-Capability UI Principle (recommended addendum)

**UI Simplicity Clause (P16-M):**

> For paid pilot and product-only surfaces, **visible control count** on the broker workbench empty state shall not exceed **10** distinct interactive elements above the fold at 1440×900. Case detail may expand on user action. Engineer, infra, and QA labels are forbidden in default view.

*Does not alter what the system does — only what the broker sees by default.*

---

## Amendment Impact Table

| Amendment | Cap | Risk | Constitution conflict? |
|-----------|-----|------|------------------------|
| 01-A Single primary | 01 | Low | No |
| 01-B Chrome merge | 01 | Low | No |
| 01-C Queue tag cap | 01 | Low | No |
| 01-D Copy draft hero | 01 | Low | No |
| 01-E Collapse paste | 01 | Low | No |
| 04-A Hide customer tab trial | 04 | Low | Aligns with §2 priority |
| 04-B Customer one CTA | 04 | Medium | No |
| 04-C Loading copy | 04 | Low | No |
| 04-D Post-handoff CTA | 04 | Low | No |
| 04-E No UTC footnote | 04 | Low | No |
| UI Simplicity Clause | Both | Low | Addendum only |

---

*End of P16-M Contract UI Amendments — proposals only; Constitution not modified in P16-M*
